"""Utilities for normalizing and chunking source text before indexing."""

from __future__ import annotations

import re
from typing import Dict, List

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 75


def normalize_text(text: str | None) -> str:
    """Collapse whitespace and trim the incoming text payload."""
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text)
    return collapsed.strip()


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[str]:
    """Split text into overlapping word windows suitable for embedding."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        if overlap == DEFAULT_CHUNK_OVERLAP and chunk_size < DEFAULT_CHUNK_OVERLAP:
            overlap = max(chunk_size - 1, 0)
        else:
            raise ValueError("overlap must be smaller than chunk_size")

    normalized = normalize_text(text)
    if not normalized:
        return []

    words = normalized.split(" ")
    if len(words) <= chunk_size:
        return [normalized]

    chunks: List[str] = []
    start = 0
    total = len(words)
    while start < total:
        end = min(start + chunk_size, total)
        chunks.append(" ".join(words[start:end]))
        if end >= total:
            break
        remaining = total - end
        if remaining < overlap:
            break
        start = end - overlap
    return chunks


def prepare_chunks(
    title: str,
    type_label: str,
    body: str | None,
    meta: Dict[str, str] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[Dict[str, Dict[str, str] | str]]:
    """Normalize text, chunk it, and attach metadata per chunk."""
    base_text = body if body and body.strip() else title
    chunks = chunk_text(base_text, chunk_size=chunk_size, overlap=overlap)
    if not chunks:
        chunks = [title.strip() or title]

    chunk_count = len(chunks)
    base_meta = {
        "source_title": title,
        "type_label": type_label,
    }
    if meta:
        base_meta.update(meta)

    prepared: List[Dict[str, Dict[str, str] | str]] = []
    for idx, chunk in enumerate(chunks):
        prepared.append(
            {
                "text": chunk,
                "meta": {
                    **base_meta,
                    "chunk_index": str(idx),
                    "chunk_count": str(chunk_count),
                },
            }
        )
    return prepared
