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
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    _logger.debug("weasyprint not available - PDF generation disabled")


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
    """Generate PDF report from analysis result.

    Requires weasyprint to be installed.

    Args:
        result: Analysis result to report
        include_raw_responses: Include raw AI responses

    Returns:
        PDF bytes or None if PDF generation unavailable
    """
    if not PDF_AVAILABLE:
        _logger.warning("PDF generation unavailable - weasyprint not installed")
        return None

    # Generate HTML from markdown-like content
    html_content = _generate_html_report(result, include_raw_responses)

    # CSS styling
    css_content = """
    @page {
        size: A4;
        margin: 2cm;
    }
    
    body {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.4;
        color: #333;
    }
    
    h1 {
        color: #1a5276;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
    
    h2 {
        color: #2874a6;
        margin-top: 20px;
    }
    
    h3 {
        color: #1a5276;
    }
    
    h4 {
        color: #5d6d7e;
    }
    
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
    }
    
    th, td {
        border: 1px solid #bdc3c7;
        padding: 8px;
        text-align: left;
    }
    
    th {
        background-color: #eaf2f8;
        font-weight: bold;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .critical {
        background-color: #f5b7b1;
        padding: 10px;
        border-left: 4px solid #e74c3c;
        margin: 10px 0;
    }
    
    .quality-good {
        color: #27ae60;
    }
    
    .quality-warning {
        color: #e67e22;
    }
    
    .severity-normal { color: #27ae60; }
    .severity-mild { color: #f1c40f; }
    .severity-moderate { color: #e67e22; }
    .severity-severe { color: #e74c3c; }
    .severity-critical { color: #c0392b; font-weight: bold; }
    
    code, pre {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 10pt;
    }
    
    pre {
        padding: 10px;
        overflow-x: auto;
    }
    
    .metric-box {
        display: inline-block;
        background-color: #eaf2f8;
        padding: 10px 20px;
        margin: 5px;
        border-radius: 5px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 24pt;
        font-weight: bold;
        color: #1a5276;
    }
    
    .metric-label {
        font-size: 9pt;
        color: #5d6d7e;
    }
    """

    try:
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        css = CSS(string=css_content, font_config=font_config)

        pdf_bytes = html.write_pdf(stylesheets=[css], font_config=font_config)
        return pdf_bytes

    except Exception as e:
        _logger.error("PDF generation failed: %s", e)
        return None


def _generate_html_report(
    result: SeriesAnalysisResult,
    include_raw_responses: bool = False,
) -> str:
    """Generate HTML content for PDF report."""
    lines: List[str] = []

    # HTML header
    lines.extend(
        [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            f"<title>DICOM Analyse-Report - {result.analysis_id}</title>",
            "</head>",
            "<body>",
            "",
            "<h1>DICOM Analyse-Report</h1>",
            "",
            "<p>",
            f"<strong>Analyse-ID:</strong> {result.analysis_id}<br>",
            f"<strong>Erstellt:</strong> {_format_datetime(result.created_at)}<br>",
            f"<strong>Quelle:</strong> {result.analysis_source}",
            "</p>",
            "",
        ]
    )

    # Metrics boxes
    lines.extend(
        [
            "<h2>Übersicht</h2>",
            "",
            "<div class='metrics'>",
            f"<div class='metric-box'><div class='metric-value'>{len(result.dicom_results)}</div><div class='metric-label'>DICOM-Dateien</div></div>",
            f"<div class='metric-box'><div class='metric-value'>{result.total_anomalies}</div><div class='metric-label'>Anomalien</div></div>",
            f"<div class='metric-box'><div class='metric-value'>{result.avg_quality:.1f}</div><div class='metric-label'>Ø Qualität</div></div>",
            f"<div class='metric-box'><div class='metric-value'>{len(result.critical_findings)}</div><div class='metric-label'>Kritisch</div></div>",
            "</div>",
            "",
        ]
    )

    # Critical findings
    if result.critical_findings:
        lines.extend(
            [
                "<div class='critical'>",
                "<h3>⚠️ Kritische Befunde</h3>",
                "<ul>",
            ]
        )
        for finding in result.critical_findings:
            lines.append(
                f"<li><strong>{finding.anomaly_type}</strong> in {finding.location}: {finding.description}</li>"
            )
        lines.extend(
            [
                "</ul>",
                "</div>",
                "",
            ]
        )

    # Severity distribution table
    lines.extend(
        [
            "<h2>Schweregrad-Verteilung</h2>",
            "",
            "<table>",
            "<tr><th>Schweregrad</th><th>Anzahl</th></tr>",
        ]
    )

    for severity in Severity:
        label = severity.to_label()
        count = result.anomaly_distribution.get(label, 0)
        css_class = f"severity-{label.lower()}"
        lines.append(f"<tr><td class='{css_class}'>{label}</td><td>{count}</td></tr>")

    lines.extend(
        [
            "</table>",
            "",
        ]
    )

    # Detailed results
    lines.extend(
        [
            "<h2>Detailergebnisse</h2>",
            "",
        ]
    )

    for i, dicom_result in enumerate(result.dicom_results, 1):
        filename = Path(dicom_result.file_path).name

        lines.extend(
            [
                f"<h3>{i}. {filename}</h3>",
                "",
            ]
        )

        if dicom_result.error:
            lines.extend(
                [
                    f"<p class='severity-critical'>Fehler: {dicom_result.error}</p>",
                    "",
                ]
            )
            continue

        # Quality
        quality = dicom_result.quality
        quality_class = "quality-good" if quality.is_diagnostic() else "quality-warning"

        lines.extend(
            [
                "<h4>Qualitätsbewertung</h4>",
                f"<p class='{quality_class}'>Gesamt: {quality.overall:.1f}/5</p>",
                "<table>",
                "<tr><th>Kriterium</th><th>Bewertung</th></tr>",
                f"<tr><td>Positionierung</td><td>{quality.positioning}/5</td></tr>",
                f"<tr><td>Kontrast</td><td>{quality.contrast}/5</td></tr>",
                f"<tr><td>Artefakte</td><td>{quality.artifacts}/5</td></tr>",
                f"<tr><td>Rauschen</td><td>{quality.noise_level}/5</td></tr>",
                f"<tr><td>Bewegungsunschärfe</td><td>{quality.motion_blur}/5</td></tr>",
                "</table>",
                "",
            ]
        )

        # Anomalies
        if dicom_result.anomalies:
            lines.extend(
                [
                    "<h4>Anomalien</h4>",
                    "<table>",
                    "<tr><th>Typ</th><th>Ort</th><th>Schweregrad</th><th>Konfidenz</th></tr>",
                ]
            )

            for a in dicom_result.anomalies:
                css_class = f"severity-{a.severity.to_label().lower()}"
                lines.append(
                    f"<tr><td>{a.anomaly_type}</td><td>{a.location}</td>"
                    f"<td class='{css_class}'>{a.severity.to_label()}</td>"
                    f"<td>{a.confidence:.0%}</td></tr>"
                )

            lines.extend(
                [
                    "</table>",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "<p>Keine Anomalien gefunden.</p>",
                    "",
                ]
            )

        # Summary
        if dicom_result.summary:
            lines.extend(
                [
                    "<h4>Zusammenfassung</h4>",
                    f"<p>{dicom_result.summary}</p>",
                    "",
                ]
            )

    # Footer
    lines.extend(
        [
            "<hr>",
            f"<p><em>Report generiert von HALO Core am {_format_datetime(datetime.now().isoformat())}</em></p>",
            "</body>",
            "</html>",
        ]
    )

    return "\n".join(lines)


def _format_datetime(iso_string: str) -> str:
    """Format ISO datetime string for display."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return iso_string


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
