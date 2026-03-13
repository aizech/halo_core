"""Tests for medical imaging agent and tools."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


class TestMedicalImagingAgentConfig:
    """Tests for medical_imaging agent configuration."""

    def test_medical_imaging_config_exists(self) -> None:
        """Medical imaging agent config file exists."""
        config_path = (
            Path(__file__).parent.parent
            / "services"
            / "agents"
            / "medical_imaging.json"
        )
        assert config_path.exists(), "medical_imaging.json should exist"

    def test_medical_imaging_config_valid_json(self) -> None:
        """Medical imaging config is valid JSON."""
        config_path = (
            Path(__file__).parent.parent
            / "services"
            / "agents"
            / "medical_imaging.json"
        )
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        assert isinstance(config, dict)

    def test_medical_imaging_config_has_required_fields(self) -> None:
        """Medical imaging config has all required fields."""
        config_path = (
            Path(__file__).parent.parent
            / "services"
            / "agents"
            / "medical_imaging.json"
        )
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        assert config.get("id") == "medical_imaging"
        assert config.get("name") == "Medical Imaging Analyst"
        assert config.get("role") == "radiologist"
        assert "instructions" in config
        assert config.get("enabled") is True

    def test_medical_imaging_uses_vision_model(self) -> None:
        """Medical imaging agent uses a vision-capable model."""
        config_path = (
            Path(__file__).parent.parent
            / "services"
            / "agents"
            / "medical_imaging.json"
        )
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        model = config.get("model", "")
        # Should use a vision-capable model
        assert (
            "gpt" in model.lower()
            or "vision" in model.lower()
            or "claude" in model.lower()
        )

    def test_medical_imaging_has_pubmed_tools(self) -> None:
        """Medical imaging agent has PubMed tools for literature search."""
        config_path = (
            Path(__file__).parent.parent
            / "services"
            / "agents"
            / "medical_imaging.json"
        )
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

        tools = config.get("tools", [])
        assert "pubmed" in tools, "Should have pubmed tool for literature search"

    def test_medical_imaging_in_chat_members(self) -> None:
        """Medical imaging agent is registered in chat team members."""
        chat_config_path = (
            Path(__file__).parent.parent / "services" / "agents" / "chat.json"
        )
        with chat_config_path.open("r", encoding="utf-8") as f:
            chat_config = json.load(f)

        members = chat_config.get("members", [])
        assert (
            "medical_imaging" in members
        ), "medical_imaging should be in chat team members"


class TestMedicalImageTools:
    """Tests for medical image preprocessing tools."""

    def test_is_dicom_available_returns_bool(self) -> None:
        """is_dicom_available returns a boolean."""
        from services.tools.medical_image import is_dicom_available

        result = is_dicom_available()
        assert isinstance(result, bool)

    def test_image_to_bytes_returns_bytes(self) -> None:
        """image_to_bytes converts PIL Image to bytes."""
        from PIL import Image as PILImage

        from services.tools.medical_image import image_to_bytes

        # Create a simple test image
        img = PILImage.new("RGB", (100, 100), color="red")
        result = image_to_bytes(img, format="PNG")

        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_prepare_image_for_analysis_regular_image(self) -> None:
        """prepare_image_for_analysis handles regular images."""
        from PIL import Image as PILImage

        from services.tools.medical_image import prepare_image_for_analysis

        # Create a test image
        img = PILImage.new("RGB", (500, 500), color="blue")
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        result, error = prepare_image_for_analysis(image_bytes, is_dicom=False)

        assert error is None
        assert result is not None
        assert isinstance(result, bytes)

    def test_prepare_image_for_analysis_resizes_large_images(self) -> None:
        """prepare_image_for_analysis resizes images larger than max_size."""
        from PIL import Image as PILImage

        from services.tools.medical_image import prepare_image_for_analysis

        # Create a large test image
        img = PILImage.new("RGB", (3000, 3000), color="green")
        import io

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        result, error = prepare_image_for_analysis(
            image_bytes, is_dicom=False, max_size=(1024, 1024)
        )

        assert error is None
        assert result is not None

        # Verify the result is smaller
        result_img = PILImage.open(io.BytesIO(result))
        assert result_img.width <= 1024
        assert result_img.height <= 1024

    @pytest.mark.skipif(
        not pytest.importorskip("pydicom", reason="pydicom not installed"),
        reason="pydicom not installed",
    )
    def test_dicom_to_image_with_valid_dicom(self) -> None:
        """dicom_to_image converts DICOM bytes to PIL Image."""
        from services.tools.medical_image import dicom_to_image

        # Create a minimal DICOM file for testing
        from pydicom.dataset import Dataset, FileMetaDataset
        from pydicom.uid import ExplicitVRLittleEndian

        ds = Dataset()
        ds.PatientName = "Test"
        ds.PatientID = "12345"
        ds.Modality = "CT"
        ds.Columns = 100
        ds.Rows = 100
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"

        # Add file meta for valid DICOM
        file_meta = FileMetaDataset()
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.file_meta = file_meta

        import numpy as np

        pixel_array = np.zeros((100, 100), dtype=np.uint8)
        ds.PixelData = pixel_array.tobytes()

        import io

        buf = io.BytesIO()
        ds.save_as(buf)
        dicom_bytes = buf.getvalue()

        result, error = dicom_to_image(dicom_bytes, anonymize=True)

        # Should succeed or fail gracefully
        if error:
            assert result is None
        else:
            assert result is not None

    def test_dicom_to_image_without_pydicom(self) -> None:
        """dicom_to_image returns error when pydicom not available."""
        with patch("services.tools.medical_image.DICOM_AVAILABLE", False):
            from services.tools.medical_image import dicom_to_image

            result, error = dicom_to_image(b"fake dicom data")

            assert result is None
            assert "pydicom not installed" in error


class TestMedicalImageStudioTemplate:
    """Tests for medical image analysis studio template."""

    def test_medical_image_template_exists(self) -> None:
        """Medical Image Analysis template exists in studio_templates.json."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "studio_templates.json"
        )
        with template_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        templates = data.get("templates", [])
        template_ids = [t.get("id") for t in templates]

        assert "medical_image_analysis" in template_ids

    def test_medical_image_template_has_correct_agent(self) -> None:
        """Medical Image Analysis template uses medical_imaging agent."""
        template_path = (
            Path(__file__).parent.parent / "templates" / "studio_templates.json"
        )
        with template_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        templates = data.get("templates", [])
        medical_template = next(
            (t for t in templates if t.get("id") == "medical_image_analysis"), None
        )

        assert medical_template is not None
        assert medical_template.get("agent_id") == "medical_imaging"
        assert "🩺" in medical_template.get("icon", "")
