from __future__ import annotations

import streamlit as st

from app import main


def render_themes_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("Themes")
    st.caption("Configure visual appearance and theme settings.")

    main._render_theme_configuration(st)


if __name__ == "__main__":
    render_themes_page()
