"""Agno-powered helper functions for grounded chat and studio outputs."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from agno.agent import Agent
from agno.team import Team
from agno.tools.openai import OpenAITools

from services.agents_config import build_agent_instructions
from services.agent_factory import build_model, build_tools, normalize_model_id
from services.halo_team import build_master_team_from_config
from services.settings import get_settings
from services.knowledge import get_agent_knowledge
from services.storage import get_agent_db

_SETTINGS = get_settings()
_LOGGER = logging.getLogger(__name__)
_LOG_AGENT_PAYLOAD = True
_LOG_AGENT_RESPONSE = True
_LOG_AGENT_ERRORS = True


def set_logging_preferences(
    *,
    log_payload: bool | None = None,
    log_response: bool | None = None,
    log_errors: bool | None = None,
) -> None:
    global _LOG_AGENT_PAYLOAD, _LOG_AGENT_RESPONSE, _LOG_AGENT_ERRORS
    if log_payload is not None:
        _LOG_AGENT_PAYLOAD = log_payload
    if log_response is not None:
        _LOG_AGENT_RESPONSE = log_response
    if log_errors is not None:
        _LOG_AGENT_ERRORS = log_errors


def _build_agent(
    instructions: str | None = None,
    name: str = "NotebookLMClone",
    model_id: object = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> Agent | None:
    normalized_model_id = normalize_model_id(model_id)
    model = build_model(
        normalized_model_id,
        openai_api_key=_SETTINGS.openai_api_key,
        logger=_LOGGER,
    )
    if model is None:
        return None
    db = get_agent_db()
    knowledge = get_agent_knowledge()
    return Agent(
        name=name,
        instructions=(
            instructions
            or "Du bist ein Assistent, der Fragen nur mit den bereitgestellten Quellen beantwortet. "
            "Zitiere Quellen inline im Format [Quelle]."
        ),
        model=model,
        markdown=True,
        debug_mode=True,
        session_id=session_id,
        user_id=user_id,
        db=db,
        add_history_to_context=db is not None,
        num_history_runs=3 if db is not None else None,
        enable_user_memories=db is not None,
        knowledge=knowledge,
        search_knowledge=knowledge is not None,
    )


def _build_agent_from_config(
    config: Dict[str, object],
    session_id: str | None = None,
    user_id: str | None = None,
) -> Agent | None:
    name = str(config.get("name") or config.get("id") or "Agent")
    instructions = build_agent_instructions(config)
    agent = _build_agent(
        instructions,
        name=name,
        model_id=config.get("model"),
        session_id=session_id,
        user_id=user_id,
    )
    if not agent:
        return None
    tools = build_tools(
        config.get("tools"),
        config.get("tool_settings"),
        logger=_LOGGER,
    )
    if tools:
        agent.tools = tools
    return agent


_AGENT = _build_agent()
_LAST_TRACE: Dict[str, object] | None = None


def get_last_trace() -> Dict[str, object] | None:
    return _LAST_TRACE


def _record_trace(
    *,
    payload: str,
    response: str | None,
    agent: Agent | Team | None,
    agent_config: Dict[str, object] | None,
    error: str | None = None,
) -> None:
    global _LAST_TRACE
    trace: Dict[str, object] = {
        "payload": payload,
        "response": response,
        "error": error,
    }
    if agent_config:
        _LOGGER.info(
            "Chat agent config name: %s",
            agent_config.get("name"),
        )
        trace["agent_id"] = agent_config.get("id")
        trace["agent_name"] = agent_config.get("name")
        trace["agent_role"] = agent_config.get("role")
        trace["agent_tools"] = agent_config.get("tools")
        trace["agent_members"] = agent_config.get("members")
    if agent is not None:
        trace["agent_type"] = "team" if isinstance(agent, Team) else "agent"
        tools = getattr(agent, "tools", None)
        if tools:
            trace["agent_tools_runtime"] = [type(tool).__name__ for tool in tools]
        if isinstance(agent, Team):
            trace["agent_members_runtime"] = [
                member.name for member in getattr(agent, "members", [])
            ]
            selected_member_ids = getattr(agent, "selected_member_ids", None)
            if selected_member_ids:
                trace["selected_member_ids"] = list(selected_member_ids)
    _LAST_TRACE = trace


def _invoke_agent(payload: str) -> Any:
    if not _AGENT:
        raise RuntimeError("Agent not configured")
    if hasattr(_AGENT, "run_sync"):
        return _AGENT.run_sync(payload)
    return _AGENT.run(payload)


def _normalize_agent_output(result: Any) -> str:
    if result is None:
        return ""
    for attr in ("content", "output_text", "text"):
        value = getattr(result, attr, None)
        if value:
            return value if isinstance(value, str) else str(value)
    if hasattr(result, "output"):
        output = getattr(result, "output")
        if isinstance(output, list):
            return "\n".join(str(item) for item in output if item)
        if output:
            return str(output)
    if hasattr(result, "messages"):
        messages = getattr(result, "messages") or []
        for message in reversed(messages):
            content = getattr(message, "content", None)
            if content:
                return content
    return str(result)


def _run_agent(payload: str, agent: Agent | Team | None = None) -> str:
    if agent is None:
        agent = _AGENT
    if not agent:
        raise RuntimeError("Agent not configured")
    raw = (
        _invoke_agent(payload)
        if agent is _AGENT
        else _normalize_agent_output(
            agent.run_sync(payload)
            if hasattr(agent, "run_sync")
            else agent.run(payload)
        )
    )
    return _normalize_agent_output(raw)


def _format_sources(sources: Iterable[str]) -> str:
    if not sources:
        return "- (keine ausgewählten Quellen)"
    return "\n".join(f"- {name}" for name in sources)


def build_chat_payload(
    prompt: str,
    sources: List[str],
    notes: List[dict],
    contexts: List[dict],
) -> str:
    context = _format_sources(sources)
    notes_text = "\n".join(f"Note: {note.get('content')}" for note in notes[-5:])
    context_chunks = "\n\n".join(
        f"Snippet: {ctx.get('text')}\nMeta: {ctx.get('meta')}" for ctx in contexts
    )
    return (
        f"Ausgewählte Quellen:\n{context}\n\nZusätzliche Notizen:\n{notes_text or '-'}"
        f"\n\nKontext (RAG):\n{context_chunks or '-'}\n\nFrage: {prompt}"
    )


def build_chat_agent(
    agent_config: Dict[str, object] | None = None,
    prompt: str | None = None,
    session_id: str | None = None,
    user_id: str | None = None,
) -> Agent | Team | None:
    team_agent: Team | None = None
    if agent_config:
        if agent_config.get("members") or agent_config.get("id") == "chat":
            team_agent = build_master_team_from_config(
                agent_config,
                prompt=prompt,
                session_id=session_id,
                user_id=user_id,
            )
            if team_agent is None:
                _LOGGER.warning("Falling back to single agent for chat")
    if team_agent is not None:
        return team_agent
    if agent_config:
        return _build_agent_from_config(
            agent_config, session_id=session_id, user_id=user_id
        )
    return _AGENT


def generate_grounded_reply(
    prompt: str,
    sources: List[str],
    notes: List[dict],
    contexts: List[dict],
    agent_config: Dict[str, object] | None = None,
) -> str:
    _LOGGER.info("agents.py path: %s", __file__)
    payload = build_chat_payload(prompt, sources, notes, contexts)
    if agent_config:
        _LOGGER.info(
            "Chat agent config: id=%s members=%s tools=%s",
            agent_config.get("id"),
            agent_config.get("members"),
            agent_config.get("tools"),
        )
    agent = build_chat_agent(agent_config, prompt=prompt)
    if agent is not None:
        _LOGGER.info(
            "Chat agent class: %s",
            type(agent).__name__,
        )
    if agent:
        try:
            agent_name = getattr(agent, "name", "Agent")
            _LOGGER.info(
                "Chat using %s (%s)",
                agent_name,
                "team" if isinstance(agent, Team) else "agent",
            )
            _LOGGER.info("Chat agent class: %s", type(agent).__name__)
            tools = getattr(agent, "tools", None) or []
            if tools:
                _LOGGER.info(
                    "Chat agent tools: %s",
                    ", ".join(type(tool).__name__ for tool in tools),
                )
            if isinstance(agent, Team):
                member_names = [member.name for member in getattr(agent, "members", [])]
                _LOGGER.info("Chat team members: %s", member_names)
                for member in getattr(agent, "members", []):
                    member_tools = getattr(member, "tools", None) or []
                    if member_tools:
                        _LOGGER.info(
                            "Chat team member %s tools: %s",
                            member.name,
                            ", ".join(type(tool).__name__ for tool in member_tools),
                        )
            if _LOG_AGENT_PAYLOAD:
                _LOGGER.info("Agent payload: %s", payload)
            result = _run_agent(payload, agent)
            response = result.strip()
            if _LOG_AGENT_RESPONSE:
                _LOGGER.info("Agent response: %s", response)
            _record_trace(
                payload=payload,
                response=response,
                agent=agent,
                agent_config=agent_config,
            )
            return response
        except Exception as exc:  # pragma: no cover - API errors
            error = f"(Agno Fehler: {exc}). Antwort (Fallback): {prompt} -> {payload}"
            if _LOG_AGENT_ERRORS:
                _LOGGER.exception("Agent error")
            _record_trace(
                payload=payload,
                response=None,
                agent=agent,
                agent_config=agent_config,
                error=error,
            )
            return error
    return (
        f"(Demo) Antwort basierend auf {', '.join(sources) or 'keinen Quellen'}: "
        f"{prompt} – bitte API Key setzen, um echte Antworten zu erhalten."
    )


def render_studio_output(
    template_name: str,
    instructions: str,
    sources: List[str],
    agent_config: Dict[str, str] | None = None,
) -> str:
    prompt = (
        f"Template: {template_name}\nAnweisungen: {instructions}\n"
        f"Quellen: {', '.join(sources) or 'keine'}\n"
        "Erzeuge eine prägnante Ausgabe."
    )
    agent_instructions = None
    if agent_config:
        agent_instructions = build_agent_instructions(agent_config)
    agent = _build_agent(agent_instructions) if agent_instructions else _AGENT
    if agent:
        try:
            agent_name = getattr(agent, "name", "Agent")
            _LOGGER.info("Studio using %s", agent_name)
            result = _run_agent(prompt, agent)
            return result
        except Exception as exc:  # pragma: no cover
            return f"Fehler bei der Generierung: {exc}"
    return f"(Demo Output) {template_name}: {instructions[:120]}..."


def _save_image_payload(data: object, suffix: str = ".png") -> str | None:
    if data is None:
        return None
    if isinstance(data, (bytes, bytearray)):
        image_bytes = bytes(data)
    elif isinstance(data, str):
        try:
            image_bytes = base64.b64decode(data)
        except (ValueError, TypeError):
            return None
    else:
        return None
    output_dir = Path(_SETTINGS.data_dir) / "studio_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"infographic_{uuid4().hex}{suffix}"
    filename.write_bytes(image_bytes)
    return str(filename)


def render_infographic_output(
    template_name: str,
    instructions: str,
    sources: List[str],
    context_text: str,
    agent_config: Dict[str, str] | None = None,
    image_model: str = "gpt-image-1",
) -> Dict[str, object]:
    agent_instructions = None
    if agent_config:
        agent_instructions = build_agent_instructions(agent_config)
    summary_agent = _build_agent(agent_instructions) if agent_instructions else _AGENT
    if not summary_agent:
        return {
            "content": "(Demo) Infografik benötigt einen OpenAI API Key.",
            "image_path": None,
        }
    summary_agent_name = getattr(summary_agent, "name", "Agent")
    _LOGGER.info("Studio (infographic) using %s", summary_agent_name)
    summary_prompt = (
        f"Template: {template_name}\nAnweisungen: {instructions}\n"
        f"Quellen: {', '.join(sources) or 'keine'}\n\n"
        "Erstelle eine prägnante Zusammenfassung der ausgewählten Quellen in 5-7 Stichpunkten. "
        "Nutze nur die bereitgestellten Inhalte.\n\n"
        f"Kontext (RAG):\n{context_text or '-'}"
    )
    try:
        summary = _run_agent(summary_prompt, summary_agent).strip()
    except Exception as exc:  # pragma: no cover
        return {"content": f"Fehler bei der Zusammenfassung: {exc}", "image_path": None}

    prompt_builder = _build_agent(agent_instructions) if agent_instructions else _AGENT
    prompt_prompt = (
        "Erstelle einen klaren, detailreichen Prompt zur Generierung einer Infografik. "
        "Die Infografik soll die folgenden Stichpunkte visualisieren. "
        "Gib nur den Prompt aus, ohne zusätzliche Erklärungen.\n\n"
        f"Stichpunkte:\n{summary}"
    )
    try:
        image_prompt = _run_agent(prompt_prompt, prompt_builder).strip()
    except Exception as exc:  # pragma: no cover
        return {"content": f"Fehler beim Infografik-Prompt: {exc}", "image_path": None}

    prompt_block = f"```md\n{image_prompt}\n```"

    api_key = _SETTINGS.openai_api_key
    if not api_key:
        return {
            "content": f"{summary}\n\n**Infografik-Prompt (Markdown)**\n{prompt_block}",
            "image_path": None,
        }
    image_agent = Agent(
        name="InfographicGenerator",
        model=build_model(
            "openai:gpt-5.2",
            openai_api_key=api_key,
            logger=_LOGGER,
        ),
        tools=[OpenAITools(image_model=image_model)],
        markdown=True,
    )
    try:
        response = image_agent.run(image_prompt)
    except Exception as exc:  # pragma: no cover
        return {
            "content": (
                f"{summary}\n\n**Infografik-Prompt (Markdown)**\n"
                f"{prompt_block}\n\nFehler: {exc}"
            ),
            "image_path": None,
        }
    image_path = None
    images = getattr(response, "images", None) or []
    if images and getattr(images[0], "content", None):
        image_path = _save_image_payload(images[0].content)
    content = f"{summary}\n\n**Infografik-Prompt (Markdown)**\n{prompt_block}"
    if image_path is None:
        content = f"{content}\n\nHinweis: Kein Bild generiert."
    return {"content": content, "image_path": image_path}
