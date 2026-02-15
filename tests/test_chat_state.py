"""Tests for services/chat_state.py centralized state helpers (Task 10)."""

from __future__ import annotations

from services import chat_state, storage


def test_default_config_has_expected_keys():
    assert "image_model" in chat_state.DEFAULT_CONFIG
    assert "log_stream_events" in chat_state.DEFAULT_CONFIG
    assert "chat_preset" in chat_state.DEFAULT_CONFIG
    assert chat_state.DEFAULT_CONFIG["chat_preset"] == "Default"


def test_new_session_id_is_unique():
    id1 = chat_state.new_session_id()
    id2 = chat_state.new_session_id()
    assert id1 != id2
    assert len(id1) == 32  # uuid4().hex


def test_default_chat_history_has_welcome():
    history = chat_state.default_chat_history()
    assert len(history) == 1
    assert history[0]["role"] == "assistant"
    assert "Willkommen" in history[0]["content"]


def test_default_chat_history_returns_new_list():
    h1 = chat_state.default_chat_history()
    h2 = chat_state.default_chat_history()
    assert h1 is not h2
    assert h1 == h2


def test_load_or_default_config_uses_defaults():
    config = chat_state.load_or_default_config()
    assert config["image_model"] == "gpt-image-1"
    assert config["log_stream_events"] is False


def test_load_or_default_config_merges_stored():
    stored = {"image_model": "dall-e-3", "custom_key": "value"}
    config = chat_state.load_or_default_config(stored_config=stored)
    assert config["image_model"] == "dall-e-3"
    assert config["custom_key"] == "value"
    assert config["chat_preset"] == "Default"  # default preserved


def test_load_or_default_config_adds_connectors():
    config = chat_state.load_or_default_config(
        enabled_connectors=["pubmed", "wikipedia"]
    )
    assert config["enabled_connectors"] == ["pubmed", "wikipedia"]


def test_load_or_default_chat_history_returns_welcome_when_no_session():
    history = chat_state.load_or_default_chat_history(None)
    assert len(history) == 1
    assert "Willkommen" in history[0]["content"]


def test_load_or_default_chat_history_loads_stored(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "_CHAT_HISTORY_DIR", tmp_path / "chat_history")

    stored = [{"role": "user", "content": "Hallo"}]
    storage.save_chat_history("sess-1", stored)

    history = chat_state.load_or_default_chat_history("sess-1")
    assert history == stored


def test_load_or_default_chat_history_falls_back_when_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "_CHAT_HISTORY_DIR", tmp_path / "chat_history")

    history = chat_state.load_or_default_chat_history("nonexistent-session")
    assert len(history) == 1
    assert "Willkommen" in history[0]["content"]


def test_ensure_state_key_sets_missing():
    state = {}
    chat_state.ensure_state_key(state, "foo", lambda: 42)
    assert state["foo"] == 42


def test_ensure_state_key_preserves_existing():
    state = {"foo": "original"}
    chat_state.ensure_state_key(state, "foo", lambda: "replaced")
    assert state["foo"] == "original"


def test_ensure_state_key_calls_factory_once():
    call_count = 0

    def factory():
        nonlocal call_count
        call_count += 1
        return []

    state = {}
    chat_state.ensure_state_key(state, "items", factory)
    chat_state.ensure_state_key(state, "items", factory)
    assert call_count == 1
    assert state["items"] == []


class _ToolCallObject:
    def __init__(self) -> None:
        self.name = "search"
        self.args = {"q": "halo"}


class _NonIterableTool:
    def __str__(self) -> str:
        return "tool-call"


def test_serialize_tool_calls_dict_input_is_wrapped_list():
    serialized = chat_state.serialize_tool_calls(
        {"name": "search", "args": {"q": "halo"}}
    )

    assert serialized == [{"name": "search", "args": {"q": "halo"}}]


def test_serialize_tool_calls_object_sanitizes_non_primitive_values():
    serialized = chat_state.serialize_tool_calls([_ToolCallObject()])

    assert serialized is not None
    assert serialized[0]["name"] == "search"
    assert isinstance(serialized[0]["args"], str)
    assert "halo" in serialized[0]["args"]


def test_serialize_tool_calls_non_iterable_falls_back_to_name():
    serialized = chat_state.serialize_tool_calls(_NonIterableTool())

    assert serialized == [{"name": "tool-call"}]


def test_append_and_persist_chat_preserves_session_history(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "_CHAT_HISTORY_DIR", tmp_path / "chat_history")

    history: list[dict[str, object]] = []
    chat_state.append_and_persist_chat(
        history,
        "sess-42",
        "assistant",
        "Antwort",
        trace={"agent_name": "HALO"},
        tool_calls={"name": "search"},
    )

    loaded = storage.load_chat_history("sess-42")
    assert loaded == history
    assert loaded[-1]["content"] == "Antwort"
    assert loaded[-1]["tool_calls"] == [{"name": "search"}]
