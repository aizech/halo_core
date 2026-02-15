from __future__ import annotations

import streamlit as st

from app import main


def render_configuration_page() -> None:
    st.title("Configuration")
    st.caption("Manage app settings and agent configuration.")

    main._render_configuration_panel(st)

    st.divider()
    st.subheader("Agent Configuration")
    if st.button("Open Agent Config", key="open_agent_config", width="stretch"):
        try:
            st.switch_page("pages/Agent_Config.py")
        except Exception:
            st.error("Agent Config navigation requires Streamlit multipage.")


if __name__ == "__main__":
    render_configuration_page()
