"""Chat turn orchestration extracted from app/main.py.

Encapsulates: payload build → agent creation → streaming → fallback → result.
Keeps Streamlit rendering concerns out of the business logic.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from time import perf_counter
from typing import Callable, Dict, List

from services import agents, pipelines, retrieval
from services.streaming_adapter import stream_agent_response

try:
    from agno.agent import RunEvent
except ImportError:  # pragma: no cover
    RunEvent = None

_LOGGER = logging.getLogger(__name__)
_CITATION_PATTERN = re.compile(r"\[(?:quelle|source)[^\]]*\]", re.IGNORECASE)


def _parse_page_number(meta: object) -> str | None:
    if not isinstance(meta, dict):
        return None

    direct_keys = ("page", "page_number", "page_no", "seitenzahl")
    for key in direct_keys:
        value = meta.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text

    index_keys = ("page_index", "chunk_index")
    for key in index_keys:
        value = meta.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        try:
            return str(int(text) + 1)
        except ValueError:
            continue
    return None


def _extract_context_references(contexts: List[dict]) -> List[tuple[str, str | None]]:
    references: List[tuple[str, str | None]] = []
    seen: set[tuple[str, str | None]] = set()

    for ctx in contexts:
        if not isinstance(ctx, dict):
            continue
        meta = ctx.get("meta")
        if not isinstance(meta, dict):
            continue
        source = str(meta.get("title") or meta.get("source_title") or "").strip()
        if not source:
            continue
        page = _parse_page_number(meta)
        key = (source.lower(), page)
        if key in seen:
            continue
        seen.add(key)
        references.append((source, page))
    return references


def _citation_for_source(
    source: str, references: List[tuple[str, str | None]]
) -> str | None:
    source_norm = source.strip().lower()
    for ref_source, page in references:
        if ref_source.strip().lower() == source_norm:
            return page
    return None


def _format_citation(source: str, page: str | None) -> str:
    if page:
        return f"[Quelle: {source}, Seite {page}]"
    return f"[Quelle: {source}]"


def _strip_citation_tags(text: str) -> str:
    without_tags = _CITATION_PATTERN.sub("", text)
    without_tags = re.sub(r"[ \t]+\n", "\n", without_tags)
    without_tags = re.sub(r"\n{3,}", "\n\n", without_tags)
    return without_tags.strip()


def _apply_citation_policy(
    response: str,
    sources: List[str],
    contexts: List[dict],
) -> str:
    cleaned = response.strip()
    if not cleaned:
        return cleaned

    selected_sources = [
        str(source).strip() for source in sources if str(source).strip()
    ]
    references = _extract_context_references(contexts)

    if len(selected_sources) <= 1:
        source_name = selected_sources[0] if selected_sources else None
        if not source_name and references:
            source_name = references[0][0]
        if not source_name:
            return cleaned

        page = _citation_for_source(source_name, references)
        body = _strip_citation_tags(cleaned)
        return f"{body}\n\n{_format_citation(source_name, page)}"

    source_lines: List[str] = []
    seen_sources: set[str] = set()
    for source_name in selected_sources:
        key = source_name.lower()
        if key in seen_sources:
            continue
        seen_sources.add(key)
        page = _citation_for_source(source_name, references)
        source_lines.append(f"- {_format_citation(source_name, page)}")

    if not source_lines:
        for source_name, page in references:
            source_lines.append(f"- {_format_citation(source_name, page)}")

    if not source_lines:
        return cleaned

    if re.search(r"(?im)^#{1,6}\s+quellen", cleaned):
        return cleaned

    return f"{cleaned}\n\n### Quellen\n" + "\n".join(source_lines)


def _extract_knowledge_sources(contexts: List[dict]) -> List[str]:
    source_names: List[str] = []
    seen: set[str] = set()
    for ctx in contexts:
        if not isinstance(ctx, dict):
            continue
        meta = ctx.get("meta")
        if not isinstance(meta, dict):
            continue
        source = str(meta.get("title") or meta.get("source_title") or "").strip()
        if not source:
            continue
        key = source.lower()
        if key in seen:
            continue
        seen.add(key)
        source_names.append(source)
    return source_names


def _extract_runtime_tools(agent: object) -> List[str]:
    tools = getattr(agent, "tools", None) or []
    names: List[str] = []
    for tool in tools:
        label = getattr(tool, "name", None)
        names.append(str(label) if label else type(tool).__name__)
    return names


def _resolve_model_label(
    agent: object | None,
    agent_config: Dict[str, object] | None,
) -> str | None:
    if isinstance(agent_config, dict):
        for key in ("model", "model_id"):
            configured = agent_config.get(key)
            if configured:
                return str(configured)

    model = getattr(agent, "model", None)
    if model is None:
        return None
    for attr in ("id", "model", "model_id", "name"):
        value = getattr(model, attr, None)
        if value:
            return str(value)
    return type(model).__name__


def _compose_run_trace(
    *,
    base_trace: Dict[str, object] | None,
    turn: "ChatTurnInput",
    agent: object,
    payload: str,
    response: str,
    contexts: List[dict],
    streamed: Dict[str, object] | None,
    used_fallback: bool,
    latency_seconds: float,
) -> Dict[str, object]:
    trace: Dict[str, object] = {}
    if isinstance(base_trace, dict):
        trace.update(base_trace)

    if payload and "payload" not in trace:
        trace["payload"] = payload
    if response:
        trace["response"] = response

    if agent is not None:
        trace.setdefault("agent_name", str(getattr(agent, "name", "Agent")))
        members = getattr(agent, "members", None)
        is_team = bool(members)
        trace.setdefault("agent_type", "team" if is_team else "agent")
        runtime_tools = _extract_runtime_tools(agent)
        if runtime_tools:
            trace["agent_tools_runtime"] = runtime_tools
        if is_team:
            member_names = [
                str(getattr(member, "name", "")).strip()
                for member in (members or [])
                if str(getattr(member, "name", "")).strip()
            ]
            if member_names:
                trace["agent_members_runtime"] = member_names
        selected_members = getattr(agent, "selected_member_ids", None)
        if selected_members:
            trace["selected_member_ids"] = [
                str(member_id) for member_id in selected_members
            ]

    stream_result = "none"
    if streamed is not None:
        stream_result = "ok" if str(streamed.get("response") or "").strip() else "empty"

    telemetry = {
        "model": _resolve_model_label(agent, turn.agent_config),
        "selected_members": trace.get("selected_member_ids") or [],
        "tools": trace.get("agent_tools_runtime") or [],
        "stream_mode": "stream",
        "stream_events": bool(turn.stream_events),
        "stream_result": stream_result,
        "latency_ms": round(max(latency_seconds, 0.0) * 1000, 2),
        "knowledge_hits": len(contexts),
        "knowledge_sources": _extract_knowledge_sources(contexts),
        "used_fallback": used_fallback,
    }
    trace["telemetry"] = telemetry

    _LOGGER.info("Chat run telemetry: %s", telemetry)
    return trace


@dataclass
class ChatTurnResult:
    """Outcome of a single chat turn."""

    response: str = ""
    tool_calls: object = None
    trace: Dict[str, object] | None = None
    used_fallback: bool = False


@dataclass
class ChatTurnInput:
    """All inputs needed for a chat turn (no Streamlit dependency)."""

    prompt: str
    sources: List[str] = field(default_factory=list)
    notes: List[dict] = field(default_factory=list)
    session_id: str | None = None
    user_id: str | None = None
    agent_config: Dict[str, object] | None = None
    images: list | None = None
    stream_events: bool = True
    log_stream_events: bool = False
    on_response: Callable[[str], None] | None = None
    on_tools: Callable[[List[object]], None] | None = None


def build_chat_payload(turn: ChatTurnInput) -> tuple[str, List[dict]]:
    """Build the agent payload and retrieve RAG contexts.

    Returns (payload_text, contexts).
    """
    contexts = retrieval.query_similar(turn.prompt)
    payload = agents.build_chat_payload(
        turn.prompt,
        turn.sources,
        turn.notes,
        contexts,
    )
    return payload, contexts


def create_chat_agent(turn: ChatTurnInput):
    """Create the chat agent/team, with fallback on TypeError."""
    try:
        return agents.build_chat_agent(
            turn.agent_config,
            prompt=turn.prompt,
            session_id=turn.session_id,
            user_id=turn.user_id,
        )
    except TypeError:
        _LOGGER.warning(
            "Prompt-aware routing unavailable; using default team selection."
        )
        return agents.build_chat_agent(turn.agent_config)


def stream_chat_response(
    agent,
    payload: str,
    turn: ChatTurnInput,
) -> Dict[str, object] | None:
    """Run the streaming adapter and return the raw result dict."""
    return stream_agent_response(
        agent,
        payload,
        images=turn.images,
        stream_events=turn.stream_events,
        run_event=RunEvent,
        logger=_LOGGER,
        log_stream_events=turn.log_stream_events,
        on_response=turn.on_response,
        on_tools=turn.on_tools,
    )


def _fallback_reply(turn: ChatTurnInput, contexts: List[dict]) -> str:
    """Generate a non-streaming reply via the pipeline fallback."""
    try:
        return pipelines.generate_chat_reply(
            turn.prompt,
            turn.sources,
            turn.notes,
            contexts,
            turn.agent_config,
        )
    except TypeError:
        return pipelines.generate_chat_reply(
            turn.prompt,
            turn.sources,
            turn.notes,
            contexts,
        )


def run_chat_turn(turn: ChatTurnInput) -> ChatTurnResult:
    """Execute a full chat turn: payload → agent → stream → fallback → result.

    This is the main entry point for chat orchestration.  It is free of
    Streamlit imports so it can be unit-tested independently.
    """
    started_at = perf_counter()
    payload, contexts = build_chat_payload(turn)
    agent = create_chat_agent(turn)

    streamed = stream_chat_response(agent, payload, turn)

    if streamed is None:
        response = _fallback_reply(turn, contexts)
        response = _apply_citation_policy(response, turn.sources, contexts)
        trace = _compose_run_trace(
            base_trace=agents.get_last_trace(),
            turn=turn,
            agent=agent,
            payload=payload,
            response=response,
            contexts=contexts,
            streamed=streamed,
            used_fallback=True,
            latency_seconds=perf_counter() - started_at,
        )
        return ChatTurnResult(
            response=response,
            trace=trace,
            used_fallback=True,
        )

    response = (streamed.get("response") or "").strip()
    response = _apply_citation_policy(response, turn.sources, contexts)
    tool_calls = streamed.get("tools")
    trace = _compose_run_trace(
        base_trace=agents.get_last_trace(),
        turn=turn,
        agent=agent,
        payload=payload,
        response=response,
        contexts=contexts,
        streamed=streamed,
        used_fallback=False,
        latency_seconds=perf_counter() - started_at,
    )

    if not response:
        response = _fallback_reply(turn, contexts)
        response = _apply_citation_policy(response, turn.sources, contexts)
        trace = _compose_run_trace(
            base_trace=trace,
            turn=turn,
            agent=agent,
            payload=payload,
            response=response,
            contexts=contexts,
            streamed=streamed,
            used_fallback=True,
            latency_seconds=perf_counter() - started_at,
        )
        return ChatTurnResult(
            response=response,
            tool_calls=tool_calls,
            trace=trace,
            used_fallback=True,
        )

    return ChatTurnResult(
        response=response,
        tool_calls=tool_calls,
        trace=trace,
    )
