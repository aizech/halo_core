"""Mock ingestion connectors for MVP workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from services import chunking, parsers, retrieval

DocumentPayload = Dict[str, str]


_SAMPLE_WEB_RESULTS = [
    {
        "title": "Notion AI Tutorial",
        "type": "Web",
        "meta": "Web • Vor 2 Tagen",
        "description": "Anleitung zur Nutzung von Notion AI für Wissensarbeit.",
    },
    {
        "title": "OpenAI DevDay Recap",
        "type": "Blog",
        "meta": "Blog • Vor 1 Woche",
        "description": "Zusammenfassung aller DevDay Ankündigungen.",
    },
    {
        "title": "Streamlit Components Guide",
        "type": "Doc",
        "meta": "Dokument • Vor 3 Wochen",
        "description": "Best Practices zum Bau komplexer Layouts.",
    },
]


def search_web(query: str) -> List[Dict[str, str]]:
    """Return mock search results – replace with MCP/System API call later."""
    if not query:
        return []
    lowered = query.lower()
    return [
        item for item in _SAMPLE_WEB_RESULTS if lowered in item["title"].lower()
    ] or _SAMPLE_WEB_RESULTS


def ingest_source_content(title: str, body: str, meta: Dict[str, str]) -> None:
    """Store normalized chunks in LanceDB so RAG can retrieve them later."""
    prepared_chunks = chunking.prepare_chunks(
        title=title,
        type_label=meta.get("type", meta.get("type_label", "Unknown")),
        body=body,
        meta=meta,
    )
    for chunk in prepared_chunks:
        retrieval.index_source_text(title, chunk["text"], chunk["meta"])


def infer_type_label(filename: str, data: bytes | None = None) -> str:
    """Infer type label from filename extension or content.

    If data is provided, also checks for DICOM magic bytes for files
    without recognized extension.
    """
    suffix = Path(filename).suffix.lower()
    type_label = {
        ".pdf": "PDF",
        ".docx": "Doc",
        ".txt": "Text",
        ".md": "Markdown",
        ".csv": "CSV",
        ".xlsx": "Excel",
        ".pptx": "PowerPoint",
        ".png": "Bild",
        ".jpg": "Bild",
        ".jpeg": "Bild",
        ".webp": "Bild",
        ".gif": "Bild",
        ".mp3": "Audio",
        ".wav": "Audio",
        ".m4a": "Audio",
        ".aac": "Audio",
        ".flac": "Audio",
        ".ogg": "Audio",
        ".opus": "Audio",
        ".mp4": "Video",
        ".mov": "Video",
        ".mkv": "Video",
        ".webm": "Video",
        ".avi": "Video",
        ".dcm": "DICOM",
        ".dicom": "DICOM",
    }.get(suffix)

    if type_label:
        return type_label

    # Check for DICOM by magic bytes if no extension match
    if data and parsers.is_dicom_file(data):
        return "DICOM"

    return "Doc"


def extract_document_payload(filename: str, data: bytes) -> DocumentPayload:
    """Return title/type/body for a single uploaded document."""
    text = parsers.extract_text_from_bytes(filename, data)
    type_label = infer_type_label(filename, data)
    return {
        "title": filename,
        "type_label": type_label,
        "body": text,
    }


def load_directory_documents(directory: Path) -> List[DocumentPayload]:
    """Collect supported files from a directory (recursively).

    Also detects DICOM files by magic bytes even without extension.
    """
    if not directory.exists():
        raise FileNotFoundError(directory)
    if not directory.is_dir():
        raise NotADirectoryError(directory)

    documents: List[DocumentPayload] = []
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()

        # Check if extension is supported
        ext_supported = suffix in parsers.SUPPORTED_EXTENSIONS

        # For files without recognized extension, check content
        if not ext_supported:
            try:
                with path.open("rb") as f:
                    header = f.read(132)  # DICOM preamble + magic
                    if not parsers.is_dicom_file(header):
                        continue
            except Exception:
                continue

        # Skip media files (handled differently)
        if suffix in (
            parsers._IMAGE_EXTENSIONS
            | parsers._AUDIO_EXTENSIONS
            | parsers._VIDEO_EXTENSIONS
        ):
            continue

        body = parsers.extract_text_from_path(path)
        documents.append(
            {
                "title": path.name,
                "type_label": infer_type_label(path.name),
                "body": body,
                "source_path": str(path),
            }
        )
    if not documents:
        raise ValueError(f"No supported documents found in {directory}")
    return documents
