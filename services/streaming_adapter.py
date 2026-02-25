"""Helpers for normalizing Agno streaming output."""

from __future__ import annotations

import asyncio
import inspect
import logging
from typing import Callable, List


def _normalize_event_name(event: object) -> str | None:
    if event is None:
        return None
    event_name = getattr(event, "value", None) or str(event)
    return (
        str(event_name)
        .replace("RunEvent.", "")
        .replace("run_event.", "")
        .replace(".", "_")
        .casefold()
    )


def _is_team_output(event: object, event_name: str | None) -> bool:
    if event_name is None:
        return False
    return event_name.startswith("teamrun")


def _content_allowed(event: object, event_name: str | None, run_event: object) -> bool:
    allowed = event is None
    if run_event is not None:
        run_content_event = getattr(run_event, "run_content", None)
        run_completed_event = getattr(run_event, "run_completed", None)
        run_content_completed_event = getattr(run_event, "run_content_completed", None)
        for evt in (
            run_content_event,
            run_completed_event,
            run_content_completed_event,
        ):
            if evt is not None and event == evt:
                allowed = True
    if event_name in (
        "runcontent",
        "runcompleted",
        "runcontentcompleted",
        "teamruncontent",
        "teamruncompleted",
        "teamruncontentcompleted",
    ):
        allowed = True
    return allowed


def _is_final_event(event: object, event_name: str | None, run_event: object) -> bool:
    """Detect RunCompleted / TeamRunCompleted / RunContentCompleted / TeamRunContentCompleted."""
    if event_name in (
        "runcompleted",
        "runcontentcompleted",
        "teamruncompleted",
        "teamruncontentcompleted",
    ):
        return True
    if run_event is None:
        return False
    for attr in ("run_completed", "run_content_completed"):
        evt = getattr(run_event, attr, None)
        if evt is not None and event == evt:
            return True
    return False


def _tool_id(tool_item: object) -> str | None:
    if hasattr(tool_item, "get"):
        return tool_item.get("name") or tool_item.get("tool_name")
    return getattr(tool_item, "name", None) or getattr(tool_item, "tool_name", None)


def _append_unique_tool(current_tools: List[object], tool_item: object) -> bool:
    identifier = _tool_id(tool_item)
    if not identifier:
        return False
    for existing in current_tools:
        existing_id = _tool_id(existing)
        if existing_id == identifier:
            return False
    current_tools.append(tool_item)
    return True


def _merge_text(existing: str, incoming: str) -> str:
    if not existing:
        return incoming
    if incoming.startswith(existing):
        return incoming
    if existing.startswith(incoming):
        return existing
    if incoming in existing:
        return existing
    return existing + incoming


def _run_stream(
    agent: object,
    payload: str,
    *,
    images: list[object] | None,
    stream_events: bool,
):
    try:
        if images:
            return agent.run(
                payload,
                images=images,
                stream=True,
                stream_events=stream_events,
                stream_intermediate_steps=True,
            )
        return agent.run(
            payload,
            stream=True,
            stream_events=stream_events,
            stream_intermediate_steps=True,
        )
    except TypeError:
        if images:
            return agent.run(payload, stream=True, images=images)
        return agent.run(payload, stream=True)


def stream_agent_response(
    agent: object,
    payload: str,
    *,
    images: list[object] | None = None,
    stream_events: bool = True,
    run_event: object = None,
    logger: logging.Logger | None = None,
    log_stream_events: bool = False,
    on_response: Callable[[str], None] | None = None,
    on_tools: Callable[[List[object]], None] | None = None,
) -> dict[str, object] | None:
    if agent is None:
        return None

    try:
        run_response = _run_stream(
            agent,
            payload,
            images=images,
            stream_events=stream_events,
        )
    except TypeError:
        return None

    current_tools: List[object] = []
    response = ""
    authoritative_response: str | None = None
    saw_content = False
    saw_member_output = False
    saw_team_output = False
    final_response_emitted = False
    mcp_telemetry_events = []

    def _emit_response() -> None:
        if on_response is not None:
            on_response(response)

    def _emit_tools() -> None:
        if on_tools is not None:
            on_tools(current_tools)

    def _handle_chunk(chunk: object) -> None:
        nonlocal response, authoritative_response, saw_content, saw_member_output, saw_team_output, final_response_emitted
        if chunk is None:
            return

        event = getattr(chunk, "event", None)
        event_name = _normalize_event_name(event)

        if logger is not None and log_stream_events:
            content_val = getattr(chunk, "content", None)
            response_val = getattr(chunk, "response", None)
            logger.info(
                "[STREAM] event=%s is_final=%s final_emitted=%s content=%s response_attr=%s current_response_len=%d",
                event_name,
                _is_final_event(event, event_name, run_event),
                final_response_emitted,
                repr(str(content_val)[:80]) if content_val is not None else "None",
                repr(str(response_val)[:80]) if response_val is not None else "None",
                len(response),
            )

        # Once the authoritative final response has been emitted, ignore
        # ALL subsequent chunks to prevent any corruption of the response.
        if final_response_emitted:
            return

        is_team_output = _is_team_output(event, event_name)
        if is_team_output:
            if not saw_team_output and saw_member_output:
                # Prefer canonical team output over earlier member draft chunks.
                response = ""
                saw_content = False
            saw_team_output = True
        elif saw_team_output:
            # Once team output starts, ignore later member-level chunks.
            return

        tool = getattr(chunk, "tool", None)
        if (
            event in ("TeamToolCallStarted", "ToolCallStarted")
            or event_name in ("teamtoolcallstarted", "toolcallstarted")
        ) and tool is not None:
            if _append_unique_tool(current_tools, tool):
                _emit_tools()

        tools = getattr(chunk, "tools", None)
        if tools:
            changed = False
            for tool_item in tools:
                changed = _append_unique_tool(current_tools, tool_item) or changed
            if changed:
                _emit_tools()

        # Collect MCP tool events for telemetry
        if event_name in (
            "toolcallstarted",
            "toolcallcompleted",
            "teamtoolcallstarted",
            "teamtoolcallcompleted",
        ):
            metrics = getattr(chunk, "metrics", None)
            # Tools inside chunk could be list or object, try to capture relevant info
            tool_info = None
            if tool is not None:
                tool_info = {
                    "name": _tool_id(tool),
                    "type": getattr(tool, "type", "function"),
                }
            elif tools:
                tool_info = [
                    {"name": _tool_id(t), "type": getattr(t, "type", "function")}
                    for t in tools
                ]

            event_data = {
                "event": event_name,
                "tool": tool_info,
                "metrics": (
                    metrics
                    if isinstance(metrics, dict)
                    else getattr(metrics, "__dict__", str(metrics)) if metrics else None
                ),
            }
            mcp_telemetry_events.append(event_data)

        if not _content_allowed(event, event_name, run_event):
            return

        is_final = _is_final_event(event, event_name, run_event)

        content = getattr(chunk, "content", None)
        if content is not None:
            content_text = str(content)
            if is_final and content_text.strip():
                # Some Agno streams carry the authoritative final text in
                # `content` on completed events instead of `response`.
                authoritative_response = content_text
                response = content_text
                saw_content = True
                final_response_emitted = True
                if logger is not None:
                    logger.info("[FINAL CONTENT RESPONSE] %s", content_text[:200])
                _emit_response()
                return
            if not is_team_output:
                saw_member_output = True
            saw_content = True
            response = _merge_text(response, content_text)
            # Don't emit intermediate content chunks to UI
            return

        response_content = getattr(chunk, "response", None)
        if response_content is not None:
            if not is_team_output:
                saw_member_output = True
            text = str(response_content)
            if is_final and text.strip():
                # Final completed events carry the full authoritative response.
                authoritative_response = text
                response = text
                saw_content = True
                final_response_emitted = True
                if logger is not None:
                    logger.info("[FINAL RESPONSE] %s", text[:200])
                _emit_response()
            elif saw_content:
                response = text if text not in response else response
                response = _merge_text(response, text)
            else:
                response = _merge_text(response, text)

    async def _consume_async() -> None:
        async for chunk in run_response:
            _handle_chunk(chunk)

    if inspect.isasyncgen(run_response):
        asyncio.run(_consume_async())
    else:
        for chunk in run_response:
            _handle_chunk(chunk)

    # Safety net: emit the accumulated response only if no authoritative final
    # event was received during the stream (avoids overwriting clean text with
    # corrupted _merge_text accumulation).
    if not final_response_emitted:
        _emit_response()

    return {
        "response": (
            authoritative_response if authoritative_response is not None else response
        ),
        "tools": current_tools,
        "mcp_events": mcp_telemetry_events,
    }
