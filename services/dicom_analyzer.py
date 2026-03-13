"""DICOM analysis engine for medical imaging AI analysis.

Provides functions to analyze DICOM series using AI agents,
with automatic anonymization and structured result extraction.
"""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.dicom_scoring import (
    AnomalyFinding,
    DicomAnalysisResult,
    QualityScore,
    SeriesAnalysisResult,
    Severity,
    generate_analysis_id,
)

_logger = logging.getLogger(__name__)

# DICOM is optional - may not be installed
try:
    import pydicom
    import numpy as np

    DICOM_AVAILABLE = True
except ImportError:
    DICOM_AVAILABLE = False
    _logger.debug("pydicom not available - DICOM analysis disabled")


def is_dicom_available() -> bool:
    """Check if DICOM processing is available."""
    return DICOM_AVAILABLE


def _get_dicom_files_from_directory(directory: Path) -> List[Path]:
    """Collect all DICOM files from a directory.

    Detects DICOM files by extension (.dcm, .dicom) or by magic bytes.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    dicom_files: List[Path] = []

    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = Path(root) / filename

            # Check by extension
            if filepath.suffix.lower() in {".dcm", ".dicom"}:
                dicom_files.append(filepath)
                continue

            # Check by magic bytes (128-byte preamble + DICM)
            try:
                with filepath.open("rb") as f:
                    header = f.read(132)
                    if len(header) >= 132 and header[128:132] == b"DICM":
                        dicom_files.append(filepath)
            except Exception:
                continue

    return sorted(dicom_files)


def _extract_dicom_metadata(data: bytes, filepath: str) -> Dict[str, Any]:
    """Extract metadata from DICOM bytes."""
    if not DICOM_AVAILABLE:
        return {"error": "pydicom not installed"}

    try:
        ds = pydicom.dcmread(io.BytesIO(data))
        return {
            "sop_instance_uid": str(getattr(ds, "SOPInstanceUID", "")),
            "series_number": int(getattr(ds, "SeriesNumber", 0)),
            "instance_number": int(getattr(ds, "InstanceNumber", 0)),
            "study_instance_uid": str(getattr(ds, "StudyInstanceUID", "")),
            "series_instance_uid": str(getattr(ds, "SeriesInstanceUID", "")),
            "modality": str(getattr(ds, "Modality", "")),
            "study_description": str(getattr(ds, "StudyDescription", "")),
            "series_description": str(getattr(ds, "SeriesDescription", "")),
            "patient_position": str(getattr(ds, "PatientPosition", "")),
            "rows": int(getattr(ds, "Rows", 0)),
            "columns": int(getattr(ds, "Columns", 0)),
            "bits_stored": int(getattr(ds, "BitsStored", 8)),
            "photometric_interpretation": str(
                getattr(ds, "PhotometricInterpretation", "")
            ),
            "file_path": filepath,
        }
    except Exception as e:
        _logger.error("Failed to extract DICOM metadata from %s: %s", filepath, e)
        return {"error": str(e), "file_path": filepath}


def _convert_dicom_to_image_bytes(
    data: bytes, anonymize: bool = True
) -> Tuple[Optional[bytes], Optional[str]]:
    """Convert DICOM bytes to image bytes suitable for AI vision analysis.

    Returns:
        Tuple of (image_bytes, error_message)
    """
    if not DICOM_AVAILABLE:
        return None, "pydicom not installed"

    try:
        from PIL import Image as PILImage

        # Read DICOM
        ds = pydicom.dcmread(io.BytesIO(data))

        # Check if pixel data exists
        if not hasattr(ds, "pixel_array"):
            return None, "No pixel data in DICOM file"

        # Get pixel array
        pixel_array = ds.pixel_array

        # Apply windowing if available for better visualization
        if hasattr(ds, "WindowCenter") and hasattr(ds, "WindowWidth"):
            try:
                wc = (
                    float(ds.WindowCenter)
                    if not isinstance(ds.WindowCenter, list)
                    else float(ds.WindowCenter[0])
                )
                ww = (
                    float(ds.WindowWidth)
                    if not isinstance(ds.WindowWidth, list)
                    else float(ds.WindowWidth[0])
                )
                pixel_array = _apply_windowing(pixel_array, wc, ww)
            except Exception:
                pixel_array = _auto_scale(pixel_array)
        else:
            pixel_array = _auto_scale(pixel_array)

        # Convert to PIL Image
        if len(pixel_array.shape) == 2:
            # Grayscale - convert to RGB for vision models
            pil_image = PILImage.fromarray(pixel_array.astype("uint8"))
            pil_image = pil_image.convert("RGB")
        else:
            # Already multi-channel
            pil_image = PILImage.fromarray(pixel_array.astype("uint8"))

        # Resize if too large (vision models have limits)
        max_size = 2048
        if pil_image.width > max_size or pil_image.height > max_size:
            pil_image.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)

        # Convert to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return buffer.getvalue(), None

    except Exception as e:
        _logger.error("Failed to convert DICOM to image: %s", e)
        return None, str(e)


def _apply_windowing(
    pixel_array: "np.ndarray", window_center: float, window_width: float
) -> "np.ndarray":
    """Apply DICOM windowing for contrast adjustment."""
    min_value = window_center - window_width / 2
    max_value = window_center + window_width / 2

    # Clip and scale
    pixel_array = np.clip(pixel_array, min_value, max_value)
    pixel_array = (pixel_array - min_value) / (max_value - min_value) * 255

    return pixel_array


def _auto_scale(pixel_array: "np.ndarray") -> "np.ndarray":
    """Auto-scale pixel array to 0-255 range."""
    min_val = pixel_array.min()
    max_val = pixel_array.max()

    if max_val > min_val:
        pixel_array = (pixel_array - min_val) / (max_val - min_val) * 255
    else:
        pixel_array = np.zeros_like(pixel_array)

    return pixel_array


def _parse_agent_analysis_response(
    response_text: str,
) -> Tuple[List[AnomalyFinding], QualityScore, str]:
    """Parse AI agent response into structured findings.

    Attempts to extract structured anomaly findings and quality scores
    from the agent's text response.
    """
    anomalies: List[AnomalyFinding] = []
    quality = QualityScore.default()
    summary = ""

    # Try to extract JSON blocks from response
    try:
        # Look for JSON code blocks
        import re

        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        json_matches = re.findall(json_pattern, response_text)

        for json_str in json_matches:
            try:
                data = json.loads(json_str)

                # Parse anomalies if present
                if "anomalies" in data or "findings" in data:
                    findings_data = data.get("anomalies", data.get("findings", []))
                    for f in findings_data:
                        anomaly = AnomalyFinding(
                            anomaly_type=f.get(
                                "type", f.get("anomaly_type", "unknown")
                            ),
                            location=f.get("location", "unspecified"),
                            severity=Severity.from_string(f.get("severity", "normal")),
                            confidence=float(f.get("confidence", 0.5)),
                            description=f.get("description", ""),
                            measurements=f.get("measurements", {}),
                            laterality=f.get("laterality"),
                        )
                        anomalies.append(anomaly)

                # Parse quality scores if present
                if "quality" in data:
                    q = data["quality"]
                    quality = QualityScore(
                        positioning=int(q.get("positioning", 3)),
                        contrast=int(q.get("contrast", 3)),
                        artifacts=int(q.get("artifacts", 3)),
                        noise_level=int(q.get("noise_level", 3)),
                        motion_blur=int(q.get("motion_blur", 3)),
                    )

                # Parse summary if present
                if "summary" in data:
                    summary = data["summary"]

            except json.JSONDecodeError:
                continue

        # If no structured data found, try to extract from text
        if not anomalies:
            anomalies = _extract_findings_from_text(response_text)

        # Generate summary from response if not found
        if not summary:
            summary = _extract_summary_from_text(response_text)

    except Exception as e:
        _logger.warning("Failed to parse agent response: %s", e)
        summary = response_text[:500] if response_text else "Analysis completed"

    return anomalies, quality, summary


def _extract_findings_from_text(text: str) -> List[AnomalyFinding]:
    """Extract anomaly findings from unstructured text response."""
    anomalies: List[AnomalyFinding] = []

    # Common patterns for findings
    severity_patterns = {
        Severity.CRITICAL: r"(critical|urgent|emergency|immediate)",
        Severity.SEVERE: r"(severe|significant|major|serious)",
        Severity.MODERATE: r"(moderate|notable|relevant)",
        Severity.MILD: r"(mild|minor|small|subtle)",
    }

    # Look for numbered or bulleted findings
    import re

    # Pattern for findings like "1. Finding description" or "- Finding description"
    finding_pattern = (
        r"(?:^|\n)\s*(?:\d+\.?|[-•])\s*(.+?)(?=(?:\n\s*(?:\d+\.?|[-•])|\n\n|$))"
    )
    matches = re.findall(finding_pattern, text, re.MULTILINE)

    for match in matches:
        if len(match) < 10:  # Skip very short matches
            continue

        # Determine severity from text
        severity = Severity.NORMAL
        for sev, pattern in severity_patterns.items():
            if re.search(pattern, match, re.IGNORECASE):
                severity = sev
                break

        # Extract location (common anatomical terms)
        location_match = re.search(
            r"(?:in|at|within|located in)\s+(the\s+)?(\w+(?:\s+\w+)?)",
            match,
            re.IGNORECASE,
        )
        location = location_match.group(2) if location_match else "unspecified"

        anomaly = AnomalyFinding(
            anomaly_type="detected_finding",
            location=location,
            severity=severity,
            confidence=0.5,  # Default confidence for text-extracted findings
            description=match.strip(),
        )
        anomalies.append(anomaly)

    return anomalies


def _extract_summary_from_text(text: str) -> str:
    """Extract or generate a summary from the response text."""
    # Look for "Summary:" or "Impression:" sections
    import re

    summary_pattern = (
        r"(?:summary|impression|conclusion)[:\s]*\n?(.+?)(?=\n\n|\n[A-Z]|$)"
    )
    match = re.search(summary_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        return match.group(1).strip()[:500]

    # Return first paragraph as summary
    paragraphs = text.split("\n\n")
    if paragraphs:
        return paragraphs[0].strip()[:500]

    return text[:500]


def analyze_single_dicom(
    dicom_data: bytes,
    file_path: str,
    agent_run_func: Optional[callable] = None,
    anonymize: bool = True,
) -> DicomAnalysisResult:
    """Analyze a single DICOM file.

    Args:
        dicom_data: Raw DICOM file bytes
        file_path: Path or name of the file for reference
        agent_run_func: Function to run AI agent analysis (image_bytes) -> response_text
        anonymize: Whether to anonymize before analysis (default True)

    Returns:
        DicomAnalysisResult with findings and quality assessment
    """
    if not DICOM_AVAILABLE:
        return DicomAnalysisResult(
            file_path=file_path,
            sop_instance_uid="",
            series_number=0,
            instance_number=0,
            anomalies=[],
            anomaly_count=0,
            quality=QualityScore.default(),
            summary="",
            raw_agent_response="",
            error="pydicom not installed",
        )

    # Extract metadata
    metadata = _extract_dicom_metadata(dicom_data, file_path)

    if "error" in metadata:
        return DicomAnalysisResult(
            file_path=file_path,
            sop_instance_uid="",
            series_number=0,
            instance_number=0,
            anomalies=[],
            anomaly_count=0,
            quality=QualityScore.default(),
            summary="",
            raw_agent_response="",
            error=metadata["error"],
        )

    # Convert to image for AI analysis
    image_bytes, error = _convert_dicom_to_image_bytes(dicom_data, anonymize=anonymize)

    if error:
        return DicomAnalysisResult(
            file_path=file_path,
            sop_instance_uid=metadata.get("sop_instance_uid", ""),
            series_number=metadata.get("series_number", 0),
            instance_number=metadata.get("instance_number", 0),
            anomalies=[],
            anomaly_count=0,
            quality=QualityScore.default(),
            summary="",
            raw_agent_response="",
            error=error,
        )

    # Run AI analysis if agent function provided
    raw_response = ""
    anomalies: List[AnomalyFinding] = []
    quality = QualityScore.default()
    summary = ""

    if agent_run_func:
        try:
            raw_response = agent_run_func(image_bytes, metadata)
            anomalies, quality, summary = _parse_agent_analysis_response(raw_response)
        except Exception as e:
            _logger.error("Agent analysis failed for %s: %s", file_path, e)
            summary = f"Analysis failed: {e}"
    else:
        # No agent provided - return metadata only
        summary = f"DICOM file loaded: {metadata.get('modality', 'Unknown')} modality, {metadata.get('rows', 0)}x{metadata.get('columns', 0)} pixels"

    return DicomAnalysisResult(
        file_path=file_path,
        sop_instance_uid=metadata.get("sop_instance_uid", ""),
        series_number=metadata.get("series_number", 0),
        instance_number=metadata.get("instance_number", 0),
        anomalies=anomalies,
        anomaly_count=len(anomalies),
        quality=quality,
        summary=summary,
        raw_agent_response=raw_response,
        image_bytes=image_bytes,  # Store converted image for display
    )


def analyze_dicom_series(
    directory: Path,
    agent_run_func: Optional[callable] = None,
    anonymize: bool = True,
    progress_callback: Optional[callable] = None,
) -> SeriesAnalysisResult:
    """Analyze all DICOM files in a directory.

    Args:
        directory: Path to directory containing DICOM files
        agent_run_func: Function to run AI agent analysis
        anonymize: Whether to anonymize before analysis
        progress_callback: Optional callback(current, total, filename) for progress updates

    Returns:
        SeriesAnalysisResult with aggregated findings
    """
    if not DICOM_AVAILABLE:
        return SeriesAnalysisResult(
            analysis_id=generate_analysis_id(),
            study_instance_uid="",
            series_instance_uid="",
            patient_info={},
            study_info={},
            series_info={},
            dicom_results=[],
            analysis_source="directory",
        )

    # Collect DICOM files
    dicom_files = _get_dicom_files_from_directory(directory)

    if not dicom_files:
        raise ValueError(f"No DICOM files found in {directory}")

    analysis_id = generate_analysis_id()
    dicom_results: List[DicomAnalysisResult] = []

    # Track series/study UIDs for aggregation
    study_uid = ""
    series_uid = ""
    study_info: Dict[str, Any] = {}
    series_info: Dict[str, Any] = {}
    patient_info: Dict[str, Any] = {}

    total = len(dicom_files)
    for i, filepath in enumerate(dicom_files):
        try:
            data = filepath.read_bytes()
            result = analyze_single_dicom(
                dicom_data=data,
                file_path=str(filepath),
                agent_run_func=agent_run_func,
                anonymize=anonymize,
            )
            dicom_results.append(result)

            # Capture UIDs from first successful result
            if i == 0 and result.sop_instance_uid:
                # Re-read to get full metadata
                metadata = _extract_dicom_metadata(data, str(filepath))
                study_uid = metadata.get("study_instance_uid", "")
                series_uid = metadata.get("series_instance_uid", "")
                study_info = {
                    "study_description": metadata.get("study_description", ""),
                    "modality": metadata.get("modality", ""),
                }
                series_info = {
                    "series_description": metadata.get("series_description", ""),
                    "series_number": metadata.get("series_number", 0),
                }
                # Anonymized patient info
                patient_info = {
                    "patient_id": "ANONYMIZED",
                    "patient_name": "ANONYMIZED",
                }

            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total, filepath.name)

        except Exception as e:
            _logger.error("Failed to analyze %s: %s", filepath, e)
            dicom_results.append(
                DicomAnalysisResult(
                    file_path=str(filepath),
                    sop_instance_uid="",
                    series_number=0,
                    instance_number=0,
                    anomalies=[],
                    anomaly_count=0,
                    quality=QualityScore.default(),
                    summary="",
                    raw_agent_response="",
                    error=str(e),
                )
            )

    return SeriesAnalysisResult(
        analysis_id=analysis_id,
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        patient_info=patient_info,
        study_info=study_info,
        series_info=series_info,
        dicom_results=dicom_results,
        analysis_source="directory",
    )


def _add_overall_summary(
    result: SeriesAnalysisResult,
    agent_run_func: Optional[callable] = None,
) -> SeriesAnalysisResult:
    """Add overall summary to the analysis result."""
    result.overall_summary = generate_overall_summary(result, agent_run_func)
    return result


def analyze_uploaded_dicoms(
    files: List[Tuple[str, bytes]],  # List of (filename, data) tuples
    agent_run_func: Optional[callable] = None,
    anonymize: bool = True,
    progress_callback: Optional[callable] = None,
) -> SeriesAnalysisResult:
    """Analyze uploaded DICOM files.

    Args:
        files: List of (filename, data) tuples
        agent_run_func: Function to run AI agent analysis
        anonymize: Whether to anonymize before analysis
        progress_callback: Optional callback for progress updates

    Returns:
        SeriesAnalysisResult with aggregated findings
    """
    if not DICOM_AVAILABLE:
        return SeriesAnalysisResult(
            analysis_id=generate_analysis_id(),
            study_instance_uid="",
            series_instance_uid="",
            patient_info={},
            study_info={},
            series_info={},
            dicom_results=[],
            analysis_source="upload",
        )

    analysis_id = generate_analysis_id()
    dicom_results: List[DicomAnalysisResult] = []

    study_uid = ""
    series_uid = ""
    study_info: Dict[str, Any] = {}
    series_info: Dict[str, Any] = {}
    patient_info: Dict[str, Any] = {}

    total = len(files)
    for i, (filename, data) in enumerate(files):
        try:
            result = analyze_single_dicom(
                dicom_data=data,
                file_path=filename,
                agent_run_func=agent_run_func,
                anonymize=anonymize,
            )
            dicom_results.append(result)

            # Capture UIDs from first successful result
            if i == 0 and result.sop_instance_uid:
                metadata = _extract_dicom_metadata(data, filename)
                study_uid = metadata.get("study_instance_uid", "")
                series_uid = metadata.get("series_instance_uid", "")
                study_info = {
                    "study_description": metadata.get("study_description", ""),
                    "modality": metadata.get("modality", ""),
                }
                series_info = {
                    "series_description": metadata.get("series_description", ""),
                    "series_number": metadata.get("series_number", 0),
                }
                patient_info = {
                    "patient_id": "ANONYMIZED",
                    "patient_name": "ANONYMIZED",
                }

            if progress_callback:
                progress_callback(i + 1, total, filename)

        except Exception as e:
            _logger.error("Failed to analyze %s: %s", filename, e)
            dicom_results.append(
                DicomAnalysisResult(
                    file_path=filename,
                    sop_instance_uid="",
                    series_number=0,
                    instance_number=0,
                    anomalies=[],
                    anomaly_count=0,
                    quality=QualityScore.default(),
                    summary="",
                    raw_agent_response="",
                    error=str(e),
                )
            )

    return SeriesAnalysisResult(
        analysis_id=analysis_id,
        study_instance_uid=study_uid,
        series_instance_uid=series_uid,
        patient_info=patient_info,
        study_info=study_info,
        series_info=series_info,
        dicom_results=dicom_results,
        analysis_source="upload",
    )


def save_analysis_result(result: SeriesAnalysisResult, output_dir: Path) -> Path:
    """Save analysis result to JSON file.

    Args:
        result: Analysis result to save
        output_dir: Directory to save to

    Returns:
        Path to saved file
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{result.analysis_id}.json"
    output_path = output_dir / filename

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)

    _logger.info("Saved analysis result to %s", output_path)
    return output_path


def load_analysis_result(filepath: Path) -> SeriesAnalysisResult:
    """Load analysis result from JSON file.

    Args:
        filepath: Path to JSON file

    Returns:
        SeriesAnalysisResult loaded from file
    """
    with filepath.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return SeriesAnalysisResult.from_dict(data)


def generate_overall_summary(
    result: SeriesAnalysisResult,
    agent_run_func: Optional[callable] = None,
) -> str:
    """Generate an overall summary of all DICOM analysis findings.

    Args:
        result: SeriesAnalysisResult with individual DICOM analyses
        agent_run_func: Function to run AI agent for summary generation

    Returns:
        Overall summary text
    """
    if not agent_run_func or not result.dicom_results:
        return _generate_statistical_summary(result)

    # Build context for the agent
    findings_context = []
    for dicom_result in result.dicom_results:
        if dicom_result.error:
            continue
        findings_context.append(
            f"**{Path(dicom_result.file_path).name}:**\n"
            f"- Anomalien: {dicom_result.anomaly_count}\n"
            f"- Qualität: {dicom_result.quality.overall:.1f}/5\n"
            f"- Zusammenfassung: {dicom_result.summary}\n"
        )
        if dicom_result.anomalies:
            for a in dicom_result.anomalies:
                findings_context.append(
                    f"  - {a.anomaly_type} ({a.severity.to_label()}): {a.description}"
                )

    try:
        # Use text-only analysis for summary (no image needed)
        response = agent_run_func(b"", {"modality": "summary", "summary_request": True})
        if response and len(response) > 50:
            return response
    except Exception as e:
        _logger.warning("Agent summary generation failed: %s", e)

    # Fallback to statistical summary
    return _generate_statistical_summary(result)


def _generate_statistical_summary(result: SeriesAnalysisResult) -> str:
    """Generate a statistical summary without AI agent."""
    parts = []

    # Overview
    parts.append(
        f"Analyse von {len(result.dicom_results)} DICOM-Dateien "
        f"mit insgesamt {result.total_anomalies} Anomalien."
    )

    # Quality assessment
    if result.avg_quality >= 4.0:
        quality_label = "ausgezeichnete"
    elif result.avg_quality >= 3.0:
        quality_label = "gute"
    elif result.avg_quality >= 2.0:
        quality_label = "ausreichende"
    else:
        quality_label = "eingeschränkte"

    parts.append(
        f"Durchschnittliche Bildqualität: {quality_label} ({result.avg_quality:.1f}/5)."
    )

    # Severity distribution
    if result.anomaly_distribution:
        dist_parts = []
        for label, count in result.anomaly_distribution.items():
            if count > 0:
                dist_parts.append(f"{count} {label}")
        if dist_parts:
            parts.append("Schweregrad-Verteilung: " + ", ".join(dist_parts) + ".")

    # Critical findings
    if result.critical_findings:
        parts.append(
            f"ACHTUNG: {len(result.critical_findings)} kritische Befunde erfordern "
            "sofortige klinische Abklärung."
        )
        for finding in result.critical_findings[:3]:  # Show top 3
            parts.append(f"- {finding.anomaly_type} in {finding.location}")

    return " ".join(parts)
