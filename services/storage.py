"""Local JSON storage helpers for the MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from services.settings import get_settings

_SETTINGS = get_settings()
_DATA_DIR = Path(_SETTINGS.data_dir)
_SOURCES_FILE = _DATA_DIR / "sources.json"
_NOTES_FILE = _DATA_DIR / "studio_notes.json"
_CONFIG_FILE = _DATA_DIR / "config.json"
_CONNECTOR_CACHE_FILE = _DATA_DIR / "connector_cache.json"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_sources() -> List[Dict[str, str]]:
    _ensure_data_dir()
    if not _SOURCES_FILE.exists():
        return []
    with _SOURCES_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_sources(sources: List[Dict[str, str]]) -> None:
    _ensure_data_dir()
    with _SOURCES_FILE.open("w", encoding="utf-8") as handle:
        json.dump(sources, handle, ensure_ascii=False, indent=2)


def load_notes() -> List[Dict[str, str]]:
    _ensure_data_dir()
    if not _NOTES_FILE.exists():
        return []
    with _NOTES_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_notes(notes: List[Dict[str, str]]) -> None:
    _ensure_data_dir()
    with _NOTES_FILE.open("w", encoding="utf-8") as handle:
        json.dump(notes, handle, ensure_ascii=False, indent=2)


def load_config() -> Dict[str, List[str]]:
    _ensure_data_dir()
    if not _CONFIG_FILE.exists():
        return {}
    with _CONFIG_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_config(config: Dict[str, List[str]]) -> None:
    _ensure_data_dir()
    with _CONFIG_FILE.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, ensure_ascii=False, indent=2)


def load_connector_cache() -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    _ensure_data_dir()
    if not _CONNECTOR_CACHE_FILE.exists():
        return {}
    with _CONNECTOR_CACHE_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_connector_cache(cache: Dict[str, Dict[str, List[Dict[str, str]]]]) -> None:
    _ensure_data_dir()
    with _CONNECTOR_CACHE_FILE.open("w", encoding="utf-8") as handle:
        json.dump(cache, handle, ensure_ascii=False, indent=2)
