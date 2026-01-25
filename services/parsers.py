"""Document parsing helpers for ingestion flows."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep
from typing import Iterable, Sequence

from agno.agent import Agent
from agno.media import Image
from agno.knowledge.reader.csv_reader import CSVReader
from agno.knowledge.reader.pptx_reader import PPTXReader
from agno.knowledge.reader.excel_reader import ExcelReader
from agno.models.openai import OpenAIChat
from agno.tools.moviepy_video import MoviePyVideoTools
from agno.tools.openai import OpenAITools
from docx import Document
from pypdf import PdfReader

from services.settings import get_settings

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
    ".md",
    ".csv",
    ".xlsx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".opus",
    ".mp4",
    ".mov",
    ".mkv",
    ".webm",
    ".avi",
}
_TEXT_EXTENSIONS = {".txt", ".md", ".csv"}
_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi"}


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Fallback with replacement characters
    return data.decode("utf-8", errors="replace")


def _extract_pdf(reader: PdfReader) -> str:
    texts: Iterable[str] = []
    buffer: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        buffer.append(extracted.strip())
    return "\n\n".join(buffer).strip()


def _extract_docx(doc: Document) -> str:
    buffer: list[str] = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            buffer.append(paragraph.text.strip())
    return "\n".join(buffer).strip()


def _doc_to_text(doc: object) -> str:
    for attr in ("content", "text", "page_content"):
        value = getattr(doc, attr, None)
        if isinstance(value, str) and value:
            return value
    return ""


def _extract_with_reader(reader: object, data: bytes, suffix: str) -> str:
    with NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        handle.flush()
        path = Path(handle.name)
    try:
        documents: Sequence[object] = reader.read(path)
        return "\n\n".join(text for text in (_doc_to_text(doc) for doc in documents) if text).strip()
    finally:
        _safe_unlink(path)


def _safe_unlink(path: Path, attempts: int = 3, delay: float = 0.2) -> None:
    for attempt in range(attempts):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            if attempt == attempts - 1:
                return
            sleep(delay)


@lru_cache(1)
def _openai_tools() -> OpenAITools | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    return OpenAITools(api_key=settings.openai_api_key)


@lru_cache(1)
def _image_caption_agent() -> Agent | None:
    settings = get_settings()
    if not settings.openai_api_key:
        return None
    model = OpenAIChat(id="gpt-4o-mini", api_key=settings.openai_api_key)
    return Agent(
        name="ImageCaption",
        model=model,
        instructions="Beschreibe den Bildinhalt prägnant in 2-3 Sätzen.",
    )


def _describe_image(data: bytes, filename: str, suffix: str) -> str:
    agent = _image_caption_agent()
    if not agent:
        return f"Bilddatei: {filename}"
    with NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        handle.flush()
        path = Path(handle.name)
    try:
        result = agent.run("Bild beschreiben", images=[Image(filepath=path)])
        text = getattr(result, "content", None) or str(result)
        return text.strip()
    finally:
        _safe_unlink(path)


def _transcribe_audio(data: bytes, filename: str, suffix: str) -> str:
    tools = _openai_tools()
    if not tools:
        return f"Audio-Datei: {filename}"
    with NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        handle.flush()
        path = Path(handle.name)
    try:
        return tools.transcribe_audio(str(path)).strip()
    finally:
        _safe_unlink(path)


def _transcribe_video(data: bytes, filename: str, suffix: str) -> str:
    tools = _openai_tools()
    if not tools:
        return f"Video-Datei: {filename}"
    with NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(data)
        handle.flush()
        video_path = Path(handle.name)
    audio_path = video_path.with_suffix(".wav")
    try:
        video_tools = MoviePyVideoTools(
            enable_process_video=True,
            enable_generate_captions=False,
            enable_embed_captions=False,
        )
        extracted = video_tools.extract_audio(str(video_path), str(audio_path))
        if not audio_path.exists():
            raise ValueError(extracted)
        return tools.transcribe_audio(str(audio_path)).strip()
    finally:
        _safe_unlink(video_path)
        _safe_unlink(audio_path)


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Return plaintext from a binary document payload."""
    suffix = Path(filename).suffix.lower()
    if suffix in _TEXT_EXTENSIONS:
        return _decode_text(data)
    if suffix == ".pdf":
        reader = PdfReader(BytesIO(data))
        return _extract_pdf(reader)
    if suffix == ".docx":
        doc = Document(BytesIO(data))
        return _extract_docx(doc)
    if suffix == ".csv":
        return _extract_with_reader(CSVReader(), data, suffix)
    if suffix == ".xlsx":
        return _extract_with_reader(ExcelReader(), data, suffix)
    if suffix == ".pptx":
        return _extract_with_reader(PPTXReader(), data, suffix)
    if suffix in _IMAGE_EXTENSIONS:
        return _describe_image(data, filename, suffix)
    if suffix in _AUDIO_EXTENSIONS:
        return _transcribe_audio(data, filename, suffix)
    if suffix in _VIDEO_EXTENSIONS:
        return _transcribe_video(data, filename, suffix)
    raise ValueError(f"Unsupported file type: {suffix or filename}")


def extract_text_from_path(path: Path) -> str:
    with path.open("rb") as handle:
        return extract_text_from_bytes(path.name, handle.read())
