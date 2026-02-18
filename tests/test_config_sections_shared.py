from __future__ import annotations

from app.pages.config_sections import shared


def test_build_payload_merges_updates() -> None:
    base = {"a": 1, "b": 2}
    updates = {"b": 3, "c": 4}

    payload = shared.build_payload(base, updates)

    assert payload == {"a": 1, "b": 3, "c": 4}
    assert base == {"a": 1, "b": 2}


def test_save_payload_updates_in_place_and_persists(monkeypatch) -> None:
    saved: list[dict[str, object]] = []

    def _fake_save_config(config: dict[str, object]) -> None:
        saved.append(dict(config))

    monkeypatch.setattr(shared.storage, "save_config", _fake_save_config)

    config = {"enabled_connectors": ["drive"], "image_model": "gpt-image-1"}
    updates = {"enabled_connectors": ["notion"], "log_agent_payload": True}

    result = shared.save_payload(config, updates)

    assert result is config
    assert config == {
        "enabled_connectors": ["notion"],
        "image_model": "gpt-image-1",
        "log_agent_payload": True,
    }
    assert saved == [config]


def test_reset_payload_applies_selected_default_keys(monkeypatch) -> None:
    saved: list[dict[str, object]] = []

    def _fake_save_config(config: dict[str, object]) -> None:
        saved.append(dict(config))

    monkeypatch.setattr(shared.storage, "save_config", _fake_save_config)

    config = {
        "enabled_connectors": ["notion"],
        "image_model": "dall-e-3",
        "log_agent_payload": False,
    }
    defaults = {
        "enabled_connectors": ["drive"],
        "image_model": "gpt-image-1",
        "log_agent_payload": True,
    }

    shared.reset_payload(config, defaults, keys=["enabled_connectors", "image_model"])

    assert config == {
        "enabled_connectors": ["drive"],
        "image_model": "gpt-image-1",
        "log_agent_payload": False,
    }
    assert saved == [config]
