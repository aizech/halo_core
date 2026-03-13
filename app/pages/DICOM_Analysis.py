"""DICOM Analysis page for medical imaging AI analysis.

Provides comprehensive analysis of DICOM series with anomaly detection,
severity scoring, and quality assessment.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from app import main
from services import parsers
from services.dicom_analyzer import (
    analyze_dicom_series,
    analyze_uploaded_dicoms,
    is_dicom_available,
    save_analysis_result,
)
from services.dicom_scoring import (
    SeriesAnalysisResult,
    Severity,
)
from services.dicom_report import (
    generate_markdown_report,
    generate_json_export,
    generate_csv_summary,
    generate_pdf_report,
    is_pdf_available,
)

_LOGGER = logging.getLogger(__name__)


def render():
    """Render the DICOM Analysis page."""
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("DICOM Analyse")
    st.markdown(
        "KI-gestützte Analyse medizinischer Bilddaten mit Anomalie-Erkennung, "
        "Schweregrad-Bewertung und Qualitätsassessment."
    )

    # Check DICOM availability
    if not is_dicom_available():
        st.error(
            ":material/warning: DICOM-Verarbeitung nicht verfügbar. "
            "Bitte installiere `pydicom`: `pip install pydicom`"
        )
        st.stop()

    # Initialize session state
    if "dicom_analysis_result" not in st.session_state:
        st.session_state.dicom_analysis_result = None
    if "dicom_analysis_running" not in st.session_state:
        st.session_state.dicom_analysis_running = False
    if "dicom_analysis_stop" not in st.session_state:
        st.session_state.dicom_analysis_stop = False

    # Tabs for different input methods
    tab1, tab2, tab3 = st.tabs(
        [
            ":material/folder: Verzeichnis",
            ":material/upload: Upload",
            ":material/local_hospital: PACS",
        ]
    )

    with tab1:
        _render_directory_tab()

    with tab2:
        _render_upload_tab()

    with tab3:
        _render_pacs_tab()

    # Show results if available
    if st.session_state.dicom_analysis_result:
        st.divider()
        _render_analysis_results(st.session_state.dicom_analysis_result)


def _render_directory_tab():
    """Render directory picker tab."""
    st.subheader("DICOM-Verzeichnis analysieren")

    st.markdown("""
        Wähle ein Verzeichnis mit DICOM-Dateien. Die Analyse wird automatisch 
        alle DICOM-Dateien im Verzeichnis (inkl. Unterordner) erkennen und analysieren.
        """)

    # Directory path input
    default_path = ""
    if "dicom_dir_path" in st.session_state:
        default_path = st.session_state.dicom_dir_path

    dir_path = st.text_input(
        "Verzeichnispfad",
        value=default_path,
        placeholder="z.B. C:\\Daten\\MRI_Series",
        help="Absoluter Pfad zum Verzeichnis mit DICOM-Dateien",
    )

    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        anonymize = st.checkbox(
            "Vor Analyse anonymisieren",
            value=True,
            help="Entfernt Patientendaten vor der KI-Analyse",
        )
    with col2:
        save_results = st.checkbox(
            "Ergebnisse speichern",
            value=True,
            help="Speichert Analyseergebnisse in data/dicom_analyses/",
        )

    # Preview directory
    if dir_path and Path(dir_path).exists():
        st.session_state.dicom_dir_path = dir_path
        _preview_directory(Path(dir_path))
    elif dir_path:
        st.warning(f"Verzeichnis nicht gefunden: {dir_path}")

    # Analyze button
    if st.button(
        ":material/search: Analyse starten",
        type="primary",
        disabled=not dir_path or not Path(dir_path).exists(),
        key="analyze_dir_btn",
    ):
        _run_directory_analysis(Path(dir_path), anonymize, save_results)


def _render_upload_tab():
    """Render file upload tab."""
    st.subheader("DICOM-Dateien hochladen")

    st.markdown("""
        Lade einzelne oder mehrere DICOM-Dateien hoch. Die Analyse wird 
        jede Datei einzeln untersuchen und die Ergebnisse aggregieren.
        """)

    uploaded_files = st.file_uploader(
        "DICOM-Dateien (.dcm, .dicom oder ohne Erweiterung)",
        type=["dcm", "dicom"],
        accept_multiple_files=True,
        help="Lade eine oder mehrere DICOM-Dateien hoch. "
        "Dateien ohne Erweiterung werden automatisch erkannt.",
    )

    # Analysis options
    col1, col2 = st.columns(2)
    with col1:
        anonymize = st.checkbox(
            "Vor Analyse anonymisieren",
            value=True,
            help="Entfernt Patientendaten vor der KI-Analyse",
            key="upload_anonymize",
        )
    with col2:
        save_results = st.checkbox(
            "Ergebnisse speichern",
            value=True,
            help="Speichert Analyseergebnisse in data/dicom_analyses/",
            key="upload_save",
        )

    # Preview files
    if uploaded_files:
        _preview_uploaded_files(uploaded_files)

    # Analyze button
    if st.button(
        ":material/search: Analyse starten",
        type="primary",
        disabled=not uploaded_files,
        key="analyze_upload_btn",
    ):
        _run_upload_analysis(uploaded_files, anonymize, save_results)


def _render_pacs_tab():
    """Render PACS query tab."""
    st.subheader("PACS-Abfrage")

    st.markdown("""
        Suche nach Studien auf einem PACS-Server und analysiere die 
        abgerufenen DICOM-Serien.
        
        **Hinweis:** PACS-Verbindung muss in der Configuration konfiguriert sein
        (`DICOM_PACS_HOST`, `DICOM_PACS_PORT`, `DICOM_PACS_AE_TITLE`).
        """)

    # Check PACS configuration
    from services.settings import get_settings

    settings = get_settings()
    pacs_configured = all(
        [
            settings.dicom_pacs_host,
            settings.dicom_pacs_port,
            settings.dicom_pacs_ae_title,
        ]
    )

    if not pacs_configured:
        st.warning(
            ":material/warning: PACS nicht konfiguriert. Bitte setze die Umgebungsvariablen "
            "`DICOM_PACS_HOST`, `DICOM_PACS_PORT` und `DICOM_PACS_AE_TITLE`."
        )
        return

    st.success(
        f":material/check_circle: PACS konfiguriert: {settings.dicom_pacs_host}:{settings.dicom_pacs_port}"
    )

    # Query form
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Patienten-ID", placeholder="z.B. PAT001")
        st.text_input("Patientenname", placeholder="z.B. Mustermann")
    with col2:
        st.date_input("Studien-Datum", value=None)
        st.selectbox(
            "Modalität",
            options=["Alle", "CT", "MR", "US", "XA", "CR", "DX", "PT"],
            index=0,
        )

    if st.button(
        ":material/search: PACS durchsuchen", type="primary", key="search_pacs_btn"
    ):
        st.info("PACS-Suche wird implementiert... (Phase 3)")
        # TODO: Implement PACS query in Phase 3


def _preview_directory(directory: Path):
    """Preview DICOM files in directory."""
    from services.dicom_analyzer import _get_dicom_files_from_directory

    try:
        dicom_files = _get_dicom_files_from_directory(directory)
        if dicom_files:
            st.info(f":material/folder: **{len(dicom_files)}** DICOM-Dateien gefunden")

            # Show first few files
            with st.expander("Dateien anzeigen", expanded=False):
                for f in dicom_files[:10]:
                    st.text(f.name)
                if len(dicom_files) > 10:
                    st.text(f"... und {len(dicom_files) - 10} weitere")
        else:
            st.warning("Keine DICOM-Dateien im Verzeichnis gefunden")
    except Exception as e:
        st.error(f"Fehler beim Lesen des Verzeichnisses: {e}")


def _preview_uploaded_files(uploaded_files: List):
    """Preview uploaded DICOM files."""
    st.info(
        f":material/upload: **{len(uploaded_files)}** Dateien zum Analysieren bereit"
    )

    valid_count = 0
    for f in uploaded_files:
        data = f.read()
        f.seek(0)
        if parsers.is_dicom_file(data):
            valid_count += 1

    if valid_count != len(uploaded_files):
        st.warning(
            f":material/warning: {len(uploaded_files) - valid_count} Dateien sind keine gültigen DICOM-Dateien"
        )


def _run_directory_analysis(directory: Path, anonymize: bool, save_results: bool):
    """Run analysis on directory."""
    from services.settings import get_settings

    st.session_state.dicom_analysis_running = True
    st.session_state.dicom_analysis_stop = False

    progress_bar = st.progress(0, text="Initialisiere Analyse...")
    stop_container = st.empty()

    # Show stop button
    with stop_container.container():
        if st.button(
            ":material/stop: Analyse stoppen",
            type="secondary",
            key="stop_dir_analysis_btn",
        ):
            st.session_state.dicom_analysis_stop = True
            st.info("Stoppe Analyse...")

    def progress_callback(current: int, total: int, filename: str):
        progress = current / total
        progress_bar.progress(
            progress, text=f"Analysiere: {filename} ({current}/{total})"
        )
        # Check for stop request
        if st.session_state.get("dicom_analysis_stop", False):
            raise InterruptedError("Analyse durch Benutzer abgebrochen")

    try:
        # Create agent runner function
        agent_runner = _create_agent_runner()

        # Run analysis
        result = analyze_dicom_series(
            directory=directory,
            agent_run_func=agent_runner,
            anonymize=anonymize,
            progress_callback=progress_callback,
        )

        progress_bar.progress(1.0, text="Analyse abgeschlossen!")
        stop_container.empty()

        # Save results if requested
        if save_results:
            settings = get_settings()
            output_dir = Path(settings.data_dir) / "dicom_analyses"
            saved_path = save_analysis_result(result, output_dir)
            st.toast(f"Ergebnisse gespeichert: {saved_path.name}")

        # Store in session state
        st.session_state.dicom_analysis_result = result
        st.session_state.dicom_analysis_running = False

        st.rerun()

    except InterruptedError as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.dicom_analysis_running = False
        st.session_state.dicom_analysis_stop = False
        st.warning(str(e))
    except Exception as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.dicom_analysis_running = False
        st.error(f"Analyse fehlgeschlagen: {e}")
        _LOGGER.error("DICOM analysis failed: %s", e)


def _run_upload_analysis(uploaded_files: List, anonymize: bool, save_results: bool):
    """Run analysis on uploaded files."""
    from services.settings import get_settings

    st.session_state.dicom_analysis_running = True
    st.session_state.dicom_analysis_stop = False

    progress_bar = st.progress(0, text="Initialisiere Analyse...")
    stop_container = st.empty()

    # Show stop button
    with stop_container.container():
        if st.button(
            ":material/stop: Analyse stoppen",
            type="secondary",
            key="stop_upload_analysis_btn",
        ):
            st.session_state.dicom_analysis_stop = True
            st.info("Stoppe Analyse...")

    def progress_callback(current: int, total: int, filename: str):
        progress = current / total
        progress_bar.progress(
            progress, text=f"Analysiere: {filename} ({current}/{total})"
        )
        # Check for stop request
        if st.session_state.get("dicom_analysis_stop", False):
            raise InterruptedError("Analyse durch Benutzer abgebrochen")

    # Prepare files
    files_data = []
    for f in uploaded_files:
        data = f.read()
        f.seek(0)
        if parsers.is_dicom_file(data):
            files_data.append((f.name, data))

    if not files_data:
        progress_bar.empty()
        stop_container.empty()
        st.error("Keine gültigen DICOM-Dateien gefunden")
        st.session_state.dicom_analysis_running = False
        return

    try:
        # Create agent runner function
        agent_runner = _create_agent_runner()

        # Run analysis
        result = analyze_uploaded_dicoms(
            files=files_data,
            agent_run_func=agent_runner,
            anonymize=anonymize,
            progress_callback=progress_callback,
        )

        progress_bar.progress(1.0, text="Analyse abgeschlossen!")
        stop_container.empty()

        # Save results if requested
        if save_results:
            settings = get_settings()
            output_dir = Path(settings.data_dir) / "dicom_analyses"
            saved_path = save_analysis_result(result, output_dir)
            st.toast(f"Ergebnisse gespeichert: {saved_path.name}")

        # Store in session state
        st.session_state.dicom_analysis_result = result
        st.session_state.dicom_analysis_running = False

        st.rerun()

    except InterruptedError as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.dicom_analysis_running = False
        st.session_state.dicom_analysis_stop = False
        st.warning(str(e))
    except Exception as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.dicom_analysis_running = False
        st.error(f"Analyse fehlgeschlagen: {e}")
        _LOGGER.error("DICOM analysis failed: %s", e)


def _create_agent_runner():
    """Create a function to run AI agent analysis on DICOM images."""

    def run_agent_analysis(image_bytes: bytes, metadata: Dict[str, Any]) -> str:
        """Run AI analysis on a DICOM image.

        Args:
            image_bytes: PNG/JPEG image bytes converted from DICOM
            metadata: DICOM metadata for context

        Returns:
            Analysis text from the agent
        """
        from agno.media import Image
        from services.agents import _build_agent_from_config
        from services.agents_config import load_agent_configs

        # Load medical imaging agent config
        configs = load_agent_configs()
        config = configs.get("medical_imaging")
        if not config:
            _LOGGER.warning("medical_imaging agent not found, using default")
            return "Medical imaging agent not configured"

        # Create agent from config
        agent = _build_agent_from_config(config)
        if not agent:
            return "Failed to create medical imaging agent"

        # Build analysis prompt
        modality = metadata.get("modality", "Unknown")
        rows = metadata.get("rows", 0)
        cols = metadata.get("columns", 0)

        prompt = f"""Analysiere dieses medizinische Bild.

**Bildinformationen:**
- Modalität: {modality}
- Auflösung: {rows}x{cols} Pixel
- Datei: {metadata.get('file_path', 'Unknown')}

**Analyseanforderungen:**
1. Identifiziere alle Anomalien oder Auffälligkeiten
2. Bewerte den Schweregrad jeder Anomalie (Normal/Mild/Moderate/Severe/Critical)
3. Gib die anatomische Lage an
4. Bewerte die Bildqualität (Positionierung, Kontrast, Artefakte, Rauschen)

**Ausgabeformat (JSON):**
```json
{{
  "anomalies": [
    {{
      "type": "anomaly_type",
      "location": "anatomical_location",
      "severity": "mild|moderate|severe|critical",
      "confidence": 0.0-1.0,
      "description": "detailed description",
      "measurements": {{}}
    }}
  ],
  "quality": {{
    "positioning": 1-5,
    "contrast": 1-5,
    "artifacts": 1-5,
    "noise_level": 1-5,
    "motion_blur": 1-5
  }},
  "summary": "Brief summary of findings"
}}
```

Falls keine Anomalien gefunden werden, gib ein leeres `anomalies`-Array zurück.
"""

        try:
            # Create image object from bytes
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = Path(tmp.name)

            try:
                image = Image(filepath=str(tmp_path))

                # Run agent with image
                result = agent.run(prompt, images=[image])

                # Extract response content
                if hasattr(result, "content"):
                    return result.content
                return str(result)
            finally:
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            _LOGGER.error("Agent analysis failed: %s", e)
            return f"Analysis error: {e}"

    return run_agent_analysis


def _render_analysis_results(result: SeriesAnalysisResult):
    """Render analysis results with drill-down."""
    st.header("Analyse-Ergebnisse")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("DICOM-Dateien", len(result.dicom_results))
    col2.metric("Gesamt-Anomalien", result.total_anomalies)
    col3.metric("Ø Qualität", f"{result.avg_quality:.1f}/5")
    col4.metric("Kritische Befunde", len(result.critical_findings))

    # Severity distribution
    st.subheader("Schweregrad-Verteilung")
    severity_cols = st.columns(5)
    severity_labels = ["Normal", "Mild", "Moderate", "Severe", "Critical"]
    severity_colors = ["green", "lightgreen", "yellow", "orange", "red"]

    for i, (label, color) in enumerate(zip(severity_labels, severity_colors)):
        count = result.anomaly_distribution.get(label, 0)
        severity_cols[i].metric(label, count)

    # Critical findings alert
    if result.critical_findings:
        st.error(
            f":material/warning: **{len(result.critical_findings)}** kritische Befunde erfordern sofortige Aufmerksamkeit!"
        )
        with st.expander("Kritische Befunde anzeigen", expanded=True):
            for finding in result.critical_findings:
                st.markdown(
                    f"- **{finding.anomaly_type}** in {finding.location}: {finding.description}"
                )

    # Series info
    if result.study_info or result.series_info:
        st.subheader("Studien-Informationen")
        col1, col2 = st.columns(2)
        with col1:
            if result.study_info:
                st.markdown(f"""
                - **Studie:** {result.study_info.get('study_description', 'N/A')}
                - **Modalität:** {result.study_info.get('modality', 'N/A')}
                """)
        with col2:
            if result.series_info:
                st.markdown(f"""
                - **Serie:** {result.series_info.get('series_description', 'N/A')}
                - **Serien-Nr.:** {result.series_info.get('series_number', 'N/A')}
                """)

    # Per-DICOM results
    st.subheader("Einzelne DICOM-Analysen")

    for dicom_result in result.dicom_results:
        with st.expander(
            f":material/description: {Path(dicom_result.file_path).name} - {dicom_result.anomaly_count} Anomalien",
            expanded=dicom_result.anomaly_count > 0,
        ):
            if dicom_result.error:
                st.error(f"Fehler: {dicom_result.error}")
                continue

            # Quality scores
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Qualitätsbewertung:**")
                quality = dicom_result.quality
                st.markdown(f"""
                - Positionierung: {quality.positioning}/5
                - Kontrast: {quality.contrast}/5
                - Artefakte: {quality.artifacts}/5
                - Rauschen: {quality.noise_level}/5
                - Bewegungsunschärfe: {quality.motion_blur}/5
                - **Gesamt:** {quality.overall:.1f}/5
                """)
                if quality.is_diagnostic():
                    st.success(":material/check_circle: Diagnostische Qualität")
                else:
                    st.warning(
                        ":material/warning: Eingeschränkte diagnostische Qualität"
                    )

            with col2:
                if dicom_result.anomalies:
                    st.markdown("**Anomalien:**")
                    for anomaly in dicom_result.anomalies:
                        severity_color = {
                            Severity.NORMAL: "🟢",
                            Severity.MILD: "🟡",
                            Severity.MODERATE: "🟠",
                            Severity.SEVERE: "🔴",
                            Severity.CRITICAL: "🚨",
                        }.get(anomaly.severity, ":material/help:")
                        st.markdown(f"""
                        {severity_color} **{anomaly.anomaly_type}** ({anomaly.severity.to_label()})
                        - Ort: {anomaly.location}
                        - Konfidenz: {anomaly.confidence:.0%}
                        - {anomaly.description}
                        """)
                else:
                    st.info("Keine Anomalien gefunden")

            # Summary
            if dicom_result.summary:
                st.markdown("**Zusammenfassung:**")
                st.markdown(dicom_result.summary)

    # Export section
    st.subheader("Export")
    _render_export_section(result)


def _render_export_section(result: SeriesAnalysisResult):
    """Render export options."""
    from services import storage

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # JSON export
        json_data = generate_json_export(result)
        st.download_button(
            ":material/data_object: JSON-Export",
            data=json_data,
            file_name=f"{result.analysis_id}.json",
            mime="application/json",
            key="export_json_btn",
        )

    with col2:
        # Markdown report
        md_report = generate_markdown_report(result)
        st.download_button(
            ":material/description: Markdown-Report",
            data=md_report,
            file_name=f"{result.analysis_id}.md",
            mime="text/markdown",
            key="export_md_btn",
        )

    with col3:
        # CSV summary
        csv_data = generate_csv_summary(result)
        st.download_button(
            ":material/table_chart: CSV-Zusammenfassung",
            data=csv_data,
            file_name=f"{result.analysis_id}_summary.csv",
            mime="text/csv",
            key="export_csv_btn",
        )

    with col4:
        # PDF export
        if is_pdf_available():
            pdf_bytes = generate_pdf_report(result)
            if pdf_bytes:
                st.download_button(
                    ":material/description: PDF-Report",
                    data=pdf_bytes,
                    file_name=f"{result.analysis_id}.pdf",
                    mime="application/pdf",
                    key="export_pdf_btn",
                )
            else:
                st.info("PDF-Generierung nicht verfügbar")
        else:
            st.info("PDF erfordert fpdf2")

    # Add to notes/sources section
    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
        if st.button(
            ":material/note_add: Als Notiz speichern",
            key="save_to_notes_btn",
            use_container_width=True,
        ):
            # Create note content from analysis
            note_content = generate_markdown_report(result)
            note = {
                "title": f"DICOM Analyse: {result.analysis_id}",
                "content": note_content,
                "sources": ["DICOM Analysis"],
                "created_at": result.created_at,
            }
            st.session_state.setdefault("notes", []).insert(0, note)
            storage.save_notes(st.session_state["notes"])
            st.toast("Analyse als Notiz gespeichert")

    with col6:
        if st.button(
            ":material/push_pin: Als Quelle hinzufügen",
            key="save_to_sources_btn",
            use_container_width=True,
        ):
            # Create source content
            source_content = generate_markdown_report(result)
            source_name = f"DICOM: {result.analysis_id[:20]}..."

            # Import SourceItem from main
            from app.main import SourceItem

            # Create source item
            source = SourceItem(
                name=source_name,
                type_label="DICOM Analysis",
                meta=f"{result.total_anomalies} Anomalien, {len(result.critical_findings)} kritisch",
            )

            # Add to sources in session state
            sources = st.session_state.setdefault("sources", [])
            sources.append(source)

            # Persist sources (convert dataclass to dict)
            storage.save_sources(
                [src.__dict__ if hasattr(src, "__dict__") else src for src in sources]
            )

            # Ingest for knowledge retrieval
            from services import ingestion

            ingestion.ingest_source_content(
                title=source_name,
                body=source_content,
                meta={
                    "type": "DICOM Analysis",
                    "analysis_id": result.analysis_id,
                    "source_id": source.id,
                },
            )

            st.toast("Analyse als Quelle hinzugefügt")

    # Reset button
    if st.button(":material/refresh: Neue Analyse", key="reset_analysis_btn"):
        st.session_state.dicom_analysis_result = None
        st.rerun()


if __name__ == "__main__":
    render()
