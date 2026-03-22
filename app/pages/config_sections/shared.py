from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict

import streamlit as st

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


# ---------------------------------------------------------------------------
# Config change-tracking helpers (migrated from app/main.py)
# ---------------------------------------------------------------------------


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def config_saved_state_key(section_key: str) -> str:
    return f"cfg_saved_at_{section_key}"


def config_baseline_state_key(section_key: str) -> str:
    return f"cfg_baseline_{section_key}"


def config_signature(payload: object) -> str:
    try:
        return json.dumps(payload, sort_keys=True, default=str)
    except TypeError:
        return repr(payload)


def set_config_baseline(section_key: str, payload: object) -> None:
    st.session_state[config_baseline_state_key(section_key)] = config_signature(payload)


def render_config_dirty_hint(
    container: st.delta_generator.DeltaGenerator,
    section_key: str,
    payload: object,
    message: str = "Ungespeicherte Änderungen.",
) -> bool:
    current_sig = config_signature(payload)
    baseline_key = config_baseline_state_key(section_key)
    baseline_sig = st.session_state.get(baseline_key)
    if not isinstance(baseline_sig, str):
        st.session_state[baseline_key] = current_sig
        return False
    is_dirty = baseline_sig != current_sig
    if is_dirty:
        container.warning(message)
    return is_dirty


def mark_config_saved(
    container: st.delta_generator.DeltaGenerator,
    section_key: str,
    message: str,
    payload: object | None = None,
) -> None:
    saved_at = datetime.now().strftime("%H:%M:%S")
    st.session_state[config_saved_state_key(section_key)] = saved_at
    if payload is not None:
        set_config_baseline(section_key, payload)
    container.success(message)


def render_config_saved_caption(
    container: st.delta_generator.DeltaGenerator,
    section_key: str,
) -> None:
    saved_at = st.session_state.get(config_saved_state_key(section_key))
    if isinstance(saved_at, str) and saved_at.strip():
        container.caption(f"Zuletzt gespeichert: {saved_at}")
