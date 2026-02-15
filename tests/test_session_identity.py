"""Tests for Agno session identity wiring (Task 5)."""

from __future__ import annotations

from services import agents_config, halo_team


def test_team_receives_session_id(monkeypatch):
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

    team = halo_team.build_master_team_from_config(
        config, session_id="sess-123", user_id="user-456"
    )
    assert team is not None
    assert getattr(team, "session_id", None) == "sess-123"
    assert getattr(team, "user_id", None) == "user-456"


def test_team_without_session_id(monkeypatch):
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
    assert getattr(team, "session_id", None) is None
    assert getattr(team, "user_id", None) is None


def test_member_agents_receive_session_id(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    def _fake_configs():
        return {
            "reports": {
                "id": "reports",
                "name": "Reports",
                "skills": ["report"],
            },
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

    team = halo_team.build_master_team_from_config(
        config, session_id="sess-abc", user_id="user-xyz"
    )
    assert team is not None
    members = list(getattr(team, "members", []) or [])
    assert len(members) == 1
    assert getattr(members[0], "session_id", None) == "sess-abc"
    assert getattr(members[0], "user_id", None) == "user-xyz"


def test_build_agent_from_config_receives_session_id(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")
    from agno.models.openai import OpenAIChat

    model = OpenAIChat(id="gpt-5.2", api_key="test-key")
    config = {"id": "test", "name": "Test Agent", "instructions": "Hello."}

    agent = halo_team.build_agent_from_config(
        config, model, session_id="sess-999", user_id="user-111"
    )
    assert agent is not None
    assert getattr(agent, "session_id", None) == "sess-999"
    assert getattr(agent, "user_id", None) == "user-111"
