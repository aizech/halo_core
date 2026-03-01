"""Session state helpers for chat history, config defaults, and state initialization."""

from __future__ import annotations

from typing import Any, Dict, List, Literal
from uuid import uuid4

from services import storage

# ── Default configuration values (single source of truth) ──────────────

DEFAULT_CONFIG: Dict[str, Any] = {
    "image_model": "gpt-image-1",
    "log_agent_payload": False,
    "log_agent_response": True,
    "log_agent_errors": True,
    "log_user_requests": True,
    "log_stream_events": False,
    "chat_preset": "Default",
    "auth_mode": "local_only",
    "enable_auth_services": False,
    "enable_auth_ui": False,
    "enable_access_guards": False,
}

WELCOME_MESSAGE: Dict[str, object] = {
    "role": "assistant",
    "content": "Willkommen! Frag mich etwas zu deinen Quellen.",
    "tool_calls": None,
}


def new_session_id() -> str:
    """Generate a new unique session identifier."""
    return uuid4().hex


def default_chat_history() -> List[Dict[str, object]]:
    """Return the default chat history with a welcome message."""
    return [dict(WELCOME_MESSAGE)]


def load_or_default_config(
    stored_config: Dict[str, Any] | None = None,
    enabled_connectors: List[str] | None = None,
) -> Dict[str, Any]:
    """Merge stored config over defaults, returning a complete config dict."""
    config = dict(DEFAULT_CONFIG)
    if enabled_connectors is not None:
        config["enabled_connectors"] = enabled_connectors
    if stored_config:
        config.update(stored_config)
    return config


def load_or_default_chat_history(
    session_id: str | None,
) -> List[Dict[str, object]]:
    """Load persisted chat history or return the default welcome message."""
    if session_id:
        stored = storage.load_chat_history(session_id)
        if stored:
            return stored
    return default_chat_history()


def ensure_state_key(
    state: Dict[str, Any],
    key: str,
    default_factory: Any,
) -> None:
    """Set ``state[key]`` to ``default_factory()`` only if key is missing.

    This is the centralized replacement for scattered ``setdefault`` calls.
    ``default_factory`` must be a callable (e.g. ``list``, ``dict``, ``lambda: 0``).
    """
    if key not in state:
        state[key] = default_factory()


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
