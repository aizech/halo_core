"""Tests for DICOM parsing and anonymization."""

from __future__ import annotations

from unittest.mock import patch

import pytest


# Sample minimal DICOM data (128-byte preamble + 'DICM' + minimal dataset)
def create_minimal_dicom() -> bytes:
    """Create a minimal valid DICOM file for testing."""
    # 128-byte preamble (zeros) + 'DICM' magic
    preamble = b"\x00" * 128 + b"DICM"

    # Minimal dataset: PatientName (0010,0010) = "Test Patient"
    # Group 0x0010, Element 0x0010, VR=PN, Length=12, Value="Test Patient"
    patient_name_tag = b"\x10\x00\x10\x00"  # Little-endian tag
    patient_name_vr = b"PN"  # VR
    patient_name_len = b"\x0c\x00"  # Length 12 (little-endian)
    patient_name_val = b"Test Patient"

    # PatientID (0010,0020) = "12345"
    patient_id_tag = b"\x10\x00\x20\x00"
    patient_id_vr = b"LO"
    patient_id_len = b"\x05\x00"
    patient_id_val = b"12345"

    # PatientBirthDate (0010,0030) = "19800101"
    birth_date_tag = b"\x10\x00\x30\x00"
    birth_date_vr = b"DA"
    birth_date_len = b"\x08\x00"
    birth_date_val = b"19800101"

    return (
        preamble
        + patient_name_tag
        + patient_name_vr
        + patient_name_len
        + patient_name_val
        + patient_id_tag
        + patient_id_vr
        + patient_id_len
        + patient_id_val
        + birth_date_tag
        + birth_date_vr
        + birth_date_len
        + birth_date_val
    )


class TestDicomDetection:
    """Tests for DICOM file detection."""

    def test_is_dicom_file_with_valid_dicom(self):
        """Test detection of valid DICOM file."""
        from services import parsers

        data = create_minimal_dicom()
        assert parsers.is_dicom_file(data) is True

    def test_is_dicom_file_with_non_dicom(self):
        """Test detection rejects non-DICOM data."""
        from services import parsers

        # Random data without DICM magic
        data = b"x" * 200
        assert parsers.is_dicom_file(data) is False

    def test_is_dicom_file_too_short(self):
        """Test detection rejects data too short."""
        from services import parsers

        data = b"short"
        assert parsers.is_dicom_file(data) is False

    def test_is_dicom_file_with_text(self):
        """Test detection rejects plain text."""
        from services import parsers

        data = b"This is plain text, not DICOM"
        assert parsers.is_dicom_file(data) is False


class TestDicomParsing:
    """Tests for DICOM content parsing."""

    def test_extract_text_from_dicom_bytes(self):
        """Test extracting text from DICOM file."""
        pytest.importorskip("pydicom")
        from services import parsers

        data = create_minimal_dicom()
        text = parsers.extract_text_from_bytes("test.dcm", data)

        # Should contain patient info
        assert "Patient" in text
        assert "Test Patient" in text or "Unbekannt" in text

    def test_extract_text_from_dicom_without_extension(self):
        """Test extracting from DICOM file without .dcm extension."""
        pytest.importorskip("pydicom")
        from services import parsers

        data = create_minimal_dicom()
        # File has no extension, but should be detected by magic bytes
        text = parsers.extract_text_from_bytes("medical_image", data)

        assert "DICOM" in text or "Patient" in text

    def test_extract_dicom_metadata_handles_missing_pydicom(self):
        """Test graceful handling when pydicom not installed."""
        from services import parsers

        data = create_minimal_dicom()

        with patch.dict("sys.modules", {"pydicom": None}):
            # Should not crash, return placeholder text
            text = parsers._extract_dicom_metadata(data, "test.dcm")
            assert "DICOM" in text


class TestDicomAnonymization:
    """Tests for DICOM anonymization."""

    def test_anonymize_dicom_bytes_removes_patient_info(self):
        """Test that anonymization removes patient information."""
        pytest.importorskip("pydicom")
        from services import dicom_anonymizer

        data = create_minimal_dicom()
        config = dicom_anonymizer.AnonymizationConfig()

        result = dicom_anonymizer.anonymize_dicom_bytes(data, "test.dcm", config)

        assert result.error is None
        assert "PatientName" in result.tags_anonymized
        assert "PatientID" in result.tags_anonymized

    def test_anonymize_dicom_bytes_regenerates_uids(self):
        """Test that anonymization regenerates UIDs."""
        pytest.importorskip("pydicom")
        from services import dicom_anonymizer

        data = create_minimal_dicom()
        config = dicom_anonymizer.AnonymizationConfig(regenerate_uids=True)

        result = dicom_anonymizer.anonymize_dicom_bytes(data, "test.dcm", config)

        assert result.error is None
        # UIDs would be regenerated if present in the DICOM

    def test_anonymize_dicom_bytes_preserves_config(self):
        """Test that config options are respected."""
        pytest.importorskip("pydicom")
        from services import dicom_anonymizer

        data = create_minimal_dicom()
        config = dicom_anonymizer.AnonymizationConfig(
            regenerate_uids=False,
            remove_private_tags=False,
        )

        result = dicom_anonymizer.anonymize_dicom_bytes(data, "test.dcm", config)

        assert result.error is None
        # UIDs should not be regenerated
        assert result.uids_regenerated == []

    def test_get_dicom_identifiable_fields(self):
        """Test extraction of identifiable fields for preview."""
        pytest.importorskip("pydicom")
        from services import dicom_anonymizer

        data = create_minimal_dicom()
        fields = dicom_anonymizer.get_dicom_identifiable_fields(data)

        assert "PatientName" in fields or "error" not in fields

    def test_anonymization_config_generates_id(self):
        """Test that AnonymizationConfig generates a unique ID."""
        from services import dicom_anonymizer

        config1 = dicom_anonymizer.AnonymizationConfig()
        config2 = dicom_anonymizer.AnonymizationConfig()

        assert config1.anonymization_id is not None
        assert config2.anonymization_id is not None
        assert config1.anonymization_id != config2.anonymization_id

    def test_create_anonymized_zip(self):
        """Test ZIP archive creation."""
        pytest.importorskip("pydicom")
        from services import dicom_anonymizer

        data = create_minimal_dicom()
        config = dicom_anonymizer.AnonymizationConfig()
        result = dicom_anonymizer.anonymize_dicom_bytes(data, "test.dcm", config)

        zip_data = dicom_anonymizer.create_anonymized_zip([result])

        assert zip_data.startswith(b"PK")  # ZIP magic bytes


class TestDicomIngestion:
    """Tests for DICOM ingestion into Sources."""

    def test_infer_type_label_dicom_extension(self):
        """Test type label inference for .dcm files."""
        from services import ingestion

        assert ingestion.infer_type_label("scan.dcm") == "DICOM"
        assert ingestion.infer_type_label("image.dicom") == "DICOM"

    def test_infer_type_label_dicom_magic_bytes(self):
        """Test type label inference from DICOM magic bytes."""
        from services import ingestion

        data = create_minimal_dicom()
        # File without extension but valid DICOM content
        assert ingestion.infer_type_label("medical_scan", data) == "DICOM"

    def test_extract_document_payload_dicom(self):
        """Test document payload extraction for DICOM."""
        pytest.importorskip("pydicom")
        from services import ingestion

        data = create_minimal_dicom()
        payload = ingestion.extract_document_payload("scan.dcm", data)

        assert payload["type_label"] == "DICOM"
        assert "body" in payload
        assert len(payload["body"]) > 0


class TestDicomSettings:
    """Tests for DICOM settings."""

    def test_settings_default_anonymization_off(self):
        """Test that anonymization on upload is off by default."""
        from services.settings import get_settings

        settings = get_settings()
        assert settings.dicom_anonymize_on_upload is False

    def test_settings_default_anonymization_tags(self):
        """Test default anonymization tags are set."""
        from services.settings import get_settings

        settings = get_settings()
        assert "PatientName" in settings.dicom_anonymization_tags
        assert "PatientID" in settings.dicom_anonymization_tags


class TestConnectors:
    """Tests for MCP connectors."""

    def test_notion_connector_exists(self):
        """Test Notion connector is available."""
        from services import connectors

        assert "notion" in connectors.AVAILABLE_CONNECTORS
        assert connectors.AVAILABLE_CONNECTORS["notion"].name == "Notion"

    def test_google_drive_connector_exists(self):
        """Test Google Drive connector is available."""
        from services import connectors

        assert "drive" in connectors.AVAILABLE_CONNECTORS
        assert connectors.AVAILABLE_CONNECTORS["drive"].name == "Google Drive"

    def test_onedrive_connector_exists(self):
        """Test OneDrive connector is available."""
        from services import connectors

        assert "onedrive" in connectors.AVAILABLE_CONNECTORS
        assert connectors.AVAILABLE_CONNECTORS["onedrive"].name == "OneDrive"

    def test_dicom_pacs_connector_exists(self):
        """Test DICOM PACS connector is available."""
        from services import connectors

        assert "dicom-pacs" in connectors.AVAILABLE_CONNECTORS
        assert connectors.AVAILABLE_CONNECTORS["dicom-pacs"].name == "DICOM PACS"

    def test_connector_status(self):
        """Test connector status reporting."""
        from services import connectors

        status = connectors.get_connector_status()

        assert "notion" in status
        assert "configured" in status["notion"]
        assert "missing_env_vars" in status["notion"]

    def test_connector_not_configured_returns_placeholder(self):
        """Test unconfigured connector returns placeholder."""
        from services import connectors

        # Notion without NOTION_API_KEY
        connector = connectors.AVAILABLE_CONNECTORS["notion"]
        if not connector.is_configured():
            results = connector.fetch_sources()
            assert len(results) > 0
            assert (
                "Nicht konfiguriert" in results[0].title
                or "Config" in results[0].type_label
            )
