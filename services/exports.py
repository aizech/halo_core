"""Placeholder export helpers for Studio artifacts."""

from __future__ import annotations

from datetime import datetime


def render_markdown(title: str, body: str) -> bytes:
    content = f"# {title}\n\n{body}\n\n_Generated {datetime.utcnow().isoformat()}Z_"
    return content.encode("utf-8")


def render_pdf(title: str, body: str) -> bytes:
    pseudo_pdf = (
        "%PDF-1.4\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        f"4 0 obj << /Length {len(body)+len(title)+20} >> stream\n"
        f"{title}\n{body}\n" "endstream endobj\n"
        "xref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000114 00000 n \n0000000210 00000 n \n"
        "trailer << /Size 5 /Root 1 0 R >>\nstartxref\n310\n%%EOF"
    )
    return pseudo_pdf.encode("latin-1", errors="ignore")


def render_slides(title: str, body: str) -> bytes:
    lines = body.split("\n")
    slides = [title]
    chunk = []
    for line in lines:
        if len(chunk) >= 4:
            slides.append(" | ".join(chunk))
            chunk = []
        chunk.append(line or "\u2022")
    if chunk:
        slides.append(" | ".join(chunk))
    csv_content = "slide_title,content\n" + "\n".join(
        f"Slide {idx},{content}" for idx, content in enumerate(slides, start=1)
    )
    return csv_content.encode("utf-8")
