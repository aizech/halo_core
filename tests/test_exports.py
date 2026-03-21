"""Tests for services/exports.py — artifact rendering helpers."""

from __future__ import annotations

from services.exports import render_markdown, render_pdf, render_slides

# ── render_markdown ────────────────────────────────────────────────────────────


def test_render_markdown_returns_bytes() -> None:
    result = render_markdown("My Title", "Body text here.")
    assert isinstance(result, bytes)


def test_render_markdown_contains_title() -> None:
    result = render_markdown("Report", "Some content").decode("utf-8")
    assert "# Report" in result


def test_render_markdown_contains_body() -> None:
    result = render_markdown("T", "The quick brown fox").decode("utf-8")
    assert "The quick brown fox" in result


def test_render_markdown_contains_generated_timestamp() -> None:
    result = render_markdown("T", "body").decode("utf-8")
    assert "_Generated" in result


def test_render_markdown_empty_body() -> None:
    result = render_markdown("Title", "").decode("utf-8")
    assert "# Title" in result


# ── render_pdf ────────────────────────────────────────────────────────────────


def test_render_pdf_returns_bytes() -> None:
    result = render_pdf("Doc", "Content")
    assert isinstance(result, bytes)


def test_render_pdf_starts_with_pdf_header() -> None:
    result = render_pdf("Doc", "Content")
    assert result.startswith(b"%PDF")


def test_render_pdf_contains_title_text() -> None:
    result = render_pdf("MyTitle", "body").decode("latin-1", errors="ignore")
    assert "MyTitle" in result


def test_render_pdf_contains_body_text() -> None:
    result = render_pdf("T", "body content").decode("latin-1", errors="ignore")
    assert "body content" in result


def test_render_pdf_empty_inputs() -> None:
    result = render_pdf("", "")
    assert isinstance(result, bytes)
    assert len(result) > 0


# ── render_slides ─────────────────────────────────────────────────────────────


def test_render_slides_returns_bytes() -> None:
    result = render_slides("Presentation", "Line one\nLine two\nLine three")
    assert isinstance(result, bytes)


def test_render_slides_is_valid_csv() -> None:
    result = render_slides("Deck", "a\nb\nc").decode("utf-8")
    assert "slide_title,content" in result


def test_render_slides_title_becomes_first_slide() -> None:
    result = render_slides("My Deck", "line").decode("utf-8")
    assert "My Deck" in result


def test_render_slides_chunks_at_four_lines() -> None:
    body = "\n".join(f"line{i}" for i in range(10))
    result = render_slides("T", body).decode("utf-8")
    lines = [ln for ln in result.splitlines() if ln.startswith("Slide")]
    assert len(lines) >= 2


def test_render_slides_empty_body() -> None:
    result = render_slides("T", "").decode("utf-8")
    assert "slide_title,content" in result
