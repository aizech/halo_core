from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from services import agents_config

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_PRESETS_PATH = _PROJECT_ROOT / "presets.json"

_LOGGER = logging.getLogger(__name__)


def load_presets(path: str | Path | None = None) -> Dict[str, Dict[str, object]]:
    presets_path = Path(path) if path is not None else _DEFAULT_PRESETS_PATH
    if not presets_path.exists():
        _LOGGER.warning("Preset file not found: %s", presets_path)
        return {}
    with presets_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Preset file must contain a JSON object.")
    return payload


def apply_preset_to_chat(
    preset_name: str, presets_path: str | Path | None = None
) -> Dict[str, object]:
    presets = load_presets(presets_path)
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}")
    preset = presets[preset_name]
    if not isinstance(preset, dict):
        raise ValueError(f"Preset '{preset_name}' must be a JSON object.")

    update: Dict[str, object] = {}
    if "model" in preset:
        update["model"] = str(preset["model"])
    if "tools" in preset:
        tools = preset.get("tools")
        if not isinstance(tools, list) or not all(
            isinstance(tool, str) for tool in tools
        ):
            raise ValueError("Preset tools must be a list of strings.")
        update["tools"] = tools
    if "members" in preset:
        members = preset.get("members")
        if not isinstance(members, list) or not all(
            isinstance(member, str) for member in members
        ):
            raise ValueError("Preset members must be a list of strings.")
        update["members"] = members
    if not update:
        raise ValueError("Preset must define model, tools, or members.")

    configs = agents_config.load_agent_configs()
    chat_config = configs.get("chat")
    if not isinstance(chat_config, dict):
        raise ValueError("Chat agent config not found.")
    updated = {**chat_config, **update}
    agents_config.save_agent_config("chat", updated)
    return updated
