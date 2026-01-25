"""Agno-powered helper functions for grounded chat and studio outputs."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat

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
