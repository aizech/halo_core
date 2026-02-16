"""Utilities for LanceDB-backed retrieval over notebook sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

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

_VECTOR_COL = "vector"
_ID_COL = "id"
_PAYLOAD_COL = "payload"


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


def _sources_schema(dimensions: int) -> pa.Schema:
    vector_field = pa.field(_VECTOR_COL, pa.list_(pa.float32(), dimensions))
    return pa.schema(
        [
            vector_field,
            pa.field(_ID_COL, pa.string()),
            pa.field(_PAYLOAD_COL, pa.string()),
            pa.field("text", pa.string()),
            pa.field(
                "meta",
                pa.struct(
                    [
                        pa.field("title", pa.string()),
                        pa.field("type", pa.string()),
                        pa.field("meta", pa.string()),
                        pa.field("source_id", pa.string()),
                    ]
                ),
            ),
        ]
    )


def _table_vector_col_is_valid(table: lancedb.table.LanceTable) -> bool:
    try:
        field = table.schema.field(_VECTOR_COL)
    except KeyError:
        return False
    list_type = field.type
    return pa.types.is_list(list_type) or pa.types.is_fixed_size_list(list_type)


def _ensure_sources_table(db: lancedb.LanceDBConnection) -> lancedb.table.LanceTable:
    dimensions = int(_embed("dimensions_probe").shape[0])
    schema = _sources_schema(dimensions)

    if _TABLE_NAME not in db.table_names():
        return db.create_table(_TABLE_NAME, schema=schema, mode="overwrite", exist_ok=True)

    table = db.open_table(_TABLE_NAME)
    if _table_vector_col_is_valid(table):
        return table

    legacy_rows = _read_table_rows(table)
    migrated_rows: List[Dict[str, object]] = []
    for row in legacy_rows:
        legacy_text = str(row.get("text") or "")
        legacy_meta = row.get("meta")
        meta_dict: Dict[str, str] = {}
        if isinstance(legacy_meta, dict):
            for key, value in legacy_meta.items():
                if value is None:
                    continue
                meta_dict[str(key)] = str(value)
        payload = {
            "name": meta_dict.get("title") or meta_dict.get("name") or "",
            "meta_data": meta_dict,
            "content": legacy_text,
            "usage": None,
            "content_id": None,
            "content_hash": None,
        }
        migrated_rows.append(
            {
                _VECTOR_COL: row.get("embedding") or _embed(legacy_text),
                _ID_COL: str(uuid4().hex),
                _PAYLOAD_COL: json.dumps(payload, ensure_ascii=True),
                "text": legacy_text,
                "meta": {
                    "title": meta_dict.get("title", ""),
                    "type": meta_dict.get("type", ""),
                    "meta": meta_dict.get("meta", ""),
                    "source_id": meta_dict.get("source_id", ""),
                },
            }
        )

    db.drop_table(_TABLE_NAME)
    db.create_table(_TABLE_NAME, schema=schema, data=migrated_rows)
    return db.open_table(_TABLE_NAME)


def ensure_sources_table() -> None:
    db = _connect_db()
    _ensure_sources_table(db)


def _ensure_meta_field(
    db: lancedb.LanceDBConnection,
    table: lancedb.table.LanceTable,
    field_name: str,
) -> Optional[lancedb.table.LanceTable]:
    if _table_has_meta_field(table, field_name):
        return table
    rows = _read_table_rows(table)
    if not rows:
        # Table is empty; drop and let caller recreate with new schema
        db.drop_table(_TABLE_NAME)
        return None
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
    table = _ensure_sources_table(db)
    meta_payload = {"title": title, **meta}
    payload = {
        "name": title,
        "meta_data": meta_payload,
        "content": body,
        "usage": None,
        "content_id": None,
        "content_hash": None,
    }
    record = {
        _VECTOR_COL: _embed(body),
        _ID_COL: str(uuid4().hex),
        _PAYLOAD_COL: json.dumps(payload, ensure_ascii=True),
        "text": body,
        "meta": {
            "title": str(meta_payload.get("title") or ""),
            "type": str(meta_payload.get("type") or ""),
            "meta": str(meta_payload.get("meta") or ""),
            "source_id": str(meta_payload.get("source_id") or ""),
        },
    }
    table = _ensure_meta_field(db, table, "source_id")
    if table is None:
        table = _ensure_sources_table(db)
    table.add([record])


def query_similar(text: str, limit: int = 5) -> List[dict]:
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return []
    table = _ensure_sources_table(db)
    query_embedding = _embed(text)
    matches = table.search(query_embedding).metric("cosine").limit(limit).to_list()
    normalized: List[dict] = []
    for match in matches or []:
        if not isinstance(match, dict):
            normalized.append({"text": str(match)})
            continue
        payload_raw = match.get(_PAYLOAD_COL)
        meta_value = match.get("meta")
        if isinstance(payload_raw, str) and payload_raw:
            try:
                payload = json.loads(payload_raw)
            except json.JSONDecodeError:
                payload = {}
            normalized.append(
                {
                    "text": payload.get("content") or match.get("text") or "",
                    "meta": payload.get("meta_data") or meta_value or {},
                    "score": match.get("_distance"),
                }
            )
        else:
            normalized.append(
                {
                    "text": match.get("text") or "",
                    "meta": meta_value or {},
                    "score": match.get("_distance"),
                }
            )
    return normalized


def get_source_chunk_texts(
    source_id: str | None = None,
    title: str | None = None,
    *,
    max_chunks: int = 200,
) -> List[str]:
    """Return chunk texts for a source from LanceDB.

    We prefer matching by ``meta.source_id`` because source titles can be renamed.
    """

    if not source_id and not title:
        return []
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return []
    table = _ensure_sources_table(db)

    rows = _read_table_rows(table)
    if not rows:
        return []

    matched: List[str] = []
    for row in rows:
        meta = row.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        if source_id and str(meta.get("source_id") or "") == source_id:
            text = row.get("text")
            if text:
                matched.append(str(text))
        elif not source_id and title and str(meta.get("title") or "") == title:
            text = row.get("text")
            if text:
                matched.append(str(text))
        if len(matched) >= max_chunks:
            break
    return matched


def delete_source_chunks(source_id: str, title: Optional[str] = None) -> None:
    if not source_id:
        return
    db = _connect_db()
    if _TABLE_NAME not in db.table_names():
        return
    table = _ensure_sources_table(db)
    condition = f"meta.source_id == '{_escape(source_id)}'"
    try:
        table.delete(condition)
        return
    except Exception:  # source_id missing on older rows
        pass
    if title:
        table.delete(f"meta.title == '{_escape(title)}'")


def rename_source(
    source_id: str, new_title: str, previous_title: Optional[str] = None
) -> None:
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
