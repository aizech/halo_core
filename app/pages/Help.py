from __future__ import annotations

import streamlit as st


def render_help_page() -> None:
    st.title("Help")
    st.caption("Find guidance and support resources.")
    st.markdown("""
        - Review **AGENTS.md** for workflow rules.
        - Reach out in **#halo-support** for help.
        - Check the docs in the repository for more details.
        """)


if __name__ == "__main__":
    render_help_page()
