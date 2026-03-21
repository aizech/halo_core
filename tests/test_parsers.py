"""Tests for services/parsers.py — document text extraction helpers."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest

from services.parsers import (
    SUPPORTED_EXTENSIONS,
    _decode_text,
    _doc_to_text,
    extract_text_from_bytes,
    is_dicom_file,
)

# ── helpers ────────────────────────────────────────────────────────────────────


def _make_dicom_bytes(payload: bytes = b"") -> bytes:
    """Return minimal DICOM bytes: 128-byte preamble + 'DICM' magic."""
    return b"\x00" * 128 + b"DICM" + payload


# ── SUPPORTED_EXTENSIONS ──────────────────────────────────────────────────────


def test_supported_extensions_includes_common_types() -> None:
    for ext in (".pdf", ".docx", ".txt", ".csv", ".xlsx", ".pptx", ".png", ".mp3"):
        assert ext in SUPPORTED_EXTENSIONS


def test_supported_extensions_includes_dicom() -> None:
    assert ".dcm" in SUPPORTED_EXTENSIONS
    assert ".dicom" in SUPPORTED_EXTENSIONS


# ── _decode_text ───────────────────────────────────────────────────────────────


def test_decode_text_utf8() -> None:
    data = "Hallo Welt".encode("utf-8")
    assert _decode_text(data) == "Hallo Welt"


def test_decode_text_latin1() -> None:
    data = "Sch\xf6n".encode("latin-1")
    result = _decode_text(data)
    assert "Sch" in result


# ── _doc_to_text ───────────────────────────────────────────────────────────────


def test_doc_to_text_reads_content_attr() -> None:
    doc = MagicMock()
    doc.content = "hello from content"
    doc.text = None
    assert _doc_to_text(doc) == "hello from content"


def test_doc_to_text_falls_back_to_text_attr() -> None:
    doc = MagicMock()
    doc.content = ""
    doc.text = "hello from text"
    assert _doc_to_text(doc) == "hello from text"


def test_doc_to_text_returns_empty_when_no_attrs() -> None:
    doc = MagicMock()
    doc.content = ""
    doc.text = ""
    doc.page_content = ""
    assert _doc_to_text(doc) == ""


# ── is_dicom_file ──────────────────────────────────────────────────────────────


def test_is_dicom_file_returns_true_for_valid_magic() -> None:
    data = _make_dicom_bytes()
    assert is_dicom_file(data) is True


def test_is_dicom_file_returns_false_for_short_data() -> None:
    assert is_dicom_file(b"\x00" * 10) is False


def test_is_dicom_file_returns_false_for_non_dicom() -> None:
    data = b"\x00" * 128 + b"NOPE" + b"\x00" * 10
    assert is_dicom_file(data) is False


# ── extract_text_from_bytes — plain text ─────────────────────────────────────


def test_extract_text_from_bytes_txt() -> None:
    data = b"Hello World"
    result = extract_text_from_bytes("file.txt", data)
    assert result == "Hello World"


def test_extract_text_from_bytes_md() -> None:
    data = b"# Heading\n\nParagraph."
    result = extract_text_from_bytes("notes.md", data)
    assert "Heading" in result


# ── extract_text_from_bytes — PDF ─────────────────────────────────────────────


def test_extract_text_from_bytes_pdf(tmp_path) -> None:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()
    result = extract_text_from_bytes("test.pdf", pdf_bytes)
    assert isinstance(result, str)


# ── extract_text_from_bytes — unsupported ────────────────────────────────────


def test_extract_text_from_bytes_raises_for_unknown_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text_from_bytes("file.xyz", b"some data")


# ── extract_text_from_bytes — DICOM (no pydicom) ─────────────────────────────


def test_extract_text_from_bytes_dicom_no_pydicom() -> None:
    data = _make_dicom_bytes()
    with patch("services.parsers._extract_dicom_metadata") as mock_extract:
        mock_extract.return_value = "DICOM: test.dcm"
        result = extract_text_from_bytes("test.dcm", data)
    assert result == "DICOM: test.dcm"


def test_extract_text_from_bytes_dicom_by_magic_not_extension() -> None:
    """A file with .txt extension but DICOM magic bytes should be treated as DICOM."""
    data = _make_dicom_bytes()
    with patch("services.parsers._extract_dicom_metadata") as mock_extract:
        mock_extract.return_value = "DICOM: sneaky.txt"
        result = extract_text_from_bytes("sneaky.txt", data)
    assert result == "DICOM: sneaky.txt"


# ── extract_text_from_bytes — image fallback (no API key) ────────────────────


def test_extract_text_from_bytes_image_no_api_key() -> None:
    with patch("services.parsers._image_caption_agent", return_value=None):
        result = extract_text_from_bytes("photo.png", b"\x89PNG\r\n")
    assert "photo.png" in result


# ── extract_text_from_bytes — audio fallback (no API key) ────────────────────


def test_extract_text_from_bytes_audio_no_api_key() -> None:
    with patch("services.parsers._openai_tools", return_value=None):
        result = extract_text_from_bytes("clip.mp3", b"ID3")
    assert "clip.mp3" in result
