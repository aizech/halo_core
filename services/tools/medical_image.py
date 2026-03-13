"""Medical image preprocessing tools for analysis."""

from __future__ import annotations

import io
import logging
from typing import Optional, Tuple

from PIL import Image as PILImage

_logger = logging.getLogger(__name__)

# DICOM is optional - may not be installed
try:
    import pydicom
    import numpy as np

    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    _logger.debug("pydicom not available - DICOM preprocessing disabled")


def is_dicom_available() -> bool:
    """Check if DICOM processing is available."""
    return DICOM_AVAILABLE


def dicom_to_image(
    dicom_data: bytes,
    anonymize: bool = True,
    window_center: Optional[float] = None,
    window_width: Optional[float] = None,
) -> Tuple[Optional[PILImage.Image], Optional[str]]:
    """Convert DICOM bytes to PIL Image for analysis.

    Args:
        dicom_data: Raw DICOM file bytes
        anonymize: Whether to clear identifying tags (default True)
        window_center: Optional window center for contrast
        window_width: Optional window width for contrast

    Returns:
        Tuple of (PIL Image, error message if any)
    """
    if not DICOM_AVAILABLE:
        return None, "pydicom not installed - cannot process DICOM files"

    try:
        # Read DICOM from bytes
        ds = pydicom.dcmread(io.BytesIO(dicom_data))

        # Anonymize if requested
        if anonymize:
            _anonymize_dicom_dataset(ds)

        # Get pixel array
        pixel_array = ds.pixel_array

        # Apply windowing if specified or use default
        if window_center is not None and window_width is not None:
            pixel_array = _apply_windowing(pixel_array, window_center, window_width)
        else:
            # Auto-scale to 0-255
            pixel_array = _auto_scale(pixel_array)

        # Convert to PIL Image
        if len(pixel_array.shape) == 2:
            # Grayscale - convert to RGB for vision models
            pil_image = PILImage.fromarray(pixel_array.astype("uint8"))
            pil_image = pil_image.convert("RGB")
        else:
            # Already multi-channel
            pil_image = PILImage.fromarray(pixel_array.astype("uint8"))

        return pil_image, None

    except Exception as e:
        _logger.error("Failed to convert DICOM to image: %s", e)
        return None, str(e)


def _anonymize_dicom_dataset(ds: "pydicom.dataset.Dataset") -> None:
    """Clear common identifying tags from DICOM dataset."""
    tags_to_clear = [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientSex",
        "PatientAge",
        "PatientAddress",
        "PatientTelephoneNumbers",
        "AccessionNumber",
        "InstitutionName",
        "InstitutionAddress",
        "ReferringPhysicianName",
        "PerformingPhysicianName",
        "OperatorsName",
        "StudyID",
        "StudyDate",
        "StudyTime",
        "SeriesDate",
        "SeriesTime",
        "AcquisitionDate",
        "AcquisitionTime",
    ]

    try:
        ds.remove_private_tags()
    except Exception:
        pass

    for tag_name in tags_to_clear:
        if hasattr(ds, tag_name):
            try:
                setattr(ds, tag_name, "")
            except Exception:
                pass

    # Remove identifying sequences
    for seq_name in ["OtherPatientIDsSequence", "ReferencedPatientSequence"]:
        if hasattr(ds, seq_name):
            try:
                delattr(ds, seq_name)
            except Exception:
                pass


def _apply_windowing(
    pixel_array: "np.ndarray", window_center: float, window_width: float
) -> "np.ndarray":
    """Apply DICOM windowing for contrast adjustment."""
    if not DICOM_AVAILABLE:
        return pixel_array

    min_value = window_center - window_width / 2
    max_value = window_center + window_width / 2

    # Clip and scale
    pixel_array = np.clip(pixel_array, min_value, max_value)
    pixel_array = (pixel_array - min_value) / (max_value - min_value) * 255

    return pixel_array


def _auto_scale(pixel_array: "np.ndarray") -> "np.ndarray":
    """Auto-scale pixel array to 0-255 range."""
    if not DICOM_AVAILABLE:
        return pixel_array

    min_val = pixel_array.min()
    max_val = pixel_array.max()

    if max_val > min_val:
        pixel_array = (pixel_array - min_val) / (max_val - min_val) * 255
    else:
        pixel_array = np.zeros_like(pixel_array)

    return pixel_array


def image_to_bytes(image: PILImage.Image, format: str = "PNG") -> bytes:
    """Convert PIL Image to bytes for AI analysis.

    Args:
        image: PIL Image
        format: Output format (PNG, JPEG)

    Returns:
        Image as bytes
    """
    buffer = io.BytesIO()
    image.save(buffer, format=format)
    return buffer.getvalue()


def prepare_image_for_analysis(
    image_data: bytes,
    is_dicom: bool = False,
    max_size: Tuple[int, int] = (2048, 2048),
) -> Tuple[Optional[bytes], Optional[str]]:
    """Prepare image data for AI vision analysis.

    Args:
        image_data: Raw image or DICOM bytes
        is_dicom: Whether the data is DICOM format
        max_size: Maximum dimensions for resizing

    Returns:
        Tuple of (prepared image bytes, error message if any)
    """
    try:
        if is_dicom:
            pil_image, error = dicom_to_image(image_data)
            if error:
                return None, error
        else:
            pil_image = PILImage.open(io.BytesIO(image_data))

        # Resize if too large
        if pil_image.width > max_size[0] or pil_image.height > max_size[1]:
            pil_image.thumbnail(max_size, PILImage.Resampling.LANCZOS)

        # Convert to RGB if needed
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        return image_to_bytes(pil_image), None

    except Exception as e:
        _logger.error("Failed to prepare image for analysis: %s", e)
        return None, str(e)
