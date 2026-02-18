from __future__ import annotations

from typing import Dict

from services import storage


def merge_payload(
    base: Dict[str, object], updates: Dict[str, object]
) -> Dict[str, object]:
    payload = dict(base)
    payload.update(updates)
    return payload


def build_payload(
    base: Dict[str, object], updates: Dict[str, object]
) -> Dict[str, object]:
    return merge_payload(base, updates)


def save_payload(
    config: Dict[str, object], updates: Dict[str, object]
) -> Dict[str, object]:
    payload = build_payload(config, updates)
    config.clear()
    config.update(payload)
    storage.save_config(config)
    return config


def reset_payload(
    config: Dict[str, object],
    defaults: Dict[str, object],
    keys: list[str] | None = None,
) -> Dict[str, object]:
    if keys is None:
        updates = dict(defaults)
    else:
        updates = {key: defaults[key] for key in keys if key in defaults}
    return save_payload(config, updates)
