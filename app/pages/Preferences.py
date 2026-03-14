from __future__ import annotations

import streamlit as st

from app import main


def render_preferences_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("Preferences")
    st.caption("Configure app functionality, authentication, and system settings.")

    main._render_preferences_configuration(st)


if __name__ == "__main__":
    render_preferences_page()
