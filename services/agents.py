"""Agno-powered helper functions for grounded chat and studio outputs."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, Iterable, List
from uuid import uuid4

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.openai import OpenAITools

from services.settings import get_settings

_SETTINGS = get_settings()


def _build_agent(instructions: str | None = None) -> Agent | None:
    api_key = _SETTINGS.openai_api_key
    if not api_key:
        return None
    model = OpenAIChat(id="gpt-5.2", api_key=api_key)
    return Agent(
        name="NotebookLMClone",
        instructions=(
            instructions
            or "Du bist ein Assistent, der Fragen nur mit den bereitgestellten Quellen beantwortet. "
            "Zitiere Quellen inline im Format [Quelle]."
        ),
        model=model,
    )


_AGENT = _build_agent()


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


def _run_agent(payload: str, agent: Agent | None = None) -> str:
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


def generate_grounded_reply(
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
    payload = (
        f"Ausgewählte Quellen:\n{context}\n\nZusätzliche Notizen:\n{notes_text or '-'}"
        f"\n\nKontext (RAG):\n{context_chunks or '-'}\n\nFrage: {prompt}"
    )
    if _AGENT:
        try:
            result = _run_agent(payload)
            return result.strip()
        except Exception as exc:  # pragma: no cover - API errors
            return f"(Agno Fehler: {exc}). Antwort (Fallback): {prompt} -> {context}"
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
        agent_instructions = agent_config.get("instructions") or agent_config.get(
            "system_prompt"
        )
    agent = _build_agent(agent_instructions) if agent_instructions else _AGENT
    if agent:
        try:
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
        agent_instructions = agent_config.get("instructions") or agent_config.get(
            "system_prompt"
        )
    summary_agent = _build_agent(agent_instructions) if agent_instructions else _AGENT
    if not summary_agent:
        return {
            "content": "(Demo) Infografik benötigt einen OpenAI API Key.",
            "image_path": None,
        }
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

    api_key = _SETTINGS.openai_api_key
    if not api_key:
        return {
            "content": f"{summary}\n\n**Infografik-Prompt**\n{image_prompt}",
            "image_path": None,
        }
    image_agent = Agent(
        name="InfographicGenerator",
        model=OpenAIChat(id="gpt-5.2", api_key=api_key),
        tools=[OpenAITools(image_model=image_model)],
        markdown=True,
    )
    try:
        response = image_agent.run(image_prompt)
    except Exception as exc:  # pragma: no cover
        return {
            "content": f"{summary}\n\n**Infografik-Prompt**\n{image_prompt}\n\nFehler: {exc}",
            "image_path": None,
        }
    image_path = None
    images = getattr(response, "images", None) or []
    if images and getattr(images[0], "content", None):
        image_path = _save_image_payload(images[0].content)
    return {
        "content": f"{summary}\n\n**Infografik-Prompt**\n{image_prompt}",
        "image_path": image_path,
    }
