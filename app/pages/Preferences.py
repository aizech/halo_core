from __future__ import annotations

import streamlit as st

from app import main
import app.pages.config_sections.preferences as preferences


def render_preferences_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("Preferences")
    st.caption("Configure app functionality, authentication, and system settings.")

    preferences.render(st)


if __name__ == "__main__":
    render_preferences_page()
