from __future__ import annotations

import streamlit as st

from app.pages.config_sections import shared
from services import agents, agents_config, presets, storage


def _normalize_agent_tools(raw_tools: object) -> list[str]:
    normalized: list[str] = []
    if isinstance(raw_tools, list):
        for tool in raw_tools:
            if isinstance(tool, str):
                normalized.append(tool)
            else:
                tool_name = type(tool).__name__.lower()
                if "pubmed" in tool_name:
                    normalized.append("pubmed")
                elif "wikipedia" in tool_name:
                    normalized.append("wikipedia")
                elif "mermaid" in tool_name:
                    normalized.append("mermaid")
    return normalized


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render chat memory configuration (migrated from main._render_chat_memory_configuration)."""
    shared.render_config_saved_caption(container, "chat")
    container.caption(
        "Diese Seite konfiguriert den Chat-Orchestrator. Einzelne Agenten (Rolle, Instruktionen, MCP, Tool-Details) bearbeitest du im Tab 'Advanced' oder auf der Seite 'Agent Config'."
    )

    agent_configs_rt = st.session_state.get("agent_configs", {})
    chat_config_rt = (
        agent_configs_rt.get("chat", {}) if isinstance(agent_configs_rt, dict) else {}
    )
    rt_model = str(chat_config_rt.get("model") or "—")
    rt_members = chat_config_rt.get("members", [])
    rt_members_display = (
        ", ".join(rt_members) if isinstance(rt_members, list) and rt_members else "—"
    )
    rt_tools_raw = _normalize_agent_tools(chat_config_rt.get("tools", []))
    rt_tools_display = ", ".join(rt_tools_raw) if rt_tools_raw else "—"
    rt_preset = str(st.session_state.get("config", {}).get("chat_preset") or "—")
    summary_box = container.container(border=True)
    summary_box.markdown("**Aktive Chat-Konfiguration**")
    sum_c1, sum_c2 = summary_box.columns(2)
    sum_c1.markdown(f"**Modell:** `{rt_model}`")
    sum_c1.markdown(f"**Preset:** `{rt_preset}`")
    sum_c2.markdown(f"**Team:** {rt_members_display}")
    sum_c2.markdown(f"**Tools:** {rt_tools_display}")

    # Presets Mapping Table
    container.markdown("### Preset-Team Zuordnung")
    presets_payload = presets.load_presets()
    if presets_payload:
        mapping_data = []
        for preset_name, preset_data in presets_payload.items():
            team_id = preset_data.get("team_id", "—")
            members = preset_data.get("members", [])
            members_str = ", ".join(members) if members else "—"
            mapping_data.append(
                {"Preset": preset_name, "Team": team_id, "Agenten": members_str}
            )
        if mapping_data:
            import pandas as pd

            df = pd.DataFrame(mapping_data)
            container.dataframe(
                df,
                width="stretch",
                hide_index=True,
            )

    payload_key = "cfg_chat_log_agent_payload"
    response_key = "cfg_chat_log_agent_response"
    errors_key = "cfg_chat_log_agent_errors"
    requests_key = "cfg_chat_log_user_requests"
    stream_events_key = "cfg_chat_log_stream_events"

    container.subheader("Agent-Logging")
    safe_log_box = container.container(border=True)
    safe_log_box.markdown("**Produktions-Logging** (immer sicher)")
    safe_log_box.checkbox(
        "Agent Fehler loggen",
        value=bool(st.session_state["config"].get("log_agent_errors", True)),
        key=errors_key,
        help="Fehler und Exceptions aus Agent-Läufen protokollieren.",
    )
    safe_log_box.checkbox(
        "User Requests loggen",
        value=bool(st.session_state["config"].get("log_user_requests", True)),
        key=requests_key,
        help="Eingehende Nutzeranfragen in der Konsole protokollieren.",
    )
    debug_log_box = container.container(border=True)
    debug_log_box.markdown("**Debug-Logging** (nur für Entwicklung / Diagnose)")
    debug_log_box.checkbox(
        "Agent payload loggen",
        value=bool(st.session_state["config"].get("log_agent_payload", True)),
        key=payload_key,
        help="Vollständigen Input-Payload an den Agenten loggen. Kann sensible Daten enthalten.",
    )
    debug_log_box.checkbox(
        "Agent response loggen",
        value=bool(st.session_state["config"].get("log_agent_response", True)),
        key=response_key,
        help="Vollständige Antworten des Agenten loggen. Kann sensible Daten enthalten.",
    )
    debug_log_box.checkbox(
        "Stream-Events debug",
        value=bool(st.session_state["config"].get("log_stream_events", False)),
        key=stream_events_key,
        help="Alle Streaming-Events in der Konsole ausgeben. Nur für Debugging.",
    )

    st.session_state["log_agent_payload"] = bool(
        st.session_state.get(payload_key, True)
    )
    st.session_state["log_agent_response"] = bool(
        st.session_state.get(response_key, True)
    )
    st.session_state["log_agent_errors"] = bool(st.session_state.get(errors_key, True))
    st.session_state["log_user_requests"] = bool(
        st.session_state.get(requests_key, True)
    )
    st.session_state["log_stream_events"] = bool(
        st.session_state.get(stream_events_key, False)
    )

    agents.set_logging_preferences(
        log_payload=bool(st.session_state.get("log_agent_payload", True)),
        log_response=bool(st.session_state.get("log_agent_response", True)),
        log_errors=bool(st.session_state.get("log_agent_errors", True)),
    )

    container.subheader("Chat Presets")
    presets_payload = presets.load_presets()
    preset_names = sorted(presets_payload.keys())
    selected_preset = str(
        st.session_state.get("config", {}).get("chat_preset", "Default")
    )
    if preset_names:
        current_preset = st.session_state.get("config", {}).get(
            "chat_preset", "Default"
        )
        preset_index = (
            preset_names.index(current_preset) if current_preset in preset_names else 0
        )
        selected_preset = container.selectbox(
            "Preset",
            options=preset_names,
            index=preset_index,
            key="chat_preset_selector",
        )
        if container.button("Preset anwenden", key="cfg_chat_apply_preset"):
            try:
                updated = presets.apply_preset_to_chat(selected_preset)
            except ValueError as exc:
                container.error(str(exc))
            else:
                st.session_state["config"]["chat_preset"] = selected_preset
                storage.save_config(st.session_state["config"])
                agent_configs_st = st.session_state.get("agent_configs", {})
                agent_configs_st["chat"] = updated
                st.session_state["agent_configs"] = agent_configs_st
                preset_data = presets_payload.get(selected_preset, {})
                team_id = preset_data.get("team_id")
                if team_id:
                    st.session_state["selected_team_id"] = team_id
                preset_payload = {
                    "chat_preset": selected_preset,
                    "model": str(updated.get("model", "openai:gpt-5.2")),
                    "members": (
                        updated.get("members", [])
                        if isinstance(updated.get("members"), list)
                        else []
                    ),
                    "tools": _normalize_agent_tools(updated.get("tools", [])),
                }
                shared.mark_config_saved(
                    container,
                    "chat",
                    "Chat-Preset angewendet",
                    payload=preset_payload,
                )
    else:
        container.caption("Keine Presets gefunden (presets.json fehlt).")

    container.subheader("Chat Modell & Tools")
    agent_configs = st.session_state.get("agent_configs", {})
    chat_config = (
        agent_configs.get("chat", {}) if isinstance(agent_configs, dict) else {}
    )
    member_options = [
        agent_id for agent_id in agent_configs.keys() if agent_id != "chat"
    ]
    from services.tool_registry import get_all_tool_metadata

    tool_metadata = get_all_tool_metadata()
    available_tools = {
        tool_id: meta.display_name for tool_id, meta in tool_metadata.items()
    }
    chat_model_key = "chat_cfg_model"
    chat_members_key = "chat_cfg_members"
    chat_tools_key = "chat_cfg_tools"
    container.text_input(
        "Chat Model",
        value=str(chat_config.get("model", "openai:gpt-5.2")),
        key=chat_model_key,
        help="Format: provider:model (z.B. openai:gpt-5.2)",
    )
    _chat_model_val = str(st.session_state.get(chat_model_key, "")).strip()
    if _chat_model_val and ":" not in _chat_model_val:
        container.warning(
            f"⚠️ Ungültiges Modell-Format: `{_chat_model_val}`. "
            "Erwartet: `provider:model` (z.B. `openai:gpt-5.2`)."
        )
    container.multiselect(
        "Chat Team",
        options=member_options,
        default=[
            m
            for m in (
                chat_config.get("members", [])
                if isinstance(chat_config.get("members"), list)
                else []
            )
            if m in member_options
        ],
        key=chat_members_key,
    )
    normalized_chat_tools = _normalize_agent_tools(chat_config.get("tools", []))
    if chat_tools_key in st.session_state:
        stored_tools = st.session_state.get(chat_tools_key)
        if isinstance(stored_tools, list) and any(
            not isinstance(tool, str) for tool in stored_tools
        ):
            st.session_state[chat_tools_key] = normalized_chat_tools
    container.multiselect(
        "Chat Tools",
        options=list(available_tools.keys()),
        default=[
            tool_id for tool_id in normalized_chat_tools if tool_id in available_tools
        ],
        format_func=lambda tool_id: available_tools.get(tool_id, tool_id),
        key=chat_tools_key,
    )
    chat_payload = {
        "chat_preset": selected_preset,
        "model": st.session_state.get(chat_model_key, "openai:gpt-5.2"),
        "members": st.session_state.get(chat_members_key, []),
        "tools": st.session_state.get(chat_tools_key, []),
    }
    shared.render_config_dirty_hint(
        container,
        "chat",
        chat_payload,
        "Ungespeicherte Chat-Änderungen.",
    )
    if container.button("Chat-Konfiguration speichern", key="cfg_chat_save_config"):
        updated = {
            **chat_config,
            "model": st.session_state.get(chat_model_key, "openai:gpt-5.2"),
            "members": st.session_state.get(chat_members_key, []),
            "tools": st.session_state.get(chat_tools_key, []),
        }
        agents_config.save_agent_config("chat", updated)
        agent_configs["chat"] = updated
        st.session_state["agent_configs"] = agent_configs
        shared.mark_config_saved(
            container,
            "chat",
            "Chat-Konfiguration gespeichert",
            payload=chat_payload,
        )
