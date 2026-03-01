"""Tests for services/auth.py."""

from __future__ import annotations

from types import SimpleNamespace

from services import auth


class _FakeSecrets(dict):
    pass


class _FakeStreamlit:
    def __init__(self) -> None:
        self.user = None
        self.secrets = _FakeSecrets()
        self._login_calls: list[tuple] = []
        self._logout_calls = 0

    def login(self, *args):
        self._login_calls.append(args)

    def logout(self):
        self._logout_calls += 1


def test_normalize_auth_mode_returns_expected_values():
    assert auth.normalize_auth_mode("local_only") == "local_only"
    assert auth.normalize_auth_mode("AUTH_OPTIONAL") == "auth_optional"
    assert auth.normalize_auth_mode("auth_required") == "auth_required"
    assert auth.normalize_auth_mode("unknown") == "local_only"


def test_is_auth_enabled_requires_flag_and_streamlit_support(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    assert auth.is_auth_enabled({"enable_auth_services": True}) is True
    assert auth.is_auth_enabled({"enable_auth_services": False}) is False


def test_resolve_auth_user_local_only_returns_local_user(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    user = auth.resolve_auth_user(
        {"auth_mode": "local_only", "enable_auth_services": True}
    )

    assert user.user_id == "local-user"
    assert user.is_logged_in is False
    assert user.provider == "local"


def test_resolve_auth_user_required_and_logged_out_returns_empty_identity(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.user = {"is_logged_in": False}
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    user = auth.resolve_auth_user(
        {"auth_mode": "auth_required", "enable_auth_services": True}
    )

    assert user.user_id == ""
    assert user.is_logged_in is False


def test_resolve_auth_user_uses_subject_for_canonical_id(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.user = {
        "is_logged_in": True,
        "email": "Person@Example.COM",
        "name": "Person",
        "sub": "abc123",
        "provider": "auth0",
    }
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    user = auth.resolve_auth_user(
        {"auth_mode": "auth_optional", "enable_auth_services": True}
    )

    assert user.user_id == "auth0:abc123"
    assert user.email == "person@example.com"
    assert user.is_logged_in is True


def test_resolve_auth_user_falls_back_to_email_id(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.user = {
        "is_logged_in": True,
        "email": "Person@Example.COM",
        "name": "Person",
    }
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    user = auth.resolve_auth_user(
        {"auth_mode": "auth_optional", "enable_auth_services": True}
    )

    assert user.user_id == "email:person@example.com"
    assert user.subject == ""


def test_resolve_auth_user_reads_object_user_payload(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.user = SimpleNamespace(
        is_logged_in=True,
        email="obj@example.com",
        name="Obj",
        subject="sub-1",
        provider="auth0",
    )
    fake_st.secrets["auth"] = {"provider": "auth0"}
    monkeypatch.setattr(auth, "st", fake_st)

    user = auth.resolve_auth_user(
        {"auth_mode": "auth_optional", "enable_auth_services": True}
    )

    assert user.user_id == "auth0:sub-1"
    assert user.email == "obj@example.com"


def test_login_calls_streamlit_login(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(auth, "st", fake_st)

    auth.login("auth0")

    assert fake_st._login_calls == [("auth0",)]


def test_logout_calls_streamlit_logout(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(auth, "st", fake_st)

    auth.logout()

    assert fake_st._logout_calls == 1


def test_resolve_canonical_user_id_prefers_authenticated_user_id():
    config = {"user_id": "local-user", "session_id": "sess-1"}
    auth_user = auth.AuthUser(
        user_id="auth0:sub-1",
        email="a@example.com",
        name="A",
        avatar_url="",
        provider="auth0",
        is_logged_in=True,
        subject="sub-1",
    )

    canonical = auth.resolve_canonical_user_id(config, auth_user)

    assert canonical == "auth0:sub-1"


def test_resolve_canonical_user_id_keeps_existing_non_legacy_user_id():
    config = {"user_id": "email:existing@example.com", "session_id": "sess-1"}
    auth_user = auth.AuthUser(
        user_id="local-user",
        email="",
        name="",
        avatar_url="",
        provider="local",
        is_logged_in=False,
        subject="",
    )

    canonical = auth.resolve_canonical_user_id(config, auth_user)

    assert canonical == "email:existing@example.com"


def test_resolve_canonical_user_id_converts_legacy_local_user():
    config = {"user_id": "local-user", "session_id": "sess-xyz"}
    auth_user = auth.AuthUser(
        user_id="local-user",
        email="",
        name="",
        avatar_url="",
        provider="local",
        is_logged_in=False,
        subject="",
    )

    canonical = auth.resolve_canonical_user_id(config, auth_user)

    assert canonical == "local:sess-xyz"
    assert config.get("legacy_user_id") == "local-user"
    assert config.get("local_identity") == "sess-xyz"
