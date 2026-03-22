from __future__ import annotations

import streamlit as st

from app import main
import app.pages.config_sections.themes as themes


def render_themes_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("Themes")
    st.caption("Configure visual appearance and theme settings.")

    themes.render(st)


if __name__ == "__main__":
    render_themes_page()
