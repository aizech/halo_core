"""Unit tests for text chunking helpers."""

from __future__ import annotations

import pytest

from services import chunking


def test_chunk_text_returns_full_payload_when_short() -> None:
    result = chunking.chunk_text("hello world", chunk_size=10)
    assert result == ["hello world"]


def test_chunk_text_creates_overlapping_windows() -> None:
    words = [f"w{i}" for i in range(12)]
    text = " ".join(words)
    result = chunking.chunk_text(text, chunk_size=5, overlap=2)
    # Sliding windows should advance by chunk_size - overlap words
    assert len(result) == 3
    assert result[0].split()[0] == "w0"
    assert result[1].split()[0] == "w3"
    assert result[2].split()[0] == "w6"


def test_chunk_text_validates_overlap_rules() -> None:
    with pytest.raises(ValueError):
        chunking.chunk_text("text", chunk_size=10, overlap=10)


def test_prepare_chunks_includes_metadata_and_counts() -> None:
    meta = {"type": "Doc", "author": "Alex"}
    prepared = chunking.prepare_chunks(
        title="My Doc",
        type_label="PDF",
        body="one two three four five six",
        meta=meta,
        chunk_size=3,
        overlap=1,
    )
    assert len(prepared) == 3
    first_meta = prepared[0]["meta"]
    assert first_meta["source_title"] == "My Doc"
    assert first_meta["type_label"] == "PDF"
    assert first_meta["chunk_index"] == "0"
    assert first_meta["chunk_count"] == "3"
    assert first_meta["author"] == "Alex"
