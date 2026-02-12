from __future__ import annotations

from typing import Dict, List, Literal

from services import storage


def serialize_tool_calls(tool_calls: object) -> List[Dict[str, object]] | None:
    if not tool_calls:
        return None
    if isinstance(tool_calls, dict):
        tool_calls = [tool_calls]
    if not isinstance(tool_calls, list):
        try:
            tool_calls = list(tool_calls)
        except (TypeError, ValueError):
            return [{"name": str(tool_calls)}]
    serialized: List[Dict[str, object]] = []
    for tool_call in tool_calls:
        if tool_call is None:
            continue
        if hasattr(tool_call, "get"):
            serialized.append(dict(tool_call))
            continue
        if hasattr(tool_call, "__dict__"):
            sanitized: Dict[str, object] = {}
            for key, value in tool_call.__dict__.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    sanitized[key] = value
                else:
                    sanitized[key] = str(value)
            serialized.append(sanitized)
            continue
        serialized.append({"name": str(tool_call)})
    return serialized or None


def build_chat_message(
    role: Literal["user", "assistant"],
    content: str,
    *,
    trace: Dict[str, object] | None = None,
    tool_calls: object | None = None,
    images: List[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    payload: Dict[str, object] = {
        "role": role,
        "content": content,
        "tool_calls": serialize_tool_calls(tool_calls),
    }
    if images:
        payload["images"] = images
    if trace:
        payload["trace"] = trace
    return payload


def append_chat(history: List[Dict[str, object]], message: Dict[str, object]) -> None:
    history.append(message)


def persist_chat_history(
    session_id: str | None, history: List[Dict[str, object]]
) -> None:
    if session_id:
        storage.save_chat_history(session_id, history)


def append_and_persist_chat(
    history: List[Dict[str, object]],
    session_id: str | None,
    role: Literal["user", "assistant"],
    content: str,
    *,
    trace: Dict[str, object] | None = None,
    tool_calls: object | None = None,
    images: List[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    message = build_chat_message(
        role,
        content,
        trace=trace,
        tool_calls=tool_calls,
        images=images,
    )
    append_chat(history, message)
    persist_chat_history(session_id, history)
    return message
