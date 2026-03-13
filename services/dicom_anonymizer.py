"""DICOM anonymization service for medical imaging data.

Provides configurable anonymization of DICOM files, removing PHI
(Protected Health Information) while preserving clinical utility.
"""

from __future__ import annotations

import csv
import datetime
import io
import logging
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from services.settings import get_settings

_logger = logging.getLogger(__name__)

# Default tags to anonymize (HIPAA Safe Harbor identifiers)
DEFAULT_TAGS_TO_ANONYMIZE: List[Tuple[str, str]] = [
    ("PatientName", ""),
    ("PatientID", ""),
    ("PatientBirthDate", ""),
    ("PatientSex", ""),
    ("PatientAge", ""),
    ("PatientAddress", ""),
    ("PatientWeight", ""),
    ("PatientTelephoneNumbers", ""),
    ("OtherPatientIDs", ""),
    ("OtherPatientNames", ""),
    ("EthnicGroup", ""),
    ("InstitutionName", ""),
    ("InstitutionAddress", ""),
    ("ReferringPhysicianName", ""),
    ("PhysiciansOfRecord", ""),
    ("PerformingPhysicianName", ""),
    ("OperatorsName", ""),
    ("StudyID", ""),
    ("AccessionNumber", ""),
    ("StudyDate", ""),
    ("SeriesDate", ""),
    ("AcquisitionDate", ""),
    ("ContentDate", ""),
    ("StudyTime", ""),
    ("SeriesTime", ""),
    ("AcquisitionTime", ""),
    ("ContentTime", ""),
]

# UID tags that should be regenerated
UID_TAGS: List[str] = [
    "StudyInstanceUID",
    "SeriesInstanceUID",
    "SOPInstanceUID",
    "FrameOfReferenceUID",
]


@dataclass
class AnonymizationResult:
    """Result of anonymizing a single DICOM file."""

    original_filename: str
    anonymized_data: bytes
    original_id: str
    anonymization_id: str
    tags_anonymized: List[str] = field(default_factory=list)
    uids_regenerated: List[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class AnonymizationConfig:
    """Configuration for DICOM anonymization."""

    tags_to_anonymize: List[Tuple[str, str]] = field(
        default_factory=lambda: list(DEFAULT_TAGS_TO_ANONYMIZE)
    )
    regenerate_uids: bool = True
    remove_private_tags: bool = True
    preserve_study_uid: bool = False  # Keep same StudyInstanceUID for all files
    anonymization_id: Optional[str] = None

    def __post_init__(self):
        if not self.anonymization_id:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self.anonymization_id = f"anon_{timestamp}_{uuid4().hex[:8]}"


def _generate_dicom_uid() -> str:
    """Generate a new DICOM UID.

    Uses a combination of timestamp and UUID to create a unique UID.
    """
    try:
        from pydicom.uid import generate_uid

        return generate_uid()
    except ImportError:
        # Fallback if pydicom not available
        return f"2.25.{uuid4().int}"


def anonymize_dicom_bytes(
    data: bytes,
    filename: str,
    config: AnonymizationConfig,
) -> AnonymizationResult:
    """Anonymize a DICOM file from bytes.

    Args:
        data: Raw DICOM file bytes
        filename: Original filename for reference
        config: Anonymization configuration

    Returns:
        AnonymizationResult with anonymized data and metadata
    """
    try:
        import pydicom
    except ImportError:
        return AnonymizationResult(
            original_filename=filename,
            anonymized_data=b"",
            original_id="",
            anonymization_id=config.anonymization_id or "",
            error="pydicom not installed",
        )

    try:
        ds = pydicom.dcmread(io.BytesIO(data))
    except Exception as exc:
        return AnonymizationResult(
            original_filename=filename,
            anonymized_data=b"",
            original_id="",
            anonymization_id=config.anonymization_id or "",
            error=f"Failed to read DICOM: {exc}",
        )

    # Get original patient ID for mapping
    original_id = str(
        getattr(ds, "PatientID", None)
        or getattr(ds, "SOPInstanceUID", None)
        or filename
    )

    tags_anonymized: List[str] = []
    uids_regenerated: List[str] = []

    # Anonymize specified tags
    for tag_name, replacement_value in config.tags_to_anonymize:
        if hasattr(ds, tag_name):
            setattr(ds, tag_name, replacement_value)
            tags_anonymized.append(tag_name)

    # Add anonymization metadata to PatientComments
    anon_comment = (
        f"AnonymizationID:{config.anonymization_id} "
        f"Date:{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    setattr(ds, "PatientComments", anon_comment)

    # Regenerate UIDs if configured
    if config.regenerate_uids:
        for uid_tag in UID_TAGS:
            if hasattr(ds, uid_tag):
                new_uid = _generate_dicom_uid()
                setattr(ds, uid_tag, new_uid)
                uids_regenerated.append(uid_tag)

    # Remove private tags if configured
    if config.remove_private_tags:
        ds.remove_private_tags()

    # Write anonymized data
    output = io.BytesIO()
    # Use enforce_file_format=False to handle files without File Meta Information
    ds.save_as(output, enforce_file_format=False)
    output.seek(0)

    return AnonymizationResult(
        original_filename=filename,
        anonymized_data=output.read(),
        original_id=original_id,
        anonymization_id=config.anonymization_id or "",
        tags_anonymized=tags_anonymized,
        uids_regenerated=uids_regenerated,
    )


def anonymize_dicom_file(
    input_path: Path,
    output_path: Path,
    config: AnonymizationConfig,
) -> AnonymizationResult:
    """Anonymize a DICOM file from disk.

    Args:
        input_path: Path to input DICOM file
        output_path: Path to write anonymized file
        config: Anonymization configuration

    Returns:
        AnonymizationResult with anonymized data and metadata
    """
    try:
        data = input_path.read_bytes()
    except Exception as exc:
        return AnonymizationResult(
            original_filename=input_path.name,
            anonymized_data=b"",
            original_id="",
            anonymization_id=config.anonymization_id or "",
            error=f"Failed to read file: {exc}",
        )

    result = anonymize_dicom_bytes(data, input_path.name, config)

    if not result.error:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(result.anonymized_data)

    return result


def anonymize_dicom_directory(
    input_dir: Path,
    output_dir: Path,
    config: AnonymizationConfig,
    mapping_csv_path: Optional[Path] = None,
) -> Tuple[List[AnonymizationResult], Path]:
    """Anonymize all DICOM files in a directory.

    Args:
        input_dir: Directory containing DICOM files
        output_dir: Directory to write anonymized files
        config: Anonymization configuration
        mapping_csv_path: Optional path for mapping CSV (default: output_dir/anonymization_mapping.csv)

    Returns:
        Tuple of (list of results, path to mapping CSV)
    """
    from services import parsers

    if output_dir.exists():
        import shutil

        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not mapping_csv_path:
        mapping_csv_path = output_dir / "anonymization_mapping.csv"

    results: List[AnonymizationResult] = []

    # Collect all files to process
    files_to_process: List[Tuple[Path, Path]] = []
    for root, _, files in os.walk(input_dir):
        for filename in files:
            src_path = Path(root) / filename
            rel_path = src_path.relative_to(input_dir)
            dest_path = output_dir / rel_path

            # Check if it's a DICOM file (by extension or content)
            is_dicom = src_path.suffix.lower() in {".dcm", ".dicom"}
            if not is_dicom:
                try:
                    with src_path.open("rb") as f:
                        header = f.read(132)
                        is_dicom = parsers.is_dicom_file(header)
                except Exception:
                    pass

            if is_dicom:
                files_to_process.append((src_path, dest_path))
            else:
                # Copy non-DICOM files as-is
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil

                shutil.copy2(src_path, dest_path)

    # Process DICOM files and write mapping
    with mapping_csv_path.open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "original_id",
            "anonymization_id",
            "src_file",
            "anonymized_file",
            "tags_anonymized",
            "uids_regenerated",
            "error",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for src_path, dest_path in files_to_process:
            result = anonymize_dicom_file(src_path, dest_path, config)
            results.append(result)

            writer.writerow(
                {
                    "original_id": result.original_id,
                    "anonymization_id": result.anonymization_id,
                    "src_file": str(src_path),
                    "anonymized_file": str(dest_path),
                    "tags_anonymized": ",".join(result.tags_anonymized),
                    "uids_regenerated": ",".join(result.uids_regenerated),
                    "error": result.error or "",
                }
            )

    return results, mapping_csv_path


def create_anonymized_zip(
    results: List[AnonymizationResult],
    zip_filename: Optional[str] = None,
) -> bytes:
    """Create a ZIP archive of anonymized DICOM files.

    Args:
        results: List of anonymization results
        zip_filename: Optional filename for the ZIP (without extension)

    Returns:
        ZIP file as bytes
    """
    if not zip_filename:
        zip_filename = (
            f"anonymized_dicom_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for result in results:
            if result.error:
                continue
            # Use original filename in ZIP
            zf.writestr(result.original_filename, result.anonymized_data)

    zip_buffer.seek(0)
    return zip_buffer.read()


def get_dicom_identifiable_fields(data: bytes) -> Dict[str, str]:
    """Extract potentially identifiable fields from a DICOM file.

    Used for preview before anonymization.

    Args:
        data: Raw DICOM file bytes

    Returns:
        Dictionary of tag name -> current value for identifiable fields
    """
    try:
        import pydicom
    except ImportError:
        return {"error": "pydicom not installed"}

    try:
        ds = pydicom.dcmread(io.BytesIO(data))
    except Exception as exc:
        return {"error": f"Failed to read DICOM: {exc}"}

    identifiable: Dict[str, str] = {}

    for tag_name, _ in DEFAULT_TAGS_TO_ANONYMIZE:
        if hasattr(ds, tag_name):
            value = getattr(ds, tag_name)
            if value:
                identifiable[tag_name] = str(value)

    for uid_tag in UID_TAGS:
        if hasattr(ds, uid_tag):
            value = getattr(ds, uid_tag)
            if value:
                identifiable[uid_tag] = str(value)

    return identifiable


def should_anonymize_on_upload() -> bool:
    """Check if DICOM files should be anonymized on upload."""
    settings = get_settings()
    return getattr(settings, "dicom_anonymize_on_upload", False)


def get_anonymization_config() -> AnonymizationConfig:
    """Get the current anonymization configuration from settings."""
    settings = get_settings()

    tags = getattr(settings, "dicom_anonymization_tags", None)
    if tags and isinstance(tags, list):
        tags_to_anonymize = [(tag, "") for tag in tags]
    else:
        tags_to_anonymize = list(DEFAULT_TAGS_TO_ANONYMIZE)

    return AnonymizationConfig(
        tags_to_anonymize=tags_to_anonymize,
        regenerate_uids=True,
        remove_private_tags=True,
    )
