"""Chat turn orchestration extracted from app/main.py.

Encapsulates: payload build → agent creation → streaming → fallback → result.
Keeps Streamlit rendering concerns out of the business logic.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import re
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable, Dict, List, MutableMapping
from uuid import uuid4

try:
    # nest_asyncio.apply() is intentional: Streamlit runs its own asyncio event loop,
    # and asyncio.run() (used by streaming_adapter.py) raises RuntimeError if called
    # inside a running loop without this patch.  The alternative would be migrating all
    # async callers to a dedicated thread pool — that is deferred to a future refactor.
    import nest_asyncio as _nest_asyncio

    _nest_asyncio.apply()
except ImportError:  # pragma: no cover
    _nest_asyncio = None

from services import agents, pipelines, retrieval
from services.settings import get_settings

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
    mcp_events = []
    if streamed is not None:
        stream_result = "ok" if str(streamed.get("response") or "").strip() else "empty"
        mcp_events = streamed.get("mcp_events", [])

    telemetry = {
        "model": _resolve_model_label(agent, turn.agent_config),
        "selected_members": trace.get("selected_member_ids") or [],
        "tools": trace.get("agent_tools_runtime") or [],
        "mcp_events": mcp_events,
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
    generated_images: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ChatTurnInput:
    """All inputs needed for a chat turn (no Streamlit dependency)."""

    prompt: str
    sources: List[str] = field(default_factory=list)
    source_ids: List[str] = field(default_factory=list)
    notes: List[dict] = field(default_factory=list)
    session_id: str | None = None
    user_id: str | None = None
    agent_config: Dict[str, object] | None = None
    images: list | None = None
    stream_events: bool = True
    log_stream_events: bool = False
    on_response: Callable[[str], None] | None = None
    on_tools: Callable[[List[object]], None] | None = None
    agent_cache: MutableMapping[str, object] | None = None


def build_chat_payload(turn: ChatTurnInput) -> tuple[str, List[dict]]:
    """Build the agent payload and retrieve RAG contexts.

    Returns (payload_text, contexts).

    The manual vector search is kept to produce citation metadata (page/source
    references appended after the response). The matching chunks are NOT
    re-injected into the prompt because the Agent/Team already carries a native
    Agno ``knowledge=`` store that performs the same search internally —
    injecting them twice would double token usage with no quality gain.
    """
    source_ids = turn.source_ids if turn.source_ids else None
    contexts = retrieval.query_similar(turn.prompt, source_ids=source_ids)
    # Pass empty contexts so agents.build_chat_payload only includes
    # selected-source names and notes, not raw snippet text.
    payload = agents.build_chat_payload(
        turn.prompt,
        turn.sources,
        turn.notes,
        [],
    )
    return payload, contexts


_MCP_CIRCUIT_BREAKER_FAILURES = {}
_MCP_CIRCUIT_BREAKER_TIMEOUT_SECONDS = 300


def _get_mcp_identifier(mcp_tool: object) -> str:
    name = getattr(mcp_tool, "name", "")
    url = getattr(mcp_tool, "url", "")
    command = getattr(mcp_tool, "command", "")
    return f"{name}|{url}|{command}"


async def _manage_mcp_lifecycle(
    agent: object, session_id: str | None = None
) -> AsyncExitStack:
    """Open connections for all MCP tools attached to the agent or team members.

    The circuit-breaker state is keyed by ``(session_id, server_identifier)``
    so failures for one session do not affect other concurrent users.
    """
    stack = AsyncExitStack()
    tools_to_open = []

    # Collect tools from master agent
    if hasattr(agent, "tools"):
        tools_to_open.extend(getattr(agent, "tools") or [])

    # Collect tools from team members if applicable
    if hasattr(agent, "members"):
        for member in getattr(agent, "members") or []:
            if hasattr(member, "tools"):
                tools_to_open.extend(getattr(member, "tools") or [])

    # Filter for MCPTools only
    mcp_tools = []
    for t in tools_to_open:
        if type(t).__name__ == "MCPTools":
            mcp_tools.append(t)

    for mcp_tool in mcp_tools:
        if hasattr(mcp_tool, "__aenter__"):
            identifier = _get_mcp_identifier(mcp_tool)
            scoped_key = f"{session_id or '_global'}|{identifier}"
            now = time.time()

            # Check circuit breaker (scoped per session)
            breaker_state = _MCP_CIRCUIT_BREAKER_FAILURES.get(scoped_key)
            if breaker_state:
                failures, last_failure_time = breaker_state
                if failures >= 3:
                    if now - last_failure_time < _MCP_CIRCUIT_BREAKER_TIMEOUT_SECONDS:
                        _LOGGER.warning(
                            "MCP circuit breaker open for '%s' due to %d recent failures. Skipping connection.",
                            getattr(mcp_tool, "name", "mcp"),
                            failures,
                        )
                        continue
                    else:
                        # Reset breaker after timeout
                        _LOGGER.info(
                            "MCP circuit breaker timeout expired for '%s'. Retrying connection.",
                            getattr(mcp_tool, "name", "mcp"),
                        )
                        _MCP_CIRCUIT_BREAKER_FAILURES.pop(scoped_key, None)

            try:
                # Basic retry logic for transient connection drops
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        await stack.enter_async_context(mcp_tool)
                        break
                    except asyncio.CancelledError as exc:
                        _LOGGER.warning(
                            "MCP lifecycle initialization cancelled for '%s': %s",
                            getattr(mcp_tool, "name", "mcp"),
                            exc,
                        )
                        raise
                    except Exception as e:
                        if attempt < max_retries - 1:
                            _LOGGER.warning(
                                "Transient failure connecting to MCP '%s': %s. Retrying...",
                                getattr(mcp_tool, "name", "mcp"),
                                e,
                            )
                            await asyncio.sleep(1)
                        else:
                            raise e

                _LOGGER.info(
                    "MCP lifecycle opened for %s", getattr(mcp_tool, "name", "mcp")
                )

                # Reset breaker on success
                if scoped_key in _MCP_CIRCUIT_BREAKER_FAILURES:
                    _MCP_CIRCUIT_BREAKER_FAILURES.pop(scoped_key, None)

            except asyncio.CancelledError:
                _LOGGER.warning(
                    "Skipping MCP lifecycle for %s due to cancellation",
                    getattr(mcp_tool, "name", "mcp"),
                )
                failures, _ = _MCP_CIRCUIT_BREAKER_FAILURES.get(scoped_key, (0, 0))
                _MCP_CIRCUIT_BREAKER_FAILURES[scoped_key] = (failures + 1, now)
                continue
            except Exception:
                _LOGGER.exception(
                    "Failed to open MCP lifecycle for %s",
                    getattr(mcp_tool, "name", "mcp"),
                )
                # Record failure
                failures, _ = _MCP_CIRCUIT_BREAKER_FAILURES.get(scoped_key, (0, 0))
                _MCP_CIRCUIT_BREAKER_FAILURES[scoped_key] = (failures + 1, now)

    return stack


def _compute_agent_cache_key(
    session_id: str | None,
    agent_config: Dict[str, object] | None,
) -> str:
    """Return a stable cache key for a (session, config) pair."""
    config_blob = (
        json.dumps(agent_config, sort_keys=True, default=str) if agent_config else ""
    )
    config_hash = hashlib.sha256(config_blob.encode()).hexdigest()[:16]
    return f"_halo_agent_cache_{session_id or 'anon'}_{config_hash}"


def create_chat_agent(
    turn: ChatTurnInput,
    agent_cache: MutableMapping[str, object] | None = None,
):
    """Create (or return cached) chat agent/team.

    If *agent_cache* is provided (e.g. ``st.session_state``), the built
    agent is stored under a key derived from session_id + config hash and
    reused on subsequent turns with the same configuration.
    """
    cache_key = _compute_agent_cache_key(turn.session_id, turn.agent_config)
    if agent_cache is not None and cache_key in agent_cache:
        _LOGGER.debug("Returning cached agent for key %s", cache_key)
        return agent_cache[cache_key]

    try:
        agent = agents.build_chat_agent(
            turn.agent_config,
            prompt=turn.prompt,
            session_id=turn.session_id,
            user_id=turn.user_id,
        )
    except TypeError:
        _LOGGER.warning(
            "Prompt-aware routing unavailable; using default team selection."
        )
        agent = agents.build_chat_agent(turn.agent_config)

    if agent_cache is not None and agent is not None:
        agent_cache[cache_key] = agent
        _LOGGER.debug("Cached agent under key %s", cache_key)
    return agent


async def stream_chat_response(
    agent: object, payload: str, turn: ChatTurnInput
) -> Dict[str, object] | None:
    """Stream response from the agent and return the stream outcome.

    Returns the RunCompleted/TeamRunCompleted event payload carrying the final
    response, or None on fallback/error.
    """
    stack = await _manage_mcp_lifecycle(agent, session_id=turn.session_id)
    try:
        async with stack:
            try:
                from services.streaming_adapter import stream_agent_response_async
            except ImportError:
                _LOGGER.warning("agno streaming adapter not found; falling back")
                return None
            try:
                from agno.agent.events import RunEvent
            except ImportError:
                _LOGGER.warning(
                    "agno.agent.events.RunEvent not found; continuing with generic event parsing"
                )
                RunEvent = None

            if hasattr(agent, "run_sync"):
                _LOGGER.warning("Agent %s is async; falling back", agent)
                return None

            return await stream_agent_response_async(
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
    except asyncio.CancelledError as exc:
        _LOGGER.warning("MCP streaming cancelled; falling back: %s", exc)
        return None


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


def _save_generated_image(
    image_data: object, suffix: str = ".png"
) -> Dict[str, str] | None:
    """Save generated image from tool result and return dict with filepath and name."""
    if image_data is None:
        return None
    if isinstance(image_data, (bytes, bytearray)):
        image_bytes = bytes(image_data)
    elif isinstance(image_data, str):
        try:
            image_bytes = base64.b64decode(image_data)
        except (ValueError, TypeError):
            return None
    else:
        return None

    settings = get_settings()
    output_dir = Path(settings.data_dir) / "chat_images"
    output_dir.mkdir(parents=True, exist_ok=True)
    image_id = uuid4().hex[:8]
    filename = output_dir / f"generated_{image_id}{suffix}"
    filename.write_bytes(image_bytes)
    return {"filepath": str(filename), "name": f"Generated Image {image_id}"}


def _extract_generated_images(tool_calls: object) -> List[Dict[str, str]]:
    """Extract generated images from tool call results or Image objects."""
    images: List[Dict[str, str]] = []

    if tool_calls is None:
        _LOGGER.debug("tool_calls is None, no images to extract")
        return images

    tool_list = []
    if isinstance(tool_calls, list):
        tool_list = tool_calls
    elif hasattr(tool_calls, "__iter__"):
        try:
            tool_list = list(tool_calls)
        except (TypeError, ValueError):
            _LOGGER.debug("tool_calls could not be converted to list")
            return images

    _LOGGER.debug("Extracting images from %d tool calls", len(tool_list))

    for tool_call in tool_list:
        if tool_call is None:
            continue

        # Handle Agno Image objects directly (from response.images)
        # Image objects have: id, url, content (base64), original_prompt
        if hasattr(tool_call, "content") and hasattr(tool_call, "id"):
            _LOGGER.debug(
                "Found Agno Image object with id=%s", getattr(tool_call, "id", None)
            )
            image_content = getattr(tool_call, "content", None)
            image_url = getattr(tool_call, "url", None)

            if image_content:
                # Base64 content
                saved = _save_generated_image(image_content)
                if saved:
                    images.append(saved)
                    continue
            if image_url:
                # URL - save metadata for display
                images.append(
                    {
                        "url": image_url,
                        "name": f"Generated Image {getattr(tool_call, 'id', 'unknown')}",
                    }
                )
                continue

        tool_name = None
        tool_content = None

        if hasattr(tool_call, "get"):
            tool_name = tool_call.get("tool_name") or tool_call.get("name")
            tool_content = tool_call.get("content")
        else:
            tool_name = getattr(tool_call, "tool_name", None) or getattr(
                tool_call, "name", None
            )
            tool_content = getattr(tool_call, "content", None)

        _LOGGER.debug(
            "Tool call: name=%s, content_type=%s",
            tool_name,
            type(tool_content).__name__ if tool_content else "None",
        )

        if tool_name and "image" in tool_name.lower():
            _LOGGER.debug(
                "Tool '%s' matches image criteria, extracting content", tool_name
            )
            if tool_content:
                if isinstance(tool_content, list):
                    for item in tool_content:
                        if isinstance(item, dict):
                            image_data = (
                                item.get("image")
                                or item.get("b64_json")
                                or item.get("base64")
                            )
                            if image_data:
                                _LOGGER.info("Found base64 image data in list item")
                                saved = _save_generated_image(image_data)
                                if saved:
                                    images.append(saved)
                elif isinstance(tool_content, dict):
                    image_data = (
                        tool_content.get("image")
                        or tool_content.get("b64_json")
                        or tool_content.get("base64")
                    )
                    if image_data:
                        _LOGGER.info("Found base64 image data in dict")
                        saved = _save_generated_image(image_data)
                        if saved:
                            images.append(saved)
                elif isinstance(tool_content, str):
                    try:
                        data = base64.b64decode(tool_content)
                        _LOGGER.debug("Found base64 string content")
                        saved = _save_generated_image(data)
                        if saved:
                            images.append(saved)
                    except (ValueError, TypeError):
                        pass

        if not images:
            _LOGGER.debug(
                "No images extracted from tool '%s', checking all attributes for base64",
                tool_name,
            )
            if hasattr(tool_call, "__dict__"):
                for attr_name, attr_val in vars(tool_call).items():
                    if attr_val and isinstance(attr_val, str) and len(attr_val) > 100:
                        try:
                            base64.b64decode(attr_val)
                            _LOGGER.debug("Found base64 in attribute '%s'", attr_name)
                            saved = _save_generated_image(attr_val)
                            if saved:
                                images.append(saved)
                                break
                        except (ValueError, TypeError):
                            pass

    _LOGGER.debug("Total images extracted: %d", len(images))
    return images


def run_chat_turn(turn: ChatTurnInput) -> ChatTurnResult:
    """Execute a full chat turn: payload → agent → stream → fallback → result.

    This is the main entry point for chat orchestration.  It is free of
    Streamlit imports so it can be unit-tested independently.
    """

    started_at = perf_counter()
    payload, contexts = build_chat_payload(turn)
    agent = create_chat_agent(turn, agent_cache=turn.agent_cache)

    try:
        streamed = asyncio.run(stream_chat_response(agent, payload, turn))
    except asyncio.CancelledError as exc:
        _LOGGER.warning("Chat stream cancelled; using fallback reply: %s", exc)
        streamed = None
    except Exception:
        _LOGGER.exception("Error during chat stream execution")
        streamed = None

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
    streamed_images = streamed.get("images", [])
    _LOGGER.info(
        "Streamed result: response_len=%d, tools=%s, images=%d",
        len(response),
        [
            getattr(t, "name", None) or t.get("name") if hasattr(t, "get") else None
            for t in (tool_calls or [])
        ],
        len(streamed_images),
    )
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

    generated_images = _extract_generated_images(tool_calls)
    # Only use streamed images if available (avoids duplicates from response object)
    # Streaming chunks capture images earlier, response.images is often the same
    if streamed_images:
        # Prefer streamed images as they come first and avoid duplicates
        generated_images = streamed_images
    # Only fall back to tool_calls extraction if no streamed images

    # Convert Agno Image objects to JSON-serializable dicts and deduplicate
    serializable_images = []
    seen_urls = set()
    seen_paths = set()

    for img in generated_images:
        img_dict = None

        if isinstance(img, dict):
            img_dict = img
        elif hasattr(img, "__dict__"):
            # Agno Image object - convert to dict
            img_dict = {}
            if hasattr(img, "url") and img.url:
                img_dict["url"] = img.url
            if hasattr(img, "content") and img.content:
                # Base64 content - save to file
                saved = _save_generated_image(img.content)
                if saved:
                    img_dict["filepath"] = saved.get("filepath")
                    img_dict["name"] = saved.get("name", "Generated Image")
            if hasattr(img, "id") and img.id:
                img_dict["name"] = f"Generated Image {img.id}"
        elif hasattr(img, "url") or hasattr(img, "filepath"):
            # Already a dict-like object
            img_dict = {
                "url": getattr(img, "url", None),
                "filepath": getattr(img, "filepath", None),
                "name": getattr(img, "name", "Generated Image"),
            }

        # Deduplicate by URL or filepath
        if img_dict:
            url = img_dict.get("url")
            filepath = img_dict.get("filepath")
            if url and url not in seen_urls:
                seen_urls.add(url)
                serializable_images.append(img_dict)
            elif filepath and filepath not in seen_paths:
                seen_paths.add(filepath)
                serializable_images.append(img_dict)
            elif not url and not filepath:
                # No dedup key, just add
                serializable_images.append(img_dict)

    # Only return first image to avoid showing duplicates
    if len(serializable_images) > 1:
        serializable_images = [serializable_images[0]]

    return ChatTurnResult(
        response=response,
        tool_calls=tool_calls,
        trace=trace,
        generated_images=serializable_images,
    )
