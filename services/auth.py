"""Authentication helpers and user identity resolution for HALO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import streamlit as st

AuthMode = Literal["local_only", "auth_optional", "auth_required"]


@dataclass
class AuthUser:
    user_id: str
    email: str
    name: str
    avatar_url: str
    provider: str
    is_logged_in: bool
    subject: str


def normalize_auth_mode(value: object) -> AuthMode:
    mode = str(value or "local_only").strip().lower()
    if mode in {"local_only", "auth_optional", "auth_required"}:
        return mode
    return "local_only"


def _read_user_field(raw_user: object, user_data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = user_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in keys:
        value = getattr(raw_user, key, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _read_is_logged_in(raw_user: object, user_data: dict[str, Any]) -> bool:
    value = user_data.get("is_logged_in")
    if isinstance(value, bool):
        return value
    return bool(getattr(raw_user, "is_logged_in", False))


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _canonical_user_id(subject: str, email: str) -> str:
    if subject:
        return f"auth0:{subject}"
    if email:
        return f"email:{_normalize_email(email)}"
    return "local-user"


def _local_auth_user() -> AuthUser:
    return AuthUser(
        user_id="local-user",
        email="",
        name="Local User",
        avatar_url="",
        provider="local",
        is_logged_in=False,
        subject="",
    )


def _streamlit_auth_is_available() -> bool:
    return all(
        hasattr(st, attr)
        for attr in (
            "user",
            "login",
            "logout",
        )
    )


def _has_auth_secrets() -> bool:
    try:
        secrets = getattr(st, "secrets", None)
        if secrets is None:
            return False
        auth_block = secrets.get("auth") if hasattr(secrets, "get") else None
        if auth_block:
            return True
        auth0_domain = secrets.get("AUTH0_DOMAIN") if hasattr(secrets, "get") else None
        auth0_client_id = (
            secrets.get("AUTH0_CLIENT_ID") if hasattr(secrets, "get") else None
        )
        return bool(auth0_domain and auth0_client_id)
    except Exception:
        return False


def is_auth_enabled(config: dict[str, Any] | None = None) -> bool:
    cfg = config or {}
    if not bool(cfg.get("enable_auth_services", False)):
        return False
    if not _streamlit_auth_is_available():
        return False
    return _has_auth_secrets() or bool(cfg.get("auth_provider"))


def _read_streamlit_user_payload() -> tuple[object, dict[str, Any]]:
    raw_user = getattr(st, "user", None)
    if callable(raw_user):
        raw_user = raw_user()
    if raw_user is None:
        return object(), {}
    if isinstance(raw_user, dict):
        return raw_user, dict(raw_user)
    if hasattr(raw_user, "to_dict"):
        try:
            data = raw_user.to_dict()
            if isinstance(data, dict):
                return raw_user, data
        except Exception:
            pass
    payload: dict[str, Any] = {}
    for key in (
        "is_logged_in",
        "email",
        "name",
        "picture",
        "avatar_url",
        "provider",
        "sub",
        "subject",
    ):
        payload[key] = getattr(raw_user, key, None)
    return raw_user, payload


def resolve_auth_user(config: dict[str, Any] | None = None) -> AuthUser:
    cfg = config or {}
    auth_mode = normalize_auth_mode(cfg.get("auth_mode"))

    if auth_mode == "local_only":
        return _local_auth_user()

    if not is_auth_enabled(cfg):
        if auth_mode == "auth_required":
            return AuthUser(
                user_id="",
                email="",
                name="",
                avatar_url="",
                provider="",
                is_logged_in=False,
                subject="",
            )
        return _local_auth_user()

    raw_user, user_data = _read_streamlit_user_payload()
    is_logged_in = _read_is_logged_in(raw_user, user_data)

    if not is_logged_in:
        if auth_mode == "auth_required":
            return AuthUser(
                user_id="",
                email="",
                name="",
                avatar_url="",
                provider="",
                is_logged_in=False,
                subject="",
            )
        return _local_auth_user()

    email = _normalize_email(_read_user_field(raw_user, user_data, "email"))
    subject = _read_user_field(raw_user, user_data, "sub", "subject")
    name = _read_user_field(raw_user, user_data, "name")
    avatar_url = _read_user_field(raw_user, user_data, "avatar_url", "picture")
    provider = _read_user_field(raw_user, user_data, "provider") or "auth"

    return AuthUser(
        user_id=_canonical_user_id(subject, email),
        email=email,
        name=name,
        avatar_url=avatar_url,
        provider=provider,
        is_logged_in=True,
        subject=subject,
    )


def login(provider: str = "auth0") -> None:
    if not hasattr(st, "login"):
        raise RuntimeError("Streamlit login is not available in this environment.")
    login_fn = getattr(st, "login")
    if not callable(login_fn):
        raise RuntimeError("Streamlit login is not callable.")
    try:
        login_fn(provider)
    except TypeError:
        login_fn()


def logout() -> None:
    if not hasattr(st, "logout"):
        raise RuntimeError("Streamlit logout is not available in this environment.")
    logout_fn = getattr(st, "logout")
    if not callable(logout_fn):
        raise RuntimeError("Streamlit logout is not callable.")
    logout_fn()
