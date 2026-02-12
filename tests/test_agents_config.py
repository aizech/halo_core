from __future__ import annotations

import json

from services import agents_config


def test_load_agent_configs_merges_defaults(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    templates_dir = tmp_path / "templates"
    data_dir.mkdir()
    templates_dir.mkdir()

    (templates_dir / "studio_templates.json").write_text(
        json.dumps(
            {
                "templates": [
                    {
                        "id": "reports",
                        "title": "Berichte",
                        "description": "Reports",
                        "agent": {"instructions": "Bericht"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(agents_config._SETTINGS, "data_dir", data_dir)
    monkeypatch.setattr(agents_config._SETTINGS, "templates_dir", templates_dir)

    agent_dir = data_dir / "agents"
    agent_dir.mkdir()
    (agent_dir / "chat.json").write_text(
        json.dumps({"id": "chat", "name": "HALO Master"}), encoding="utf-8"
    )

    configs = agents_config.load_agent_configs()

    assert "chat" in configs
    assert configs["chat"].get("members") == ["reports", "infographic"]
    assert "pubmed" in configs
    assert "reports" in configs


def test_load_agent_configs_accepts_optional_fields(tmp_path, monkeypatch):
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
                "skills": ["routing"],
                "mcp_calls": ["web.search"],
                "memory_scope": "session",
            }
        ),
        encoding="utf-8",
    )

    configs = agents_config.load_agent_configs()

    chat = configs["chat"]
    assert chat.get("skills") == ["routing"]
    assert chat.get("mcp_calls") == ["web.search"]
    assert chat.get("memory_scope") == "session"


def test_load_agent_configs_rejects_invalid_optional_fields(tmp_path, monkeypatch):
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
                "skills": [1],
                "coordination_mode": 42,
            }
        ),
        encoding="utf-8",
    )

    try:
        agents_config.load_agent_configs()
    except ValueError as exc:
        assert "skills" in str(exc) or "coordination_mode" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid skills list")
