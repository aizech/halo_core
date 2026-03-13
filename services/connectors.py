"""System API connector abstractions with MCP-based implementations."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

from services import storage

_logger = logging.getLogger(__name__)


@dataclass
class ConnectorResult:
    title: str
    type_label: str
    meta: str
    description: str = ""
    source_id: Optional[str] = None  # Unique ID for tracking
    connector_slug: str = ""  # Which connector provided this


@dataclass
class ConnectorConfig:
    """Configuration for a connector instance."""

    slug: str
    name: str
    description: str = ""
    env_vars: List[str] = field(default_factory=list)
    mcp_server_name: Optional[str] = None  # Maps to MCP server config


class Connector(Protocol):
    name: str
    slug: str
    description: str

    def is_configured(self) -> bool:
        """Check if required environment variables are set."""
        ...

    def fetch_sources(self) -> List[ConnectorResult]:
        """Fetch available sources from the connector."""
        ...


class BaseMCPConnector:
    """Base class for MCP-based connectors with common functionality."""

    slug: str = ""
    name: str = ""
    description: str = ""
    env_vars: List[str] = field(default_factory=list)
    mcp_server_name: Optional[str] = None

    def is_configured(self) -> bool:
        """Check if required environment variables are set."""
        for var in self.env_vars:
            if not os.environ.get(var):
                return False
        return True

    def _get_mcp_tools(self) -> Optional[Any]:
        """Get MCP tools instance for this connector.

        Returns None if MCP integration is not available or not configured.
        """
        if not self.is_configured():
            return None

        try:
            # MCP tools are configured via agents_config, not directly here
            # This is a placeholder for future direct MCP tool access
            return None
        except ImportError:
            _logger.debug("MCPTools not available for %s", self.name)
            return None

    def fetch_sources(self) -> List[ConnectorResult]:
        """Fetch sources - override in subclasses."""
        if not self.is_configured():
            _logger.info(
                "Connector %s not configured (missing env vars: %s)",
                self.name,
                self.env_vars,
            )
            return self._get_placeholder_results()
        return self._fetch_from_mcp()

    def _fetch_from_mcp(self) -> List[ConnectorResult]:
        """Override in subclasses to fetch from actual MCP server."""
        return []

    def _get_placeholder_results(self) -> List[ConnectorResult]:
        """Return placeholder results when not configured."""
        return [
            ConnectorResult(
                title=f"{self.name}: Nicht konfiguriert",
                type_label="Config",
                meta=f"{self.name} • Setup erforderlich",
                description=f"Setze die Umgebungsvariablen: {', '.join(self.env_vars)}",
                connector_slug=self.slug,
            )
        ]


class NotionConnector(BaseMCPConnector):
    """Notion workspace connector via official Notion MCP server."""

    slug = "notion"
    name = "Notion"
    description = "Notion workspace integration via official Notion MCP server"
    env_vars = ["NOTION_API_KEY"]
    mcp_server_name = "notion"

    def _fetch_from_mcp(self) -> List[ConnectorResult]:
        """Fetch pages and databases from Notion.

        When MCP is configured, this would call the Notion MCP tools.
        For now, returns a hint that MCP integration is active.
        """
        # Placeholder until MCP tools are callable directly
        return [
            ConnectorResult(
                title="Notion: MCP aktiviert",
                type_label="Config",
                meta="Notion • Bereit für Sync",
                description="Aktiviere den Notion MCP-Server in der Agent-Konfiguration für den Zugriff.",
                connector_slug=self.slug,
            )
        ]


class GoogleDriveConnector(BaseMCPConnector):
    """Google Drive connector via MCP server."""

    slug = "drive"
    name = "Google Drive"
    description = "Google Drive integration via MCP server"
    env_vars = ["GOOGLE_OAUTH_CREDENTIALS"]
    mcp_server_name = "google-drive"

    def _fetch_from_mcp(self) -> List[ConnectorResult]:
        """Fetch files and folders from Google Drive."""
        return [
            ConnectorResult(
                title="Google Drive: MCP aktiviert",
                type_label="Config",
                meta="Drive • Bereit für Sync",
                description="Aktiviere den Google Drive MCP-Server in der Agent-Konfiguration.",
                connector_slug=self.slug,
            )
        ]


class OneDriveConnector(BaseMCPConnector):
    """OneDrive/SharePoint connector via Microsoft MCP server."""

    slug = "onedrive"
    name = "OneDrive"
    description = "OneDrive/SharePoint integration via Microsoft MCP server"
    env_vars = ["MSAL_TENANT_ID", "MSAL_CLIENT_ID", "MSAL_CLIENT_SECRET"]
    mcp_server_name = "onedrive"

    def _fetch_from_mcp(self) -> List[ConnectorResult]:
        """Fetch files and folders from OneDrive."""
        return [
            ConnectorResult(
                title="OneDrive: MCP aktiviert",
                type_label="Config",
                meta="OneDrive • Bereit für Sync",
                description="Aktiviere den OneDrive MCP-Server in der Agent-Konfiguration.",
                connector_slug=self.slug,
            )
        ]


class DicomPacsConnector(BaseMCPConnector):
    """DICOM PACS connector for medical imaging."""

    slug = "dicom-pacs"
    name = "DICOM PACS"
    description = "DICOM PACS server integration for medical imaging"
    env_vars = ["DICOM_PACS_HOST", "DICOM_PACS_PORT", "DICOM_PACS_AE_TITLE"]
    mcp_server_name = "dicom-pacs"

    def _fetch_from_mcp(self) -> List[ConnectorResult]:
        """Fetch studies and series from DICOM PACS."""
        return [
            ConnectorResult(
                title="DICOM PACS: MCP aktiviert",
                type_label="Config",
                meta="PACS • Bereit für Query",
                description="Aktiviere den DICOM MCP-Server für Zugriff auf medizinische Bilddaten.",
                connector_slug=self.slug,
            )
        ]


# Instantiate all available connectors
_notion = NotionConnector()
_drive = GoogleDriveConnector()
_onedrive = OneDriveConnector()
_dicom = DicomPacsConnector()

AVAILABLE_CONNECTORS: Dict[str, Connector] = {
    _notion.slug: _notion,
    _drive.slug: _drive,
    _onedrive.slug: _onedrive,
    _dicom.slug: _dicom,
}


def get_connector_status() -> Dict[str, Dict[str, Any]]:
    """Get configuration status for all connectors.

    Returns dict mapping slug to status info including name, configured, env_vars.
    """
    status: Dict[str, Dict[str, Any]] = {}
    for slug, connector in AVAILABLE_CONNECTORS.items():
        missing_vars = [var for var in connector.env_vars if not os.environ.get(var)]
        status[slug] = {
            "name": connector.name,
            "description": connector.description,
            "configured": connector.is_configured(),
            "missing_env_vars": missing_vars,
        }
    return status


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
