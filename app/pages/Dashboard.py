from __future__ import annotations

import streamlit as st


def render_dashboard_page() -> None:
    st.title("Dashboard")
    st.caption("Quick status view for your notebooks and agents.")
    st.info("Dashboard details will appear here soon.")


if __name__ == "__main__":
    render_dashboard_page()
