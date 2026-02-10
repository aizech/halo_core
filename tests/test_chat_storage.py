from services import storage


def _set_temp_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(storage, "_DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "_CHAT_HISTORY_DIR", tmp_path / "chat_history")


def test_load_chat_history_returns_empty_when_missing(tmp_path, monkeypatch):
    _set_temp_data_dir(monkeypatch, tmp_path)

    history = storage.load_chat_history("session-1")

    assert history == []


def test_save_and_load_chat_history_round_trip(tmp_path, monkeypatch):
    _set_temp_data_dir(monkeypatch, tmp_path)

    payload = [
        {"role": "user", "content": "Hallo"},
        {"role": "assistant", "content": "Hi", "tool_calls": None},
    ]

    storage.save_chat_history("session-1", payload)

    loaded = storage.load_chat_history("session-1")

    assert loaded == payload
