"""User memory helpers for listing and deleting Agno memories."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

from services import storage


@dataclass
class UserMemoryView:
    memory_id: str
    memory_text: str
    topics: List[str]
    created_at: str


@dataclass
class MemoryDeleteResult:
    deleted_count: int
    failed_ids: List[str]


def resolve_user_id(session_state: Dict[str, Any]) -> str:
    config = session_state.get("config")
    if isinstance(config, dict):
        config_user = str(config.get("user_id") or "").strip()
        if config_user:
            return config_user
    state_user = str(session_state.get("user_id") or "").strip()
    if state_user:
        return state_user
    return "local-user"


def is_memory_backend_enabled() -> bool:
    return storage.get_agent_db() is not None


def ensure_memory_schema_if_needed() -> None:
    db = storage.get_agent_db()
    connection = getattr(db, "connection", None)
    if connection is None:
        return
    connection.execute("""
        CREATE TABLE IF NOT EXISTS agno_memories (
            memory_id VARCHAR NOT NULL PRIMARY KEY,
            memory JSON NOT NULL,
            input VARCHAR,
            agent_id VARCHAR,
            team_id VARCHAR,
            user_id VARCHAR,
            topics JSON,
            feedback VARCHAR,
            created_at BIGINT NOT NULL,
            updated_at BIGINT
        )
        """)
    connection.commit()


def _format_timestamp(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        )
    if isinstance(value, str):
        parsed = value.strip()
        if not parsed:
            return ""
        try:
            if parsed.isdigit():
                return datetime.fromtimestamp(int(parsed), tz=timezone.utc).strftime(
                    "%Y-%m-%d %H:%M"
                )
            return datetime.fromisoformat(parsed.replace("Z", "+00:00")).strftime(
                "%Y-%m-%d %H:%M"
            )
        except ValueError:
            return parsed
    return str(value)


def _memory_text(value: Any) -> str:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except Exception:
            return value
        if isinstance(decoded, str):
            return decoded
        return json.dumps(decoded, ensure_ascii=True)
    if isinstance(value, dict):
        if isinstance(value.get("memory"), str):
            return str(value.get("memory"))
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _memory_topics(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except Exception:
            return [value] if value.strip() else []
        if isinstance(decoded, list):
            return [str(item) for item in decoded if str(item).strip()]
        if isinstance(decoded, str) and decoded.strip():
            return [decoded]
        return []
    return [str(value)]


def _from_memory_object(memory: Any) -> UserMemoryView | None:
    memory_id = str(
        getattr(memory, "memory_id", "") or getattr(memory, "id", "")
    ).strip()
    if not memory_id:
        return None
    return UserMemoryView(
        memory_id=memory_id,
        memory_text=_memory_text(getattr(memory, "memory", memory)),
        topics=_memory_topics(getattr(memory, "topics", [])),
        created_at=_format_timestamp(getattr(memory, "created_at", None)),
    )


def list_user_memories(*, user_id: str) -> List[UserMemoryView]:
    db = storage.get_agent_db()
    if db is None:
        return []

    memories = []
    if hasattr(db, "get_user_memories"):
        try:
            memories = db.get_user_memories(user_id=user_id) or []
        except TypeError:
            memories = db.get_user_memories(user_id) or []
        except Exception:
            memories = []

    normalized: List[UserMemoryView] = []
    for memory in memories:
        row = _from_memory_object(memory)
        if row is not None:
            normalized.append(row)
    if normalized:
        return normalized

    connection = getattr(db, "connection", None)
    if connection is None:
        return []

    rows = connection.execute(
        "SELECT memory_id, memory, topics, created_at FROM agno_memories WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    for row in rows:
        normalized.append(
            UserMemoryView(
                memory_id=str(row[0]),
                memory_text=_memory_text(row[1]),
                topics=_memory_topics(row[2]),
                created_at=_format_timestamp(row[3]),
            )
        )
    return normalized


def delete_user_memory(*, user_id: str, memory_id: str) -> bool:
    db = storage.get_agent_db()
    if db is None:
        return False

    if hasattr(db, "delete_user_memory"):
        try:
            db.delete_user_memory(memory_id=memory_id, user_id=user_id)
            return True
        except TypeError:
            try:
                db.delete_user_memory(memory_id=memory_id)
                return True
            except TypeError:
                try:
                    db.delete_user_memory(memory_id)
                    return True
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            pass

    connection = getattr(db, "connection", None)
    if connection is None:
        return False

    cursor = connection.execute(
        "DELETE FROM agno_memories WHERE memory_id = ? AND user_id = ?",
        (memory_id, user_id),
    )
    connection.commit()
    return int(getattr(cursor, "rowcount", 0) or 0) > 0


def delete_user_memories(*, user_id: str, memory_ids: List[str]) -> MemoryDeleteResult:
    deleted_count = 0
    failed_ids: List[str] = []
    for memory_id in memory_ids:
        if delete_user_memory(user_id=user_id, memory_id=memory_id):
            deleted_count += 1
        else:
            failed_ids.append(memory_id)
    return MemoryDeleteResult(deleted_count=deleted_count, failed_ids=failed_ids)


def clear_user_memories(*, user_id: str) -> MemoryDeleteResult:
    memory_ids = [row.memory_id for row in list_user_memories(user_id=user_id)]
    return delete_user_memories(user_id=user_id, memory_ids=memory_ids)
