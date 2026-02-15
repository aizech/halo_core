from __future__ import annotations

import json
from typing import Dict, List

import streamlit as st

from services import agents_config


def _load_configs() -> Dict[str, Dict[str, object]]:
    return agents_config.load_agent_configs()


def _save_config(agent_id: str, config: Dict[str, object]) -> None:
    agents_config.save_agent_config(agent_id, config)


def _as_text_lines(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def _parse_lines(raw: str) -> List[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def render_agent_config_page() -> None:
    st.title("Agent Config")
    st.caption("Manage per-agent configuration files.")

    try:
        configs = _load_configs()
    except ValueError as exc:
        st.error(f"Agent config validation failed: {exc}")
        return
    except Exception as exc:
        st.error(f"Failed to load agent configs: {exc}")
        return
    agent_ids = sorted(configs.keys())
    if not agent_ids:
        st.info("No agents found.")
        return

    selected_id = st.selectbox("Select agent", options=agent_ids)
    current = dict(configs[selected_id])

    st.text_input("ID", value=str(current.get("id", "")), disabled=True)
    name = st.text_input("Name", value=str(current.get("name", "")))
    role = st.text_input("Role", value=str(current.get("role", "")))
    description = st.text_area(
        "Description", value=str(current.get("description", "")), height=80
    )
    enabled = st.checkbox("Enabled", value=bool(current.get("enabled", True)))
    instructions = st.text_area(
        "Instructions", value=str(current.get("instructions", "")), height=160
    )
    st.subheader("Capabilities")
    skills_raw = st.text_area(
        "Skills (one per line)", value=_as_text_lines(current.get("skills"))
    )
    tools_raw = st.text_area(
        "Tools (one per line)", value=_as_text_lines(current.get("tools"))
    )
    mcp_raw = st.text_area(
        "MCP calls (one per line)", value=_as_text_lines(current.get("mcp_calls"))
    )
    st.subheader("Routing & Runtime")
    model = st.text_input("Model override", value=str(current.get("model", "")))
    memory_scope = st.text_input(
        "Memory scope", value=str(current.get("memory_scope", ""))
    )
    coordination_options = [
        "",
        "direct_only",
        "delegate_on_complexity",
        "always_delegate",
        "coordinated_rag",
    ]
    current_mode = str(current.get("coordination_mode", ""))
    if current_mode not in coordination_options:
        coordination_options.append(current_mode)
    coordination_mode = st.selectbox(
        "Coordination mode",
        options=coordination_options,
        index=coordination_options.index(current_mode),
        help="Controls how the master agent delegates to team members.",
    )
    stream_events = st.checkbox(
        "Stream events", value=bool(current.get("stream_events", True))
    )

    if st.button("Save configuration", type="primary"):
        updated = {
            **current,
            "name": name.strip(),
            "description": description.strip(),
            "role": role.strip(),
            "instructions": instructions.strip(),
            "skills": _parse_lines(skills_raw),
            "tools": _parse_lines(tools_raw),
            "mcp_calls": _parse_lines(mcp_raw),
            "model": model.strip() or None,
            "memory_scope": memory_scope.strip() or None,
            "coordination_mode": coordination_mode.strip() or None,
            "stream_events": stream_events,
            "enabled": enabled,
        }
        updated = {k: v for k, v in updated.items() if v is not None}
        try:
            json.dumps(updated)
        except TypeError as exc:
            st.error(f"Config is not JSON-serializable: {exc}")
            return
        try:
            _save_config(selected_id, updated)
        except Exception as exc:
            st.error(f"Failed to save config: {exc}")
        else:
            st.success("Saved.")


if __name__ == "__main__":
    render_agent_config_page()
