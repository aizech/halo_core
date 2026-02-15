"""Tests for optional Agno DB-backed memory (Task 6)."""

from __future__ import annotations

from services import storage, agents_config, halo_team


def test_get_agent_db_returns_none_when_not_configured(monkeypatch):
    """Without HALO_AGENT_DB, get_agent_db() returns None (JSON-only fallback)."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", None)

    db = storage.get_agent_db()
    assert db is None


def test_get_agent_db_returns_sqlite_when_configured(monkeypatch, tmp_path):
    """With HALO_AGENT_DB set, get_agent_db() returns a SqliteDb instance."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    db_path = str(tmp_path / "test_agent.db")
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", db_path)

    db = storage.get_agent_db()
    assert db is not None
    from agno.db.sqlite import SqliteDb

    assert isinstance(db, SqliteDb)


def test_get_agent_db_is_cached(monkeypatch, tmp_path):
    """Subsequent calls return the same cached instance."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    db_path = str(tmp_path / "test_agent_cached.db")
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", db_path)

    db1 = storage.get_agent_db()
    db2 = storage.get_agent_db()
    assert db1 is db2


def test_team_gets_db_when_configured(monkeypatch, tmp_path):
    """Team and members receive db= when agent_db_file is set."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    db_path = str(tmp_path / "team_agent.db")
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", db_path)
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": [],
        "instructions": "Test.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config, session_id="s1")
    assert team is not None
    assert getattr(team, "db", None) is not None
    assert getattr(team, "add_history_to_context", False) is True
    assert getattr(team, "enable_user_memories", False) is True


def test_team_no_db_when_not_configured(monkeypatch):
    """Team has no db= when agent_db_file is not set."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", None)
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": [],
        "instructions": "Test.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config)
    assert team is not None
    assert getattr(team, "db", None) is None
    assert getattr(team, "add_history_to_context", True) is False


def test_member_agent_gets_db_when_configured(monkeypatch, tmp_path):
    """Member agents receive db= when agent_db_file is set."""
    monkeypatch.setattr(storage, "_AGENT_DB_INITIALIZED", False)
    monkeypatch.setattr(storage, "_AGENT_DB", None)
    db_path = str(tmp_path / "member_agent.db")
    monkeypatch.setattr(storage._SETTINGS, "agent_db_file", db_path)
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    def _fake_configs():
        return {
            "reports": {"id": "reports", "name": "Reports", "skills": ["report"]},
        }

    monkeypatch.setattr(agents_config, "load_agent_configs", _fake_configs)

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": ["reports"],
        "coordination_mode": "always_delegate",
        "instructions": "Test.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config, session_id="s2")
    assert team is not None
    members = list(getattr(team, "members", []) or [])
    assert len(members) == 1
    assert getattr(members[0], "db", None) is not None
    assert getattr(members[0], "enable_user_memories", False) is True
