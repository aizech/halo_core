from __future__ import annotations

import streamlit as st

from app import main
import app.pages.config_sections.advanced as advanced
import app.pages.config_sections.app_design as app_design
import app.pages.config_sections.chat_memory as chat_memory
import app.pages.config_sections.sources as sources
import app.pages.config_sections.studio as studio


def render_configuration_page() -> None:
    main._init_state()
    main.render_sidebar()
    st.title("Configuration")
    st.caption("Manage app settings by section.")

    app_tab, sources_tab, chat_tab, studio_tab, advanced_tab = st.tabs(
        ["App", "Sources", "Chat", "Studio", "Advanced"]
    )

    with app_tab:
        app_design.render(st)
    with sources_tab:
        sources.render(st)
    with chat_tab:
        chat_memory.render(st)
    with studio_tab:
        studio.render(st)
    with advanced_tab:
        advanced.render(st)

    st.divider()
    st.subheader("Agent Configuration")
    if st.button("Open Agent Config", key="open_agent_config", width="stretch"):
        try:
            st.switch_page("pages/Agent_Config.py")
        except Exception:
            st.error("Agent Config navigation requires Streamlit multipage.")


if __name__ == "__main__":
    render_configuration_page()
