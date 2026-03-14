from __future__ import annotations

import streamlit as st

from app import main
import app.pages.config_sections.advanced as advanced
import app.pages.config_sections.chat_memory as chat_memory
import app.pages.config_sections.sources as sources
import app.pages.config_sections.studio as studio


def render_configuration_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()
    st.title("Configuration")
    st.caption("Manage app settings by section.")

    st.divider()
    st.caption("Core functionality configuration below.")

    sources_tab, chat_tab, studio_tab, advanced_tab = st.tabs(
        ["Sources", "Chat", "Studio", "Advanced"]
    )

    with sources_tab:
        sources.render(st)
    with chat_tab:
        chat_memory.render(st)
    with studio_tab:
        studio.render(st)
    with advanced_tab:
        advanced.render(st)


if __name__ == "__main__":
    render_configuration_page()
