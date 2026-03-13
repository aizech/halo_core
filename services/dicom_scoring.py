"""DICOM analysis scoring models and calculations.

Provides data structures for anomaly detection, quality assessment,
and series-level analysis results.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class Severity(IntEnum):
    """Severity levels for anomaly findings."""

    NORMAL = 1  # No abnormality
    MILD = 2  # Minor finding, likely benign
    MODERATE = 3  # Requires attention, may need follow-up
    SEVERE = 4  # Significant finding, requires action
    CRITICAL = 5  # Urgent finding, immediate attention needed

    @classmethod
    def from_string(cls, value: str) -> "Severity":
        """Convert string to Severity enum."""
        mapping = {
            "normal": cls.NORMAL,
            "mild": cls.MILD,
            "moderate": cls.MODERATE,
            "severe": cls.SEVERE,
            "critical": cls.CRITICAL,
        }
        return mapping.get(value.lower(), cls.NORMAL)

    def to_label(self) -> str:
        """Get human-readable label."""
        labels = {
            Severity.NORMAL: "Normal",
            Severity.MILD: "Mild",
            Severity.MODERATE: "Moderate",
            Severity.SEVERE: "Severe",
            Severity.CRITICAL: "Critical",
        }
        return labels.get(self, "Unknown")


@dataclass
class AnomalyFinding:
    """A single detected anomaly in a DICOM image."""

    anomaly_type: str  # e.g., "nodule", "fracture", "opacity", "mass"
    location: str  # Anatomical location
    severity: Severity
    confidence: float  # 0.0-1.0
    description: str  # Detailed description
    measurements: Dict[str, Any] = field(
        default_factory=dict
    )  # e.g., {"diameter_mm": 15.2}
    laterality: Optional[str] = None  # "left", "right", "bilateral", None
    icd_code: Optional[str] = None  # Optional ICD-10 code reference

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "anomaly_type": self.anomaly_type,
            "location": self.location,
            "severity": self.severity.value,
            "severity_label": self.severity.to_label(),
            "confidence": round(self.confidence, 3),
            "description": self.description,
            "measurements": self.measurements,
            "laterality": self.laterality,
            "icd_code": self.icd_code,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnomalyFinding":
        """Create from dictionary."""
        return cls(
            anomaly_type=data["anomaly_type"],
            location=data["location"],
            severity=Severity(data.get("severity", 1)),
            confidence=data.get("confidence", 0.5),
            description=data.get("description", ""),
            measurements=data.get("measurements", {}),
            laterality=data.get("laterality"),
            icd_code=data.get("icd_code"),
        )


@dataclass
class QualityScore:
    """Technical quality assessment for a DICOM image."""

    positioning: int  # 1-5 (5 = optimal positioning)
    contrast: int  # 1-5 (5 = excellent contrast)
    artifacts: int  # 1-5 (5 = no artifacts)
    noise_level: int  # 1-5 (5 = minimal noise)
    motion_blur: int  # 1-5 (5 = no motion blur)
    overall: float = 0.0  # Weighted average, calculated

    def __post_init__(self):
        """Calculate overall score if not provided."""
        if self.overall == 0.0:
            self.overall = self._calculate_overall()

    def _calculate_overall(self) -> float:
        """Calculate weighted overall quality score."""
        # Weighting: contrast and artifacts most important for diagnosis
        weights = {
            "positioning": 0.20,
            "contrast": 0.30,
            "artifacts": 0.25,
            "noise_level": 0.15,
            "motion_blur": 0.10,
        }
        return round(
            (
                self.positioning * weights["positioning"]
                + self.contrast * weights["contrast"]
                + self.artifacts * weights["artifacts"]
                + self.noise_level * weights["noise_level"]
                + self.motion_blur * weights["motion_blur"]
            ),
            2,
        )

    def is_diagnostic(self) -> bool:
        """Check if image quality is sufficient for diagnosis."""
        return self.overall >= 3.0 and self.contrast >= 2 and self.artifacts >= 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "positioning": self.positioning,
            "contrast": self.contrast,
            "artifacts": self.artifacts,
            "noise_level": self.noise_level,
            "motion_blur": self.motion_blur,
            "overall": self.overall,
            "is_diagnostic": self.is_diagnostic(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityScore":
        """Create from dictionary."""
        return cls(
            positioning=data.get("positioning", 3),
            contrast=data.get("contrast", 3),
            artifacts=data.get("artifacts", 3),
            noise_level=data.get("noise_level", 3),
            motion_blur=data.get("motion_blur", 3),
            overall=data.get("overall", 0.0),
        )

    @classmethod
    def default(cls) -> "QualityScore":
        """Create a default quality score (moderate quality)."""
        return cls(
            positioning=3,
            contrast=3,
            artifacts=3,
            noise_level=3,
            motion_blur=3,
        )


@dataclass
class DicomAnalysisResult:
    """Analysis result for a single DICOM file."""

    file_path: str
    sop_instance_uid: str
    series_number: int
    instance_number: int
    anomalies: List[AnomalyFinding]
    anomaly_count: int
    quality: QualityScore
    summary: str
    raw_agent_response: str
    image_bytes: Optional[bytes] = None  # Converted DICOM image for display
    analysis_timestamp: str = field(
        default_factory=lambda: datetime.datetime.now().isoformat()
    )
    error: Optional[str] = None

    def __post_init__(self):
        """Calculate anomaly count if not provided."""
        if self.anomaly_count == 0 and self.anomalies:
            self.anomaly_count = len(self.anomalies)

    def get_anomalies_by_severity(self, severity: Severity) -> List[AnomalyFinding]:
        """Filter anomalies by severity level."""
        return [a for a in self.anomalies if a.severity == severity]

    def get_critical_anomalies(self) -> List[AnomalyFinding]:
        """Get all critical (severity 4-5) anomalies."""
        return [a for a in self.anomalies if a.severity >= Severity.SEVERE]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "file_path": self.file_path,
            "sop_instance_uid": self.sop_instance_uid,
            "series_number": self.series_number,
            "instance_number": self.instance_number,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "anomaly_count": self.anomaly_count,
            "quality": self.quality.to_dict(),
            "summary": self.summary,
            "raw_agent_response": self.raw_agent_response,
            "analysis_timestamp": self.analysis_timestamp,
            "error": self.error,
            # Note: image_bytes not serialized to JSON
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DicomAnalysisResult":
        """Create from dictionary."""
        anomalies = [AnomalyFinding.from_dict(a) for a in data.get("anomalies", [])]
        quality = QualityScore.from_dict(data.get("quality", {}))
        return cls(
            file_path=data["file_path"],
            sop_instance_uid=data.get("sop_instance_uid", ""),
            series_number=data.get("series_number", 0),
            instance_number=data.get("instance_number", 0),
            anomalies=anomalies,
            anomaly_count=data.get("anomaly_count", len(anomalies)),
            quality=quality,
            summary=data.get("summary", ""),
            raw_agent_response=data.get("raw_agent_response", ""),
            analysis_timestamp=data.get("analysis_timestamp", ""),
            error=data.get("error"),
        )


@dataclass
class SeriesAnalysisResult:
    """Analysis result for an entire DICOM series."""

    analysis_id: str
    study_instance_uid: str
    series_instance_uid: str
    patient_info: Dict[str, Any]  # Anonymized patient info
    study_info: Dict[str, Any]
    series_info: Dict[str, Any]
    dicom_results: List[DicomAnalysisResult]
    total_anomalies: int = 0
    anomaly_distribution: Dict[str, int] = field(default_factory=dict)
    avg_quality: float = 0.0
    critical_findings: List[AnomalyFinding] = field(default_factory=list)
    overall_summary: str = ""  # AI-generated summary of all findings
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    analysis_source: str = "directory"  # "directory", "upload", "pacs"

    def __post_init__(self):
        """Calculate aggregate statistics."""
        if self.total_anomalies == 0 and self.dicom_results:
            self._calculate_aggregates()

    def _calculate_aggregates(self) -> None:
        """Calculate aggregate statistics from DICOM results."""
        # Total anomalies
        self.total_anomalies = sum(r.anomaly_count for r in self.dicom_results)

        # Distribution by severity
        self.anomaly_distribution = {s.to_label(): 0 for s in Severity}
        for result in self.dicom_results:
            for anomaly in result.anomalies:
                label = anomaly.severity.to_label()
                self.anomaly_distribution[label] = (
                    self.anomaly_distribution.get(label, 0) + 1
                )

        # Average quality
        if self.dicom_results:
            self.avg_quality = round(
                sum(r.quality.overall for r in self.dicom_results)
                / len(self.dicom_results),
                2,
            )

        # Critical findings
        self.critical_findings = []
        for result in self.dicom_results:
            self.critical_findings.extend(result.get_critical_anomalies())

    def get_dicom_by_instance(
        self, instance_number: int
    ) -> Optional[DicomAnalysisResult]:
        """Get DICOM result by instance number."""
        for result in self.dicom_results:
            if result.instance_number == instance_number:
                return result
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "analysis_id": self.analysis_id,
            "study_instance_uid": self.study_instance_uid,
            "series_instance_uid": self.series_instance_uid,
            "patient_info": self.patient_info,
            "study_info": self.study_info,
            "series_info": self.series_info,
            "dicom_results": [r.to_dict() for r in self.dicom_results],
            "total_anomalies": self.total_anomalies,
            "anomaly_distribution": self.anomaly_distribution,
            "avg_quality": self.avg_quality,
            "critical_findings": [f.to_dict() for f in self.critical_findings],
            "overall_summary": self.overall_summary,
            "created_at": self.created_at,
            "analysis_source": self.analysis_source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeriesAnalysisResult":
        """Create from dictionary."""
        dicom_results = [
            DicomAnalysisResult.from_dict(r) for r in data.get("dicom_results", [])
        ]
        critical_findings = [
            AnomalyFinding.from_dict(f) for f in data.get("critical_findings", [])
        ]
        return cls(
            analysis_id=data.get("analysis_id", str(uuid4())),
            study_instance_uid=data.get("study_instance_uid", ""),
            series_instance_uid=data.get("series_instance_uid", ""),
            patient_info=data.get("patient_info", {}),
            study_info=data.get("study_info", {}),
            series_info=data.get("series_info", {}),
            dicom_results=dicom_results,
            total_anomalies=data.get("total_anomalies", 0),
            anomaly_distribution=data.get("anomaly_distribution", {}),
            avg_quality=data.get("avg_quality", 0.0),
            critical_findings=critical_findings,
            overall_summary=data.get("overall_summary", ""),
            created_at=data.get("created_at", ""),
            analysis_source=data.get("analysis_source", "directory"),
        )


def generate_analysis_id() -> str:
    """Generate a unique analysis ID."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"dicom_analysis_{timestamp}_{uuid4().hex[:8]}"


def calculate_series_statistics(results: List[DicomAnalysisResult]) -> Dict[str, Any]:
    """Calculate aggregate statistics for a list of DICOM results."""
    if not results:
        return {
            "total_dicoms": 0,
            "total_anomalies": 0,
            "avg_quality": 0.0,
            "anomaly_distribution": {},
            "critical_count": 0,
            "diagnostic_quality_count": 0,
        }

    total_anomalies = sum(r.anomaly_count for r in results)
    avg_quality = round(sum(r.quality.overall for r in results) / len(results), 2)

    distribution = {s.to_label(): 0 for s in Severity}
    critical_count = 0
    for result in results:
        for anomaly in result.anomalies:
            label = anomaly.severity.to_label()
            distribution[label] = distribution.get(label, 0) + 1
            if anomaly.severity >= Severity.SEVERE:
                critical_count += 1

    diagnostic_count = sum(1 for r in results if r.quality.is_diagnostic())

    return {
        "total_dicoms": len(results),
        "total_anomalies": total_anomalies,
        "avg_quality": avg_quality,
        "anomaly_distribution": distribution,
        "critical_count": critical_count,
        "diagnostic_quality_count": diagnostic_count,
    }
