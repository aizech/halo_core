from __future__ import annotations

import streamlit as st

from app import main


def render_dashboard_page() -> None:
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()
    st.title("Dashboard")
    st.caption("Quick status view for your notebooks and agents.")
    st.info("Dashboard details will appear here soon.")


if __name__ == "__main__":
    render_dashboard_page()
