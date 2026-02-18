from __future__ import annotations

import streamlit as st

from app.pages.config_sections import shared
from services import connectors


def render(container: st.delta_generator.DeltaGenerator) -> None:
    container.subheader("Quellen & Connectoren")
    enabled = container.multiselect(
        "Aktivierte Connectoren",
        options=list(connectors.AVAILABLE_CONNECTORS.keys()),
        default=st.session_state["config"].get("enabled_connectors", []),
        format_func=lambda key: connectors.AVAILABLE_CONNECTORS[key].name,
    )
    container.subheader("Bildgenerierung")
    image_model = container.selectbox(
        "Bildmodell",
        options=["gpt-image-1", "dall-e-3"],
        index=["gpt-image-1", "dall-e-3"].index(
            st.session_state["config"].get("image_model", "gpt-image-1")
        ),
    )
    if container.button("Speichern", key="cfg_sources_save_connectors"):
        updates = {
            "enabled_connectors": enabled,
            "image_model": image_model,
            "log_agent_payload": bool(st.session_state.get("log_agent_payload", True)),
            "log_agent_response": bool(
                st.session_state.get("log_agent_response", True)
            ),
            "log_agent_errors": bool(st.session_state.get("log_agent_errors", True)),
            "log_user_requests": bool(st.session_state.get("log_user_requests", True)),
            "log_stream_events": bool(st.session_state.get("log_stream_events", False)),
        }
        shared.save_payload(st.session_state["config"], updates)
        container.success("Connector-Einstellungen aktualisiert")
