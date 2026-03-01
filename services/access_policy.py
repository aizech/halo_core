"""Auth-only access policy helpers."""

from __future__ import annotations

from typing import Literal

import streamlit as st

from services.auth import AuthUser, login, normalize_auth_mode

AccessLevel = Literal["public", "logged_in", "admin"]


def can_access(level: AccessLevel, auth_user: AuthUser, auth_mode: str) -> bool:
    mode = normalize_auth_mode(auth_mode)
    if mode == "local_only":
        return True

    if level == "public":
        return True
    if level == "logged_in":
        return bool(auth_user.is_logged_in)

    return bool(auth_user.is_logged_in and getattr(auth_user, "is_admin", False))


def deny_access_ui(level: AccessLevel) -> None:
    if level == "admin":
        st.warning("Admin access required.")
        return

    st.info("Please log in to continue.")
    if st.button("Log in", key=f"auth_login_cta_{level}", width="stretch"):
        try:
            login()
        except Exception as exc:
            st.error(f"Login failed: {exc}")
