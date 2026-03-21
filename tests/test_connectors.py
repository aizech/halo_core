"""Tests for services/connectors.py."""

from __future__ import annotations

from unittest.mock import patch

from services.connectors import (
    AVAILABLE_CONNECTORS,
    ConnectorResult,
    NotionConnector,
    GoogleDriveConnector,
    OneDriveConnector,
    DicomPacsConnector,
    get_connector_status,
    collect_connector_results,
)


def test_available_connectors_has_expected_slugs() -> None:
    assert "notion" in AVAILABLE_CONNECTORS
    assert "drive" in AVAILABLE_CONNECTORS
    assert "onedrive" in AVAILABLE_CONNECTORS
    assert "dicom-pacs" in AVAILABLE_CONNECTORS


def test_connector_result_fields() -> None:
    result = ConnectorResult(
        title="Test",
        type_label="Doc",
        meta="meta info",
        description="desc",
        source_id="src-1",
        connector_slug="notion",
    )
    assert result.title == "Test"
    assert result.connector_slug == "notion"


def test_notion_connector_not_configured_without_env(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    c = NotionConnector()
    assert c.is_configured() is False


def test_notion_connector_configured_with_env(monkeypatch) -> None:
    monkeypatch.setenv("NOTION_API_KEY", "test-token")
    c = NotionConnector()
    assert c.is_configured() is True


def test_google_drive_connector_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_OAUTH_CREDENTIALS", raising=False)
    c = GoogleDriveConnector()
    assert c.is_configured() is False


def test_onedrive_connector_not_configured(monkeypatch) -> None:
    for var in ["MSAL_TENANT_ID", "MSAL_CLIENT_ID", "MSAL_CLIENT_SECRET"]:
        monkeypatch.delenv(var, raising=False)
    c = OneDriveConnector()
    assert c.is_configured() is False


def test_dicom_pacs_connector_not_configured(monkeypatch) -> None:
    for var in ["DICOM_PACS_HOST", "DICOM_PACS_PORT", "DICOM_PACS_AE_TITLE"]:
        monkeypatch.delenv(var, raising=False)
    c = DicomPacsConnector()
    assert c.is_configured() is False


def test_fetch_sources_returns_placeholder_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    c = NotionConnector()
    results = c.fetch_sources()
    assert len(results) == 1
    assert "Nicht konfiguriert" in results[0].title
    assert results[0].connector_slug == "notion"


def test_get_connector_status_all_slugs_present() -> None:
    status = get_connector_status()
    for slug in ("notion", "drive", "onedrive", "dicom-pacs"):
        assert slug in status
        assert "name" in status[slug]
        assert "configured" in status[slug]
        assert "missing_env_vars" in status[slug]


def test_get_connector_status_test_mode_configured() -> None:
    status = get_connector_status(
        test_mode=True,
        test_credentials={"notion": "fake-key"},
    )
    assert status["notion"]["configured"] is True


def test_get_connector_status_test_mode_missing() -> None:
    status = get_connector_status(
        test_mode=True,
        test_credentials={"notion": ""},
    )
    assert status["notion"]["configured"] is False


def test_collect_connector_results_skips_unknown_slug() -> None:
    with patch("services.connectors.storage") as mock_storage:
        mock_storage.load_connector_cache.return_value = {}
        mock_storage.save_connector_cache.return_value = None
        results = collect_connector_results(["nonexistent-slug"])
    assert results == []


def test_collect_connector_results_uses_cache(monkeypatch) -> None:
    cached_item = {
        "title": "Cached",
        "type_label": "Doc",
        "meta": "m",
        "description": "",
        "source_id": None,
        "connector_slug": "notion",
    }
    with patch("services.connectors.storage") as mock_storage:
        mock_storage.load_connector_cache.return_value = {
            "notion": {"items": [cached_item]}
        }
        mock_storage.save_connector_cache.return_value = None
        results = collect_connector_results(["notion"])
    assert len(results) == 1
    assert results[0].title == "Cached"
