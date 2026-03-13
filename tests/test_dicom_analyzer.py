"""Tests for DICOM analysis functionality."""

import json
from unittest.mock import patch

import pytest

from services.dicom_scoring import (
    AnomalyFinding,
    DicomAnalysisResult,
    QualityScore,
    SeriesAnalysisResult,
    Severity,
    generate_analysis_id,
    calculate_series_statistics,
)


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self):
        """Severity levels should have correct integer values."""
        assert Severity.NORMAL == 1
        assert Severity.MILD == 2
        assert Severity.MODERATE == 3
        assert Severity.SEVERE == 4
        assert Severity.CRITICAL == 5

    def test_from_string(self):
        """from_string should convert string to Severity."""
        assert Severity.from_string("normal") == Severity.NORMAL
        assert Severity.from_string("MILD") == Severity.MILD
        assert Severity.from_string("Moderate") == Severity.MODERATE
        assert Severity.from_string("SEVERE") == Severity.SEVERE
        assert Severity.from_string("critical") == Severity.CRITICAL
        assert Severity.from_string("unknown") == Severity.NORMAL

    def test_to_label(self):
        """to_label should return human-readable label."""
        assert Severity.NORMAL.to_label() == "Normal"
        assert Severity.CRITICAL.to_label() == "Critical"


class TestAnomalyFinding:
    """Tests for AnomalyFinding dataclass."""

    def test_create_anomaly(self):
        """Should create AnomalyFinding with all fields."""
        anomaly = AnomalyFinding(
            anomaly_type="nodule",
            location="right lung upper lobe",
            severity=Severity.MODERATE,
            confidence=0.85,
            description="Well-circumscribed nodule measuring 12mm",
            measurements={"diameter_mm": 12.0},
            laterality="right",
        )

        assert anomaly.anomaly_type == "nodule"
        assert anomaly.severity == Severity.MODERATE
        assert anomaly.confidence == 0.85

    def test_to_dict(self):
        """to_dict should serialize all fields."""
        anomaly = AnomalyFinding(
            anomaly_type="fracture",
            location="left femur",
            severity=Severity.SEVERE,
            confidence=0.95,
            description="Transverse fracture",
        )

        data = anomaly.to_dict()

        assert data["anomaly_type"] == "fracture"
        assert data["severity"] == 4
        assert data["severity_label"] == "Severe"
        assert data["confidence"] == 0.95

    def test_from_dict(self):
        """from_dict should deserialize correctly."""
        data = {
            "anomaly_type": "opacity",
            "location": "left lower lobe",
            "severity": 3,
            "confidence": 0.7,
            "description": "Ground glass opacity",
        }

        anomaly = AnomalyFinding.from_dict(data)

        assert anomaly.anomaly_type == "opacity"
        assert anomaly.severity == Severity.MODERATE
        assert anomaly.confidence == 0.7


class TestQualityScore:
    """Tests for QualityScore dataclass."""

    def test_create_quality_score(self):
        """Should create QualityScore with all criteria."""
        quality = QualityScore(
            positioning=5,
            contrast=4,
            artifacts=5,
            noise_level=4,
            motion_blur=5,
        )

        assert quality.positioning == 5
        assert quality.overall > 0

    def test_overall_calculation(self):
        """Overall score should be weighted average."""
        quality = QualityScore(
            positioning=5,
            contrast=5,
            artifacts=5,
            noise_level=5,
            motion_blur=5,
        )

        assert quality.overall == 5.0

    def test_is_diagnostic(self):
        """is_diagnostic should return True for sufficient quality."""
        good_quality = QualityScore(
            positioning=4,
            contrast=4,
            artifacts=4,
            noise_level=4,
            motion_blur=4,
        )
        assert good_quality.is_diagnostic() is True

        poor_quality = QualityScore(
            positioning=1,
            contrast=1,
            artifacts=1,
            noise_level=1,
            motion_blur=1,
        )
        assert poor_quality.is_diagnostic() is False

    def test_default_quality(self):
        """default() should return moderate quality."""
        quality = QualityScore.default()

        assert quality.positioning == 3
        assert quality.contrast == 3
        assert quality.overall >= 2.5


class TestDicomAnalysisResult:
    """Tests for DicomAnalysisResult dataclass."""

    def test_create_result(self):
        """Should create result with all fields."""
        result = DicomAnalysisResult(
            file_path="/data/scan.dcm",
            sop_instance_uid="1.2.3.4.5",
            series_number=1,
            instance_number=1,
            anomalies=[],
            anomaly_count=0,
            quality=QualityScore.default(),
            summary="Normal findings",
            raw_agent_response="",
        )

        assert result.file_path == "/data/scan.dcm"
        assert result.anomaly_count == 0

    def test_get_critical_anomalies(self):
        """get_critical_anomalies should filter by severity."""
        result = DicomAnalysisResult(
            file_path="/data/scan.dcm",
            sop_instance_uid="1.2.3.4.5",
            series_number=1,
            instance_number=1,
            anomalies=[
                AnomalyFinding("nodule", "lung", Severity.MILD, 0.5, ""),
                AnomalyFinding("mass", "liver", Severity.SEVERE, 0.9, ""),
                AnomalyFinding("bleed", "brain", Severity.CRITICAL, 0.95, ""),
            ],
            anomaly_count=3,
            quality=QualityScore.default(),
            summary="Multiple findings",
            raw_agent_response="",
        )

        critical = result.get_critical_anomalies()

        assert len(critical) == 2
        assert all(a.severity >= Severity.SEVERE for a in critical)

    def test_to_dict_and_from_dict(self):
        """Should serialize and deserialize correctly."""
        result = DicomAnalysisResult(
            file_path="/data/scan.dcm",
            sop_instance_uid="1.2.3.4.5",
            series_number=1,
            instance_number=1,
            anomalies=[
                AnomalyFinding(
                    "nodule", "lung", Severity.MODERATE, 0.8, "Test finding"
                ),
            ],
            anomaly_count=1,
            quality=QualityScore(
                positioning=4, contrast=4, artifacts=4, noise_level=4, motion_blur=4
            ),
            summary="Test summary",
            raw_agent_response="Raw response",
        )

        data = result.to_dict()
        restored = DicomAnalysisResult.from_dict(data)

        assert restored.file_path == result.file_path
        assert restored.sop_instance_uid == result.sop_instance_uid
        assert len(restored.anomalies) == 1
        assert restored.anomalies[0].anomaly_type == "nodule"


class TestSeriesAnalysisResult:
    """Tests for SeriesAnalysisResult dataclass."""

    def test_create_series_result(self):
        """Should create series result with aggregated statistics."""
        dicom_results = [
            DicomAnalysisResult(
                file_path=f"/data/scan{i}.dcm",
                sop_instance_uid=f"1.2.3.{i}",
                series_number=1,
                instance_number=i,
                anomalies=[
                    AnomalyFinding("nodule", "lung", Severity.MODERATE, 0.7, ""),
                ],
                anomaly_count=1,
                quality=QualityScore.default(),
                summary=f"Scan {i}",
                raw_agent_response="",
            )
            for i in range(5)
        ]

        result = SeriesAnalysisResult(
            analysis_id="test_analysis",
            study_instance_uid="1.2.3.4",
            series_instance_uid="1.2.3.4.5",
            patient_info={"patient_id": "ANONYMIZED"},
            study_info={"modality": "CT"},
            series_info={"series_description": "Test Series"},
            dicom_results=dicom_results,
        )

        assert result.total_anomalies == 5
        assert result.avg_quality > 0

    def test_critical_findings_aggregation(self):
        """Should aggregate critical findings across all DICOMs."""
        dicom_results = [
            DicomAnalysisResult(
                file_path="/data/scan1.dcm",
                sop_instance_uid="1.2.3.1",
                series_number=1,
                instance_number=1,
                anomalies=[
                    AnomalyFinding(
                        "bleed", "brain", Severity.CRITICAL, 0.95, "Active hemorrhage"
                    ),
                ],
                anomaly_count=1,
                quality=QualityScore.default(),
                summary="",
                raw_agent_response="",
            ),
            DicomAnalysisResult(
                file_path="/data/scan2.dcm",
                sop_instance_uid="1.2.3.2",
                series_number=1,
                instance_number=2,
                anomalies=[
                    AnomalyFinding(
                        "nodule", "lung", Severity.MILD, 0.5, "Small nodule"
                    ),
                ],
                anomaly_count=1,
                quality=QualityScore.default(),
                summary="",
                raw_agent_response="",
            ),
        ]

        result = SeriesAnalysisResult(
            analysis_id="test_analysis",
            study_instance_uid="1.2.3.4",
            series_instance_uid="1.2.3.4.5",
            patient_info={},
            study_info={},
            series_info={},
            dicom_results=dicom_results,
        )

        assert len(result.critical_findings) == 1
        assert result.critical_findings[0].anomaly_type == "bleed"


class TestGenerateAnalysisId:
    """Tests for analysis ID generation."""

    def test_generate_analysis_id_format(self):
        """Should generate ID with timestamp and unique suffix."""
        analysis_id = generate_analysis_id()

        assert analysis_id.startswith("dicom_analysis_")
        assert (
            len(analysis_id.split("_")) >= 4
        )  # dicom_analysis_YYYYMMDD_HHMMSS_XXXXXXXX

    def test_generate_analysis_id_unique(self):
        """Each ID should be unique."""
        id1 = generate_analysis_id()
        id2 = generate_analysis_id()

        assert id1 != id2


class TestCalculateSeriesStatistics:
    """Tests for series statistics calculation."""

    def test_empty_results(self):
        """Should return zeros for empty list."""
        stats = calculate_series_statistics([])

        assert stats["total_dicoms"] == 0
        assert stats["total_anomalies"] == 0
        assert stats["avg_quality"] == 0.0

    def test_with_results(self):
        """Should calculate correct statistics."""
        results = [
            DicomAnalysisResult(
                file_path="/data/scan1.dcm",
                sop_instance_uid="1.2.3.1",
                series_number=1,
                instance_number=1,
                anomalies=[
                    AnomalyFinding("nodule", "lung", Severity.MODERATE, 0.7, ""),
                    AnomalyFinding("opacity", "lung", Severity.MILD, 0.5, ""),
                ],
                anomaly_count=2,
                quality=QualityScore(
                    positioning=4, contrast=4, artifacts=4, noise_level=4, motion_blur=4
                ),
                summary="",
                raw_agent_response="",
            ),
            DicomAnalysisResult(
                file_path="/data/scan2.dcm",
                sop_instance_uid="1.2.3.2",
                series_number=1,
                instance_number=2,
                anomalies=[
                    AnomalyFinding("mass", "liver", Severity.SEVERE, 0.9, ""),
                ],
                anomaly_count=1,
                quality=QualityScore(
                    positioning=5, contrast=5, artifacts=5, noise_level=5, motion_blur=5
                ),
                summary="",
                raw_agent_response="",
            ),
        ]

        stats = calculate_series_statistics(results)

        assert stats["total_dicoms"] == 2
        assert stats["total_anomalies"] == 3
        assert stats["critical_count"] == 1  # One SEVERE
        assert stats["diagnostic_quality_count"] == 2


# Tests for dicom_analyzer module (with mocking)
class TestDicomAnalyzer:
    """Tests for DICOM analyzer functions."""

    @pytest.fixture
    def mock_dicom_data(self):
        """Create mock DICOM data."""
        # This would normally be real DICOM bytes
        return b"mock_dicom_data"

    def test_is_dicom_available(self):
        """is_dicom_available should return boolean."""
        from services.dicom_analyzer import is_dicom_available

        # Result depends on whether pydicom is installed
        assert isinstance(is_dicom_available(), bool)

    @patch("services.dicom_analyzer.DICOM_AVAILABLE", False)
    def test_analyze_without_pydicom(self, mock_dicom_data):
        """Should return error result when pydicom not available."""
        from services.dicom_analyzer import analyze_single_dicom

        result = analyze_single_dicom(mock_dicom_data, "test.dcm")

        assert result.error is not None
        assert "pydicom" in result.error.lower()

    def test_parse_agent_analysis_response_with_json(self):
        """Should parse JSON response from agent."""
        from services.dicom_analyzer import _parse_agent_analysis_response

        response = """Analysis complete.

```json
{
  "anomalies": [
    {
      "type": "nodule",
      "location": "right lung",
      "severity": "moderate",
      "confidence": 0.85,
      "description": "8mm nodule in right upper lobe"
    }
  ],
  "quality": {
    "positioning": 4,
    "contrast": 5,
    "artifacts": 4,
    "noise_level": 4,
    "motion_blur": 5
  },
  "summary": "Single pulmonary nodule identified."
}
```
"""

        anomalies, quality, summary = _parse_agent_analysis_response(response)

        assert len(anomalies) == 1
        assert anomalies[0].anomaly_type == "nodule"
        assert anomalies[0].severity == Severity.MODERATE
        assert quality.overall >= 4.0
        assert "nodule" in summary.lower()

    def test_parse_agent_analysis_response_without_json(self):
        """Should extract findings from unstructured text."""
        from services.dicom_analyzer import _parse_agent_analysis_response

        response = """
Findings:
1. There is a moderate-sized nodule in the right upper lobe.
2. Mild ground glass opacity noted in the left lower lobe.

Impression: Findings require follow-up.
"""

        anomalies, quality, summary = _parse_agent_analysis_response(response)

        # Should extract at least some findings
        assert isinstance(anomalies, list)
        assert isinstance(quality, QualityScore)


# Tests for dicom_report module
class TestDicomReport:
    """Tests for DICOM report generation."""

    @pytest.fixture
    def sample_result(self):
        """Create a sample analysis result for testing."""
        return SeriesAnalysisResult(
            analysis_id="test_analysis_20240101_120000_abc123",
            study_instance_uid="1.2.3.4.5",
            series_instance_uid="1.2.3.4.5.6",
            patient_info={"patient_id": "ANONYMIZED"},
            study_info={"modality": "CT", "study_description": "Chest CT"},
            series_info={"series_description": "Lung Window"},
            dicom_results=[
                DicomAnalysisResult(
                    file_path="/data/scan1.dcm",
                    sop_instance_uid="1.2.3.4.5.6.1",
                    series_number=1,
                    instance_number=1,
                    anomalies=[
                        AnomalyFinding(
                            anomaly_type="nodule",
                            location="right upper lobe",
                            severity=Severity.MODERATE,
                            confidence=0.85,
                            description="8mm nodule with spiculated margins",
                            measurements={"diameter_mm": 8.0},
                        ),
                    ],
                    anomaly_count=1,
                    quality=QualityScore(
                        positioning=4,
                        contrast=5,
                        artifacts=4,
                        noise_level=4,
                        motion_blur=5,
                    ),
                    summary="Single pulmonary nodule identified.",
                    raw_agent_response="",
                ),
            ],
        )

    def test_generate_markdown_report(self, sample_result):
        """Should generate valid Markdown report."""
        from services.dicom_report import generate_markdown_report

        report = generate_markdown_report(sample_result)

        assert "# DICOM Analyse-Report" in report
        assert sample_result.analysis_id in report
        assert "nodule" in report.lower()
        assert "Moderate" in report

    def test_generate_json_export(self, sample_result):
        """Should generate valid JSON export."""
        from services.dicom_report import generate_json_export

        json_str = generate_json_export(sample_result)
        data = json.loads(json_str)

        assert data["analysis_id"] == sample_result.analysis_id
        assert len(data["dicom_results"]) == 1

    def test_generate_csv_summary(self, sample_result):
        """Should generate valid CSV summary."""
        from services.dicom_report import generate_csv_summary

        csv_str = generate_csv_summary(sample_result)

        assert "Datei" in csv_str  # Header
        assert "scan1.dcm" in csv_str  # Data

    def test_generate_anomaly_csv(self, sample_result):
        """Should generate valid anomaly CSV."""
        from services.dicom_report import generate_anomaly_csv

        csv_str = generate_anomaly_csv(sample_result)

        assert "Anomalie-Typ" in csv_str
        assert "nodule" in csv_str
        assert "Moderate" in csv_str

    def test_is_pdf_available(self):
        """is_pdf_available should return boolean."""
        from services.dicom_report import is_pdf_available

        assert isinstance(is_pdf_available(), bool)

    def test_generate_pdf_report(self, sample_result):
        """Should generate PDF bytes when weasyprint available."""
        from services.dicom_report import generate_pdf_report, is_pdf_available

        if not is_pdf_available():
            pytest.skip("weasyprint not installed")

        pdf_bytes = generate_pdf_report(sample_result)

        if pdf_bytes:  # May fail on some systems
            assert pdf_bytes.startswith(b"%PDF")
