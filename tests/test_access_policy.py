"""Tests for services/access_policy.py."""

from __future__ import annotations

from dataclasses import dataclass

from services import access_policy


@dataclass
class _User:
    is_logged_in: bool
    is_admin: bool = False


class _FakeStreamlit:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []
        self.button_result = False

    def warning(self, message: str) -> None:
        self.calls.append(("warning", message))

    def info(self, message: str) -> None:
        self.calls.append(("info", message))

    def error(self, message: str) -> None:
        self.calls.append(("error", message))

    def button(self, label: str, **_kwargs) -> bool:
        self.calls.append(("button", label))
        return self.button_result


def test_can_access_public_always_true():
    assert access_policy.can_access("public", _User(False), "auth_required") is True


def test_can_access_logged_in_requires_auth_when_not_local_mode():
    assert access_policy.can_access("logged_in", _User(False), "auth_optional") is False
    assert access_policy.can_access("logged_in", _User(True), "auth_optional") is True


def test_can_access_admin_requires_admin_flag():
    assert (
        access_policy.can_access("admin", _User(True, is_admin=False), "auth_optional")
        is False
    )
    assert (
        access_policy.can_access("admin", _User(True, is_admin=True), "auth_optional")
        is True
    )


def test_can_access_allows_everything_in_local_mode():
    assert access_policy.can_access("logged_in", _User(False), "local_only") is True
    assert access_policy.can_access("admin", _User(False), "local_only") is True


def test_deny_access_ui_shows_admin_warning(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(access_policy, "st", fake_st)

    access_policy.deny_access_ui("admin")

    assert ("warning", "Admin access required.") in fake_st.calls


def test_deny_access_ui_renders_login_cta(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(access_policy, "st", fake_st)

    access_policy.deny_access_ui("logged_in")

    assert ("info", "Please log in to continue.") in fake_st.calls
    assert ("button", "Log in") in fake_st.calls


def test_deny_access_ui_calls_login_when_button_clicked(monkeypatch):
    fake_st = _FakeStreamlit()
    fake_st.button_result = True
    login_called = {"value": False}

    def _fake_login() -> None:
        login_called["value"] = True

    monkeypatch.setattr(access_policy, "st", fake_st)
    monkeypatch.setattr(access_policy, "login", _fake_login)

    access_policy.deny_access_ui("logged_in")

    assert login_called["value"] is True
