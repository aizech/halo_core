"""Ingestion connectors for web search and content scraping."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from services import chunking, parsers, retrieval

_LOGGER = logging.getLogger(__name__)

DocumentPayload = Dict[str, str]

_last_search_time: float = 0
MIN_SEARCH_INTERVAL: float = 1.0


def _rate_limit_search() -> None:
    """Apply rate limiting to prevent DuckDuckGo rate limits."""
    global _last_search_time
    elapsed = time.time() - _last_search_time
    if elapsed < MIN_SEARCH_INTERVAL:
        time.sleep(MIN_SEARCH_INTERVAL - elapsed)
    _last_search_time = time.time()


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Search the web using DuckDuckGo and return formatted results.

    Args:
        query: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of dicts with keys: title, type, meta, description, url
    """
    if not query or not query.strip():
        return []

    try:
        from ddgs import DDGS
    except ImportError:
        _LOGGER.warning("ddgs not installed, returning empty results")
        return []

    results: List[Dict[str, str]] = []
    try:
        _rate_limit_search()
        ddgs = DDGS()
        search_results = ddgs.text(query, max_results=max_results)
        if search_results:
            for item in search_results:
                results.append(
                    {
                        "title": item.get("title", "Untitled"),
                        "type": "Web",
                        "meta": f"Web • {datetime.now():%d.%m.%Y}",
                        "description": item.get("body", "")[:300],
                        "url": item.get("href", ""),
                    }
                )
    except Exception as e:
        _LOGGER.error("DuckDuckGo search failed: %s", e)

    return results


def scrape_web_content(url: str, max_retries: int = 3) -> Dict[str, str]:
    """Scrape content from a URL using WebsiteTools with retry logic.

    Args:
        url: URL to scrape
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Dict with keys: title, body, source_url, or empty dict on failure
    """
    if not url or not url.strip():
        return {}

    try:
        from agno.tools.website import WebsiteTools
    except ImportError:
        _LOGGER.warning("agno.tools.website not available")
        return {}

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            tools = WebsiteTools()
            content = tools.read(url)

            if content:
                return {
                    "title": url.split("/")[-1] or url,
                    "body": content,
                    "source_url": url,
                }
            if attempt == 0:
                _LOGGER.warning(
                    "Web scraping returned empty content for %s (no retries needed)",
                    url,
                )
            return {}
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                _LOGGER.warning(
                    "Web scraping attempt %d/%d failed for %s: %s",
                    attempt + 1,
                    max_retries,
                    url,
                    e,
                )

    _LOGGER.error(
        "Web scraping failed for %s after %d attempts: %s",
        url,
        max_retries,
        last_error,
    )
    return {}


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
