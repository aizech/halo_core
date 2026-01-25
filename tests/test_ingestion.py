"""Tests for ingestion parsing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import ingestion


def test_extract_document_payload_text() -> None:
    data = b"Hello NotebookLM"
    payload = ingestion.extract_document_payload("note.txt", data)
    assert payload["title"] == "note.txt"
    assert payload["type_label"] == "Text"
    assert "NotebookLM" in payload["body"]


def test_load_directory_documents_reads_supported_files(tmp_path: Path) -> None:
    valid = tmp_path / "summary.txt"
    valid.write_text("Chunk me", encoding="utf-8")
    ignored = tmp_path / "image.png"
    ignored.write_bytes(b"binary")

    docs = ingestion.load_directory_documents(tmp_path)
    assert len(docs) == 1
    doc = docs[0]
    assert doc["title"] == "summary.txt"
    assert doc["body"] == "Chunk me"
    assert doc["type_label"] == "Text"


def test_load_directory_documents_raises_when_empty(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        ingestion.load_directory_documents(tmp_path)
