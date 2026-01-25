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
