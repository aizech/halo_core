"""Utilities for LanceDB-backed retrieval over notebook sources."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import lancedb
import numpy as np
import pyarrow as pa
from numpy.typing import NDArray
from openai import OpenAI

from services.settings import get_settings

_SETTINGS = get_settings()
_DB_PATH = Path(_SETTINGS.data_dir) / "lancedb"
_TABLE_NAME = "sources"

_api_key = _SETTINGS.openai_api_key
_client = OpenAI(api_key=_api_key) if _api_key else None


def _escape(value: str) -> str:
    return value.replace("'", "\\'")


def _connect_db() -> lancedb.LanceDBConnection:
    _DB_PATH.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(_DB_PATH))


def _table_has_meta_field(table: lancedb.table.LanceTable, field_name: str) -> bool:
    try:
        meta_field = table.schema.field("meta")
    except KeyError:
        return False
    meta_type = meta_field.type
    if not pa.types.is_struct(meta_type):  # pragma: no cover - defensive
        return False
    return any(child.name == field_name for child in meta_type)


def _read_table_rows(table: lancedb.table.LanceTable) -> List[Dict[str, object]]:
    to_arrow = getattr(table, "to_arrow", None)
    if callable(to_arrow):
        return to_arrow().to_pylist()
    to_pandas = getattr(table, "to_pandas", None)
    if callable(to_pandas):
        data_frame = to_pandas()
        return data_frame.to_dict("records")
    return []


def _ensure_meta_field(
    db: lancedb.LanceDBConnection,
    table: lancedb.table.LanceTable,
    field_name: str,
) -> lancedb.table.LanceTable:
    if _table_has_meta_field(table, field_name):
        return table
    rows = _read_table_rows(table)
    if not rows:
        # Table is empty; drop and let caller recreate with new schema
        db.drop_table(_TABLE_NAME)
        return db.create_table(_TABLE_NAME, data=[])
    for row in rows:
        meta = dict(row.get("meta") or {})
        meta.setdefault(field_name, "")
        row["meta"] = meta
    db.drop_table(_TABLE_NAME)
    db.create_table(_TABLE_NAME, data=rows)
    return db.open_table(_TABLE_NAME)


def _embed(text: str) -> NDArray[np.float32]:
    if _client:
        response = _client.embeddings.create(model="text-embedding-3-small", input=text)
        return np.array(response.data[0].embedding, dtype=np.float32)
    # Deterministic fallback using hashed seed
    seed = abs(hash(text)) % (2**32)
    rng = np.random.default_rng(seed)
    return rng.random(1536, dtype=np.float32)


def index_source_text(title: str, body: str, meta: Dict[str, str]) -> None:
    """Add a document chunk to LanceDB."""
    db = _connect_db()
    record = {
        "text": body,
        "embedding": _embed(body),
        "meta": {"title": title, **meta},
    }
    if _TABLE_NAME in db.table_names():
        table = db.open_table(_TABLE_NAME)
        table = _ensure_meta_field(db, table, "source_id")
        table.add([record])
    else:
        db.create_table(_TABLE_NAME, data=[record])


def query_similar(text: str, limit: int = 5) -> List[dict]:
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return []
    table = db.open_table(_TABLE_NAME)
    query_embedding = _embed(text)
    matches = table.search(query_embedding).metric("cosine").limit(limit).to_list()
    return matches


def delete_source_chunks(source_id: str, title: Optional[str] = None) -> None:
    if not source_id:
        return
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return
    table = db.open_table(_TABLE_NAME)
    condition = f"meta.source_id == '{_escape(source_id)}'"
    try:
        table.delete(condition)
        return
    except Exception:  # source_id missing on older rows
        pass
    if title:
        table.delete(f"meta.title == '{_escape(title)}'")


def rename_source(source_id: str, new_title: str, previous_title: Optional[str] = None) -> None:
    """Rename all chunks for a source, falling back to title matching if needed."""
    if not source_id or not new_title:
        return
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return
    table = db.open_table(_TABLE_NAME)
    values = {"meta.title": new_title}
    condition = f"meta.source_id == '{_escape(source_id)}'"
    try:
        table.update(where=condition, values=values)
        return
    except Exception:
        pass
    if previous_title:
        condition = f"meta.title == '{_escape(previous_title)}'"
        rows: List[Dict[str, object]] = []
        data_frame = None
        try:
            # pandas offers the most convenient conversion, but keep it optional
            import pandas as pd  # type: ignore[import-not-found]  # noqa: F401

            if hasattr(table, "to_pandas"):
                data_frame = table.to_pandas()  # type: ignore[attr-defined]
        except (ImportError, ModuleNotFoundError):
            data_frame = None
        if data_frame is not None:
            rows = data_frame.to_dict("records")
        else:
            to_arrow = getattr(table, "to_arrow", None)
            if callable(to_arrow):
                rows = to_arrow().to_pylist()
        updated_rows = []
        for row in rows:
            meta = dict(row.get("meta") or {})
            if meta.get("title") == previous_title:
                meta["title"] = new_title
                updated_rows.append({**row, "meta": meta})
        if not updated_rows:
            return
        table.delete(condition)
        table.add(updated_rows)
