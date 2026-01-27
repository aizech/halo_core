from __future__ import annotations

from agno.tools.wikipedia import WikipediaTools

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
