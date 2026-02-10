from __future__ import annotations

import json

from services import agents_config
from services import presets


def test_apply_preset_updates_chat_config(tmp_path, monkeypatch):
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
    monkeypatch.setattr(agents_config, "_agent_dir", lambda: agent_dir)

    preset_path = tmp_path / "presets.json"
    preset_path.write_text(
        json.dumps(
            {
                "Research": {
                    "model": "openai:gpt-5",
                    "members": ["reports"],
                    "tools": ["pubmed"],
                }
            }
        ),
        encoding="utf-8",
    )

    presets.apply_preset_to_chat("Research", preset_path)

    chat_config_path = agent_dir / "chat.json"
    saved = json.loads(chat_config_path.read_text(encoding="utf-8"))

    assert saved.get("model") == "openai:gpt-5"
    assert saved.get("members") == ["reports"]
    assert saved.get("tools") == ["pubmed"]
