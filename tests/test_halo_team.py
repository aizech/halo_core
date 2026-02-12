from __future__ import annotations

from agno.tools.wikipedia import WikipediaTools

from services import agents_config
from services import halo_team

try:  # optional
    from agno.tools.reasoning import ReasoningTools
except ImportError:  # pragma: no cover
    ReasoningTools = None


def test_build_master_team_from_config_includes_tools(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")
    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": ["wikipedia"],
        "members": [],
        "instructions": "Use tools when needed.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config)
    assert team is not None

    tools = list(getattr(team, "tools", []) or [])
    tool_types = {type(tool) for tool in tools}
    assert WikipediaTools in tool_types
    if ReasoningTools is not None:
        assert ReasoningTools in tool_types


def test_build_master_team_respects_direct_only(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")
    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": ["reports"],
        "coordination_mode": "direct_only",
        "instructions": "Use tools when needed.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config)
    assert team is not None
    assert list(getattr(team, "members", []) or []) == []


def test_build_master_team_delegate_on_complexity(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    def _fake_configs():
        return {
            "reports": {
                "id": "reports",
                "name": "Reports",
                "skills": ["report"],
            },
            "infographic": {
                "id": "infographic",
                "name": "Infographic",
                "skills": ["diagram"],
            },
        }

    monkeypatch.setattr(agents_config, "load_agent_configs", _fake_configs)

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": ["reports", "infographic"],
        "coordination_mode": "delegate_on_complexity",
        "instructions": "Use tools when needed.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config, prompt="report summary")
    assert team is not None
    assert list(getattr(team, "selected_member_ids", []) or []) == ["reports"]


def test_build_master_team_always_delegate(monkeypatch):
    monkeypatch.setattr(halo_team._SETTINGS, "openai_api_key", "test-key")

    def _fake_configs():
        return {
            "reports": {"id": "reports", "name": "Reports"},
            "infographic": {"id": "infographic", "name": "Infographic"},
        }

    monkeypatch.setattr(agents_config, "load_agent_configs", _fake_configs)

    config = {
        "id": "chat",
        "name": "Chat Agent",
        "model": "openai:gpt-5.2",
        "tools": [],
        "members": ["reports", "infographic"],
        "coordination_mode": "always_delegate",
        "instructions": "Use tools when needed.",
        "role": "assistant",
    }

    team = halo_team.build_master_team_from_config(config, prompt="hello")
    assert team is not None
    assert list(getattr(team, "selected_member_ids", []) or []) == [
        "reports",
        "infographic",
    ]
