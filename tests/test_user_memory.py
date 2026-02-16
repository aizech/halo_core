"""Tests for services/user_memory.py."""

from __future__ import annotations

from dataclasses import dataclass

from services import user_memory


@dataclass
class FakeMemory:
    memory_id: str
    memory: str
    topics: list[str]
    created_at: int


class FakeCursor:
    def __init__(self, rowcount: int = 0):
        self.rowcount = rowcount


class FakeConnection:
    def __init__(self):
        self.deleted: list[tuple[str, str]] = []
        self.rows = []

    def execute(self, query, params=()):
        text = str(query).strip().lower()
        if text.startswith("select"):
            return type("Rows", (), {"fetchall": lambda _self: list(self.rows)})()
        if text.startswith("delete"):
            memory_id, user_id = params
            before = len(self.rows)
            self.rows = [
                row
                for row in self.rows
                if not (row[0] == memory_id and row[4] == user_id)
            ]
            deleted = before - len(self.rows)
            self.deleted.append((memory_id, user_id))
            return FakeCursor(rowcount=deleted)
        return FakeCursor(rowcount=0)

    def commit(self):
        return None


class FakeDbWithApi:
    def __init__(self):
        self.connection = FakeConnection()
        self.deleted: list[tuple[str, str]] = []

    def get_user_memories(self, user_id: str):
        if user_id == "u1":
            return [FakeMemory("m1", "likes tea", ["prefs"], 1700000000)]
        return []

    def delete_user_memory(self, memory_id: str, user_id: str):
        self.deleted.append((memory_id, user_id))


class FakeDbNoApi:
    def __init__(self):
        self.connection = FakeConnection()
        self.connection.rows = [
            ("m1", '"likes tea"', '["prefs"]', 1700000000, "u1"),
            ("m2", '"likes coffee"', '["prefs"]', 1700000001, "u1"),
        ]


def test_resolve_user_id_prefers_config_then_state():
    assert (
        user_memory.resolve_user_id(
            {"config": {"user_id": "cfg-user"}, "user_id": "state-user"}
        )
        == "cfg-user"
    )
    assert user_memory.resolve_user_id({"user_id": "state-user"}) == "state-user"
    assert user_memory.resolve_user_id({}) == "local-user"


def test_list_user_memories_uses_db_api(monkeypatch):
    db = FakeDbWithApi()
    monkeypatch.setattr(user_memory.storage, "get_agent_db", lambda: db)

    rows = user_memory.list_user_memories(user_id="u1")

    assert len(rows) == 1
    assert rows[0].memory_id == "m1"
    assert rows[0].memory_text == "likes tea"
    assert rows[0].topics == ["prefs"]


def test_delete_user_memory_prefers_db_api(monkeypatch):
    db = FakeDbWithApi()
    monkeypatch.setattr(user_memory.storage, "get_agent_db", lambda: db)

    ok = user_memory.delete_user_memory(user_id="u1", memory_id="m1")

    assert ok is True
    assert db.deleted == [("m1", "u1")]


def test_delete_user_memory_falls_back_to_sql(monkeypatch):
    db = FakeDbNoApi()
    monkeypatch.setattr(user_memory.storage, "get_agent_db", lambda: db)

    ok = user_memory.delete_user_memory(user_id="u1", memory_id="m1")

    assert ok is True
    assert ("m1", "u1") in db.connection.deleted


def test_clear_user_memories_deletes_all_for_user(monkeypatch):
    db = FakeDbNoApi()
    monkeypatch.setattr(user_memory.storage, "get_agent_db", lambda: db)

    result = user_memory.clear_user_memories(user_id="u1")

    assert result.deleted_count == 2
    assert result.failed_ids == []
