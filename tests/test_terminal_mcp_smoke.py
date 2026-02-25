from __future__ import annotations

import json
import logging

from services import agents, agents_config


def test_terminal_smoke_chat_config_merges_airbnb_default(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    templates_dir = tmp_path / "templates"
    data_dir.mkdir()
    templates_dir.mkdir()
    (templates_dir / "studio_templates.json").write_text(
        json.dumps({"templates": []}), encoding="utf-8"
    )

    monkeypatch.setattr(agents_config._SETTINGS, "data_dir", data_dir)
    monkeypatch.setattr(agents_config._SETTINGS, "templates_dir", templates_dir)

    agent_dir = data_dir / "agents"
    agent_dir.mkdir()
    (agent_dir / "chat.json").write_text(
        json.dumps(
            {
                "id": "chat",
                "name": "HALO Master",
                "mcp_servers": [
                    {
                        "name": "agno-docs",
                        "enabled": True,
                        "transport": "streamable-http",
                        "url": "https://docs.agno.com/mcp",
                        "command": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loaded = agents_config.load_agent_configs()
    chat = loaded["chat"]
    servers = chat.get("mcp_servers")

    assert isinstance(servers, list)
    assert any(srv.get("name") == "agno-docs" for srv in servers)
    assert any(srv.get("name") == "airbnb" for srv in servers)


def test_terminal_smoke_logs_active_mcp_servers(caplog, monkeypatch):
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
