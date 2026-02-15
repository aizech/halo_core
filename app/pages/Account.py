from __future__ import annotations

import streamlit as st


def render_account_page() -> None:
    st.title("Account")
    st.caption("Manage your profile and preferences.")
    st.info("Account settings will appear here soon.")


if __name__ == "__main__":
    render_account_page()
