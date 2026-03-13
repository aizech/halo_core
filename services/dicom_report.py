"""DICOM analysis report generation.

Provides functions to generate reports in Markdown, JSON, and PDF formats
from DICOM analysis results.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from services.dicom_scoring import (
    SeriesAnalysisResult,
    Severity,
)

_logger = logging.getLogger(__name__)

# PDF generation is optional
try:
    from fpdf import FPDF

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    _logger.debug("fpdf not available - PDF generation disabled")


def is_pdf_available() -> bool:
    """Check if PDF generation is available."""
    return PDF_AVAILABLE


def generate_markdown_report(
    result: SeriesAnalysisResult,
    include_raw_responses: bool = False,
) -> str:
    """Generate a detailed Markdown report.

    Args:
        result: Analysis result to report
        include_raw_responses: Include raw AI responses in appendix

    Returns:
        Markdown formatted report string
    """
    lines: List[str] = []

    # Header
    lines.extend(
        [
            "# DICOM Analyse-Report",
            "",
            f"**Analyse-ID:** {result.analysis_id}",
            f"**Erstellt:** {_format_datetime(result.created_at)}",
            f"**Quelle:** {result.analysis_source}",
            "",
        ]
    )

    # Executive Summary
    lines.extend(
        [
            "## Zusammenfassung",
            "",
            f"Diese Analyse umfasst **{len(result.dicom_results)}** DICOM-Dateien "
            f"mit insgesamt **{result.total_anomalies}** erkannten Anomalien.",
            "",
        ]
    )

    # Critical findings alert
    if result.critical_findings:
        lines.extend(
            [
                "### ⚠️ Kritische Befunde",
                "",
                f"**{len(result.critical_findings)}** Befunde erfordern sofortige Aufmerksamkeit:",
                "",
            ]
        )
        for finding in result.critical_findings:
            lines.append(
                f"- **{finding.anomaly_type}** in {finding.location}: {finding.description}"
            )
        lines.append("")

    # Metrics table
    lines.extend(
        [
            "## Metriken",
            "",
            "| Metrik | Wert |",
            "|--------|------|",
            f"| DICOM-Dateien | {len(result.dicom_results)} |",
            f"| Gesamt-Anomalien | {result.total_anomalies} |",
            f"| Durchschn. Qualität | {result.avg_quality:.1f}/5 |",
            f"| Kritische Befunde | {len(result.critical_findings)} |",
            "",
        ]
    )

    # Severity distribution
    lines.extend(
        [
            "## Schweregrad-Verteilung",
            "",
            "| Schweregrad | Anzahl |",
            "|-------------|--------|",
        ]
    )

    severity_colors = {
        "Normal": "🟢",
        "Mild": "🟡",
        "Moderate": "🟠",
        "Severe": "🔴",
        "Critical": "🚨",
    }

    for severity in Severity:
        label = severity.to_label()
        count = result.anomaly_distribution.get(label, 0)
        color = severity_colors.get(label, "⚪")
        lines.append(f"| {color} {label} | {count} |")

    lines.append("")

    # Study/Series info
    if result.study_info or result.series_info:
        lines.extend(
            [
                "## Studien-Informationen",
                "",
            ]
        )

        if result.study_info:
            lines.extend(
                [
                    "### Studie",
                    "",
                    f"- **Beschreibung:** {result.study_info.get('study_description', 'N/A')}",
                    f"- **Modalität:** {result.study_info.get('modality', 'N/A')}",
                    "",
                ]
            )

        if result.series_info:
            lines.extend(
                [
                    "### Serie",
                    "",
                    f"- **Beschreibung:** {result.series_info.get('series_description', 'N/A')}",
                    f"- **Serien-Nr.:** {result.series_info.get('series_number', 'N/A')}",
                    "",
                ]
            )

    # Detailed results per DICOM
    lines.extend(
        [
            "## Detailergebnisse",
            "",
        ]
    )

    for i, dicom_result in enumerate(result.dicom_results, 1):
        filename = Path(dicom_result.file_path).name

        lines.extend(
            [
                f"### {i}. {filename}",
                "",
            ]
        )

        if dicom_result.error:
            lines.extend(
                [
                    f"**Fehler:** {dicom_result.error}",
                    "",
                ]
            )
            continue

        # Instance info
        lines.extend(
            [
                f"- **SOP Instance UID:** {dicom_result.sop_instance_uid}",
                f"- **Serien-Nr.:** {dicom_result.series_number}",
                f"- **Instanz-Nr.:** {dicom_result.instance_number}",
                "",
            ]
        )

        # Quality assessment
        quality = dicom_result.quality
        quality_status = (
            "✅ Diagnostische Qualität"
            if quality.is_diagnostic()
            else "⚠️ Eingeschränkte Qualität"
        )

        lines.extend(
            [
                "#### Qualitätsbewertung",
                "",
                f"**Gesamt:** {quality.overall:.1f}/5 - {quality_status}",
                "",
                "| Kriterium | Bewertung |",
                "|-----------|-----------|",
                f"| Positionierung | {quality.positioning}/5 |",
                f"| Kontrast | {quality.contrast}/5 |",
                f"| Artefakte | {quality.artifacts}/5 |",
                f"| Rauschen | {quality.noise_level}/5 |",
                f"| Bewegungsunschärfe | {quality.motion_blur}/5 |",
                "",
            ]
        )

        # Anomalies
        if dicom_result.anomalies:
            lines.extend(
                [
                    "#### Anomalien",
                    "",
                    "| Typ | Ort | Schweregrad | Konfidenz | Beschreibung |",
                    "|-----|-----|-------------|-----------|--------------|",
                ]
            )

            for a in dicom_result.anomalies:
                color = severity_colors.get(a.severity.to_label(), "")
                lines.append(
                    f"| {a.anomaly_type} | {a.location} | {color} {a.severity.to_label()} | "
                    f"{a.confidence:.0%} | {a.description[:50]}... |"
                )
            lines.append("")

        else:
            lines.extend(
                [
                    "#### Anomalien",
                    "",
                    "Keine Anomalien gefunden.",
                    "",
                ]
            )

        # Summary
        if dicom_result.summary:
            lines.extend(
                [
                    "#### Zusammenfassung",
                    "",
                    dicom_result.summary,
                    "",
                ]
            )

    # Appendix with raw responses
    if include_raw_responses:
        lines.extend(
            [
                "---",
                "",
                "## Anhang: Rohdaten der KI-Analyse",
                "",
            ]
        )

        for dicom_result in result.dicom_results:
            if dicom_result.raw_agent_response:
                filename = Path(dicom_result.file_path).name
                lines.extend(
                    [
                        f"### {filename}",
                        "",
                        "```",
                        dicom_result.raw_agent_response[:2000],
                        "```",
                        "",
                    ]
                )

    return "\n".join(lines)


def generate_json_export(result: SeriesAnalysisResult) -> str:
    """Generate JSON export of analysis result.

    Args:
        result: Analysis result to export

    Returns:
        JSON formatted string
    """
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


def generate_csv_summary(result: SeriesAnalysisResult) -> str:
    """Generate CSV summary of all DICOM results.

    Args:
        result: Analysis result to summarize

    Returns:
        CSV formatted string
    """
    import csv
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)

    # Header
    writer.writerow(
        [
            "Datei",
            "SOP Instance UID",
            "Serien-Nr.",
            "Instanz-Nr.",
            "Anomalien",
            "Qualität (Gesamt)",
            "Positionierung",
            "Kontrast",
            "Artefakte",
            "Rauschen",
            "Bewegung",
            "Diagnostisch",
            "Fehler",
        ]
    )

    # Data rows
    for r in result.dicom_results:
        writer.writerow(
            [
                Path(r.file_path).name,
                r.sop_instance_uid,
                r.series_number,
                r.instance_number,
                r.anomaly_count,
                f"{r.quality.overall:.1f}",
                r.quality.positioning,
                r.quality.contrast,
                r.quality.artifacts,
                r.quality.noise_level,
                r.quality.motion_blur,
                "Ja" if r.quality.is_diagnostic() else "Nein",
                r.error or "",
            ]
        )

    return buffer.getvalue()


def generate_anomaly_csv(result: SeriesAnalysisResult) -> str:
    """Generate CSV of all anomalies found.

    Args:
        result: Analysis result

    Returns:
        CSV formatted string with anomaly details
    """
    import csv
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer)

    # Header
    writer.writerow(
        [
            "Datei",
            "Anomalie-Typ",
            "Ort",
            "Schweregrad",
            "Konfidenz",
            "Beschreibung",
            "Lateralität",
            "Messungen",
        ]
    )

    # Data rows
    for r in result.dicom_results:
        for a in r.anomalies:
            measurements_str = json.dumps(a.measurements) if a.measurements else ""
            writer.writerow(
                [
                    Path(r.file_path).name,
                    a.anomaly_type,
                    a.location,
                    a.severity.to_label(),
                    f"{a.confidence:.2f}",
                    a.description,
                    a.laterality or "",
                    measurements_str,
                ]
            )

    return buffer.getvalue()


def generate_pdf_report(
    result: SeriesAnalysisResult,
    include_raw_responses: bool = False,
) -> Optional[bytes]:
    """Generate PDF report from analysis result using fpdf2.

    Pure Python solution - no system dependencies required.

    Args:
        result: Analysis result to report
        include_raw_responses: Include raw AI responses

    Returns:
        PDF bytes or None if PDF generation unavailable
    """
    if not PDF_AVAILABLE:
        _logger.warning("PDF generation unavailable - fpdf2 not installed")
        return None

    # A4 constants - explicit to avoid any dynamic margin drift
    _LM = 15  # left margin mm
    _RM = 15  # right margin mm
    _TM = 15  # top margin mm
    _CW = 180  # content width: A4 210mm - 2*15mm

    def _mc(pdf_obj: "FPDF", h: float, text: str) -> None:
        """Write wrapped text, always resetting X to left margin first."""
        safe = str(text).strip() if text else " "
        pdf_obj.set_x(_LM)
        pdf_obj.multi_cell(_CW, h, safe)

    try:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_margins(_LM, _TM, _RM)
        pdf.set_auto_page_break(auto=True, margin=_TM)

        # Use built-in font with Unicode character replacement
        pdf.set_font("helvetica", size=10)

        pdf.add_page()

        # Title
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, _clean_text("DICOM Analyse-Report"), ln=True, align="C")
        pdf.ln(5)

        # Metadata
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, f"Analyse-ID: {result.analysis_id}", ln=True)
        pdf.cell(0, 6, f"Erstellt: {_format_datetime(result.created_at)}", ln=True)
        pdf.cell(0, 6, f"Quelle: {result.analysis_source}", ln=True)
        pdf.ln(5)

        # Summary metrics
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Zusammenfassung", ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 6, f"DICOM-Dateien: {len(result.dicom_results)}", ln=True)
        pdf.cell(0, 6, f"Gesamt-Anomalien: {result.total_anomalies}", ln=True)
        pdf.cell(0, 6, f"Durchschn. Qualitat: {result.avg_quality:.1f}/5", ln=True)
        pdf.cell(0, 6, f"Kritische Befunde: {len(result.critical_findings)}", ln=True)
        pdf.ln(5)

        # Critical findings
        if result.critical_findings:
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(220, 20, 60)
            pdf.cell(0, 8, "Kritische Befunde", ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("helvetica", "", 10)
            for finding in result.critical_findings:
                text = f"- {finding.anomaly_type} in {finding.location}: {finding.description}"
                _mc(pdf, 6, _clean_text(text))
            pdf.ln(5)

        # Severity distribution
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Schweregrad-Verteilung", ln=True)
        pdf.set_font("helvetica", "", 10)
        for severity in Severity:
            label = severity.to_label()
            count = result.anomaly_distribution.get(label, 0)
            pdf.cell(0, 6, f"  {label}: {count}", ln=True)
        pdf.ln(5)

        # Per-file details
        pdf.add_page()
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Detailergebnisse", ln=True)
        pdf.ln(3)

        for i, dicom_result in enumerate(result.dicom_results, 1):
            filename = Path(dicom_result.file_path).name
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(0, 7, _clean_text(f"{i}. {filename}"), ln=True)

            if dicom_result.error:
                pdf.set_font("helvetica", "", 10)
                pdf.set_text_color(220, 20, 60)
                pdf.cell(0, 6, _clean_text(f"Fehler: {dicom_result.error}"), ln=True)
                pdf.set_text_color(0, 0, 0)
                continue

            # Quality
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(0, 6, "Qualitatsbewertung:", ln=True)
            pdf.set_font("helvetica", "", 10)
            quality = dicom_result.quality
            quality_text = f"Gesamt: {quality.overall:.1f}/5"
            if quality.is_diagnostic():
                pdf.set_text_color(0, 128, 0)
                quality_text += " (Diagnostisch)"
            else:
                pdf.set_text_color(255, 140, 0)
                quality_text += " (Eingeschrankt)"
            pdf.cell(0, 6, quality_text, ln=True)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 5, f"Positionierung: {quality.positioning}/5", ln=True)
            pdf.cell(0, 5, f"Kontrast: {quality.contrast}/5", ln=True)
            pdf.cell(0, 5, f"Artefakte: {quality.artifacts}/5", ln=True)
            pdf.cell(0, 5, f"Rauschen: {quality.noise_level}/5", ln=True)
            pdf.cell(0, 5, f"Bewegung: {quality.motion_blur}/5", ln=True)
            pdf.ln(3)

            # Anomalies
            if dicom_result.anomalies:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Anomalien:", ln=True)
                pdf.set_font("helvetica", "", 9)
                for a in dicom_result.anomalies:
                    severity_color = {
                        Severity.NORMAL: (0, 128, 0),
                        Severity.MILD: (0, 0, 255),
                        Severity.MODERATE: (255, 140, 0),
                        Severity.SEVERE: (255, 69, 0),
                        Severity.CRITICAL: (220, 20, 60),
                    }.get(a.severity, (0, 0, 0))
                    pdf.set_text_color(*severity_color)
                    # Anomaly type and severity
                    text1 = _clean_text(f"- {a.anomaly_type} ({a.severity.to_label()})")
                    _mc(pdf, 5, text1)
                    pdf.set_text_color(0, 0, 0)
                    # Location and confidence
                    text_loc = _clean_text(
                        f"  {a.location}, Konfidenz: {a.confidence:.0%}"
                    )
                    _mc(pdf, 5, text_loc)
                    # Description with proper wrapping
                    text2 = _clean_text(f"  {a.description}")
                    _mc(pdf, 5, text2)
                pdf.ln(3)

            # Summary
            if dicom_result.summary:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 6, "Zusammenfassung:", ln=True)
                pdf.set_font("helvetica", "", 10)
                _mc(pdf, 5, _clean_text(dicom_result.summary))
                pdf.ln(3)

            pdf.ln(5)

        # Footer
        pdf.ln(10)
        pdf.set_font("helvetica", "I", 8)
        pdf.cell(
            0,
            10,
            f"HALO Core - {_format_datetime(datetime.now().isoformat())}",
            align="C",
        )

        return bytes(pdf.output())

    except Exception as e:
        _logger.error("PDF generation failed: %s", e)
        return None


def _format_datetime(iso_string: str) -> str:
    """Format ISO datetime string for display."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_string


def _clean_text(text: str) -> str:
    """Replace Unicode characters with ASCII equivalents for PDF compatibility."""
    if not text:
        return text
    replacements = {
        "–": "-",  # en-dash
        "—": "-",  # em-dash
        """: '"',  # left double quote
        """: '"',  # right double quote
        "‘": "'",  # left single quote (U+2018)
        "'": "'",  # right single quote
        "…": "...",  # ellipsis
        "×": "x",  # multiplication sign
        "•": "-",  # bullet
        "°": " deg",  # degree
        "±": "+/-",  # plus-minus
        "µ": "u",  # micro
        "ä": "ae",  # German umlauts
        "ö": "oe",
        "ü": "ue",
        "Ä": "Ae",
        "Ö": "Oe",
        "Ü": "Ue",
        "ß": "ss",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-ASCII characters
    return text.encode("ascii", "replace").decode("ascii")


def save_report_files(
    result: SeriesAnalysisResult,
    output_dir: Path,
    formats: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """Save report files in multiple formats.

    Args:
        result: Analysis result
        output_dir: Directory to save files
        formats: List of formats to generate ('md', 'json', 'csv', 'pdf')

    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ["md", "json", "csv"]

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files: Dict[str, Path] = {}

    base_name = result.analysis_id

    # Markdown
    if "md" in formats:
        md_path = output_dir / f"{base_name}.md"
        md_path.write_text(generate_markdown_report(result), encoding="utf-8")
        saved_files["md"] = md_path

    # JSON
    if "json" in formats:
        json_path = output_dir / f"{base_name}.json"
        json_path.write_text(generate_json_export(result), encoding="utf-8")
        saved_files["json"] = json_path

    # CSV
    if "csv" in formats:
        csv_path = output_dir / f"{base_name}_summary.csv"
        csv_path.write_text(generate_csv_summary(result), encoding="utf-8")
        saved_files["csv"] = csv_path

        # Also save anomaly CSV
        anomaly_csv_path = output_dir / f"{base_name}_anomalies.csv"
        anomaly_csv_path.write_text(generate_anomaly_csv(result), encoding="utf-8")
        saved_files["csv_anomalies"] = anomaly_csv_path

    # PDF
    if "pdf" in formats and PDF_AVAILABLE:
        pdf_bytes = generate_pdf_report(result)
        if pdf_bytes:
            pdf_path = output_dir / f"{base_name}.pdf"
            pdf_path.write_bytes(pdf_bytes)
            saved_files["pdf"] = pdf_path

    return saved_files
