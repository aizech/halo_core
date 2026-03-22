"""Tests for ingestion parsing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from services import ingestion


def test_extract_document_payload_text() -> None:
    data = b"Hello HALO Core"
    payload = ingestion.extract_document_payload("note.txt", data)
    assert payload["title"] == "note.txt"
    assert payload["type_label"] == "Text"
    assert "HALO Core" in payload["body"]


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


def test_dicom_magic_byte_detected_without_dcm_extension(tmp_path: Path) -> None:
    from services import parsers

    dicom_header = b"\x00" * 128 + b"DICM"
    no_ext_file = tmp_path / "mystery_file"
    no_ext_file.write_bytes(dicom_header + b"\x00" * 256)

    assert parsers.is_dicom_file(dicom_header) is True


def test_non_dicom_magic_bytes_rejected() -> None:
    from services import parsers

    pdf_header = b"%PDF-1.4" + b"\x00" * 124
    assert parsers.is_dicom_file(pdf_header) is False


def test_dicom_magic_too_short() -> None:
    from services import parsers

    short = b"\x00" * 64
    assert parsers.is_dicom_file(short) is False
