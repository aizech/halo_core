from __future__ import annotations

from types import SimpleNamespace

from app import main


class _FakeStreamlit:
    def __init__(self, session_state: dict):
        self.session_state = session_state


def test_require_access_returns_true_when_guards_disabled(monkeypatch):
    fake_st = _FakeStreamlit(session_state={"config": {"enable_access_guards": False}})
    monkeypatch.setattr(main, "st", fake_st)

    assert main.require_access("logged_in") is True


def test_require_access_returns_true_for_allowed_user(monkeypatch):
    fake_st = _FakeStreamlit(
        session_state={
            "config": {"enable_access_guards": True, "auth_mode": "auth_optional"},
            "auth_user": SimpleNamespace(is_logged_in=True),
        }
    )
    monkeypatch.setattr(main, "st", fake_st)

    assert main.require_access("logged_in") is True


def test_require_access_denies_when_not_allowed(monkeypatch):
    fake_st = _FakeStreamlit(
        session_state={
            "config": {"enable_access_guards": True, "auth_mode": "auth_optional"},
            "auth_user": SimpleNamespace(is_logged_in=False),
        }
    )
    denied = {"level": ""}

    def _fake_deny(level: str) -> None:
        denied["level"] = level

    monkeypatch.setattr(main, "st", fake_st)
    monkeypatch.setattr(main.access_policy, "deny_access_ui", _fake_deny)

    assert main.require_access("logged_in") is False
    assert denied["level"] == "logged_in"
