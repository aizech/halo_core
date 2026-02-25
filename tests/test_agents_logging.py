from __future__ import annotations

import logging

from services import agents


def test_build_chat_agent_logs_active_mcp_servers(caplog, monkeypatch):
    agent_config = {
        "id": "chat",
        "name": "HALO Master",
        "mcp_servers": [
            {"name": "airbnb", "enabled": True, "transport": "stdio"},
            {"name": "agno-docs", "enabled": True, "transport": "streamable-http"},
            {"name": "sqlite", "enabled": False, "transport": "stdio"},
        ],
    }

    sentinel_team = object()
    monkeypatch.setattr(
        agents,
        "build_master_team_from_config",
        lambda *args, **kwargs: sentinel_team,
    )

    with caplog.at_level(logging.INFO, logger="services.agents"):
        built = agents.build_chat_agent(agent_config=agent_config, prompt="test")

    assert built is sentinel_team
    assert "Configured active MCP servers: ['airbnb', 'agno-docs']" in caplog.text
