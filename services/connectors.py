"""System API connector abstractions (mock implementations for MVP)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from services import storage


@dataclass
class ConnectorResult:
    title: str
    type_label: str
    meta: str
    description: str = ""


class Connector(Protocol):
    name: str

    def fetch_sources(self) -> List[ConnectorResult]: ...


class GoogleDriveConnector:
    name = "Google Drive"

    def fetch_sources(self) -> List[ConnectorResult]:
        return [
            ConnectorResult(
                title="Drive: Projektplan NotebookLM",
                type_label="Doc",
                meta="Drive • Aktualisiert heute",
                description="Projektbriefing mit Deliverables",
            ),
            ConnectorResult(
                title="Drive: Multimedia Assets",
                type_label="Folder",
                meta="Drive • 12 Dateien",
            ),
        ]


class NotionConnector:
    name = "Notion"

    def fetch_sources(self) -> List[ConnectorResult]:
        return [
            ConnectorResult(
                title="Notion: Wissensdatenbank",
                type_label="Page",
                meta="Notion • 24 Blocks",
                description="Sammlung aller Projektentscheidungen",
            ),
            ConnectorResult(
                title="Notion: FAQ",
                type_label="Page",
                meta="Notion • Aktualisiert gestern",
            ),
        ]


AVAILABLE_CONNECTORS: Dict[str, Connector] = {
    "drive": GoogleDriveConnector(),
    "notion": NotionConnector(),
}


def _deserialize(entry: Dict[str, List[Dict[str, str]]]) -> List[ConnectorResult]:
    return [ConnectorResult(**item) for item in entry.get("items", [])]


def collect_connector_results(
    slugs: List[str], refresh: bool = False
) -> List[ConnectorResult]:
    cache = storage.load_connector_cache()
    results: List[ConnectorResult] = []
    cache_updated = False
    for slug in slugs:
        connector = AVAILABLE_CONNECTORS.get(slug)
        if not connector:
            continue
        cached_entry = cache.get(slug)
        if cached_entry and not refresh:
            results.extend(_deserialize(cached_entry))
            continue
        fetched = connector.fetch_sources()
        cache[slug] = {"items": [result.__dict__ for result in fetched]}
        results.extend(fetched)
        cache_updated = True
    if cache_updated:
        storage.save_connector_cache(cache)
    return results
