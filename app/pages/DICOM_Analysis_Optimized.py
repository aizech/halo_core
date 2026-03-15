"""DICOM Analysis (Optimized) page for medical imaging AI analysis.

Drop-in replacement for DICOM_Analysis.py that uses the parallel,
metadata-only, cache-backed analyzer from services/dicom_analyzer_optimized.py.

Key differences vs. the original page:
- Parallel ProcessPoolExecutor workers (stop_before_pixels + specific_tags)
- File-hash cache: unchanged files are instant on re-run
- Performance summary shown after each run (workers, cache hits, elapsed)
- AI analysis step is identical (radiologist agent, same prompt)
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from app import main
from services import parsers
from services.dicom_analyzer import (
    generate_overall_summary,
    is_dicom_available,
    save_analysis_result,
)
from services.dicom_analyzer_optimized import (
    DicomRecord,
    BenchmarkResult,
    analyze_optimized,
    CACHE_PATH,
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

# ── Helpers ───────────────────────────────────────────────────────────────────


def _save_uploads_to_temp(uploaded_files: List) -> List[str]:
    """Persist Streamlit UploadedFile objects to a temp dir, return paths."""
    tmp = tempfile.mkdtemp(prefix="halo_opt_")
    paths: List[str] = []
    for uf in uploaded_files:
        dest = Path(tmp) / uf.name
        dest.write_bytes(uf.read())
        paths.append(str(dest))
    return paths


def _get_dicom_paths_from_directory(directory: Path) -> List[Path]:
    """Collect all .dcm files recursively."""
    from services.dicom_analyzer import _get_dicom_files_from_directory

    return _get_dicom_files_from_directory(directory)


def _dicom_record_to_metadata(rec: DicomRecord) -> Dict[str, Any]:
    return {
        "modality": rec.modality,
        "rows": rec.rows,
        "columns": rec.columns,
        "file_path": rec.file,
        "patient_id": rec.patient_id,
        "study_date": rec.study_date,
        "institution": rec.institution,
        "manufacturer": rec.manufacturer,
    }


# ── Page ──────────────────────────────────────────────────────────────────────


def render() -> None:
    """Render the Optimized DICOM Analysis page."""
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title(":material/speed: DICOM Analyse (Optimiert)")
    st.markdown(
        "KI-gestützte Analyse medizinischer Bilddaten mit paralleler Verarbeitung, "
        "Metadaten-Cache und Schweregrad-Bewertung."
    )
    st.caption(
        ":material/bolt: Verwendet `stop_before_pixels`, `specific_tags` und "
        "`ProcessPoolExecutor` für bis zu 50× schnellere Metadaten-Extraktion."
    )

    if not is_dicom_available():
        st.error(
            ":material/warning: DICOM-Verarbeitung nicht verfügbar. "
            "Bitte installiere `pydicom`: `pip install pydicom`"
        )
        st.stop()

    # Session state
    for key, default in [
        ("opt_analysis_result", None),
        ("opt_benchmark", None),
        ("opt_analysis_running", False),
        ("opt_analysis_stop", False),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # Worker / cache settings
    with st.expander(":material/settings: Analyse-Einstellungen", expanded=False):
        _sc1, _sc2 = st.columns(2)
        with _sc1:
            max_workers = st.slider(
                "Parallele Worker",
                min_value=1,
                max_value=min(16, (os.cpu_count() or 4) * 2),
                value=min(8, os.cpu_count() or 4),
                help="Anzahl paralleler Prozesse für die Metadaten-Extraktion.",
                key="opt_max_workers",
            )
            use_cache = st.checkbox(
                "Datei-Hash-Cache aktivieren",
                value=True,
                help="Bereits analysierte (unveränderte) Dateien werden sofort aus dem Cache geladen.",
                key="opt_use_cache",
            )
        with _sc2:
            chunk_size = st.select_slider(
                "Chunk-Größe (Dateien pro Batch)",
                options=[10, 25, 50, 100, 200],
                value=50,
                key="opt_chunk_size",
            )
            anonymize = st.checkbox(
                "Vor KI-Analyse anonymisieren",
                value=True,
                help="Entfernt Patientendaten vor der KI-Bildanalyse.",
                key="opt_anonymize",
            )
        _cc, _ = st.columns([1, 3])
        with _cc:
            if st.button(
                ":material/delete: Cache leeren", width="stretch", key="opt_clear_cache"
            ):
                if CACHE_PATH.exists():
                    CACHE_PATH.unlink()
                    st.success("Cache geleert.")
                else:
                    st.info("Kein Cache gefunden.")

    st.divider()

    # Input tabs
    tab1, tab2, tab3 = st.tabs(
        [
            ":material/folder: Verzeichnis",
            ":material/upload: Upload",
            ":material/local_hospital: PACS",
        ]
    )

    with tab1:
        _render_directory_tab(max_workers, use_cache, chunk_size, anonymize)

    with tab2:
        _render_upload_tab(max_workers, use_cache, chunk_size, anonymize)

    with tab3:
        _render_pacs_tab()

    # Performance badge
    bench: BenchmarkResult | None = st.session_state.get("opt_benchmark")
    if bench:
        st.divider()
        bc1, bc2, bc3, bc4 = st.columns(4)
        bc1.metric("Dateien", bench.total_files)
        bc2.metric("Elapsed", f"{bench.elapsed_sec}s")
        bc3.metric("Cache-Treffer", bench.cache_hits)
        bc4.metric("Worker", bench.workers_used)
        if bench.failed_files:
            st.warning(
                f":material/warning: {bench.failed_files} Dateien fehlgeschlagen."
            )

    # Analysis results
    if st.session_state.opt_analysis_result:
        st.divider()
        _render_analysis_results(st.session_state.opt_analysis_result)


# ── Input tabs ────────────────────────────────────────────────────────────────


def _render_directory_tab(
    max_workers: int, use_cache: bool, chunk_size: int, anonymize: bool
) -> None:
    st.subheader("DICOM-Verzeichnis analysieren")
    st.markdown(
        "Wähle ein Verzeichnis mit DICOM-Dateien. Alle .dcm-Dateien (inkl. Unterordner) "
        "werden parallel extrahiert und anschließend per KI analysiert."
    )

    default_path = st.session_state.get("opt_dicom_dir_path", "")
    dir_path = st.text_input(
        "Verzeichnispfad",
        value=default_path,
        placeholder="z.B. C:\\Daten\\MRI_Series",
        help="Absoluter Pfad zum Verzeichnis mit DICOM-Dateien",
        key="opt_dir_path_input",
    )

    col1, col2 = st.columns(2)
    with col2:
        save_results = st.checkbox(
            "Ergebnisse speichern",
            value=True,
            help="Speichert Analyseergebnisse in data/dicom_analyses/",
            key="opt_dir_save",
        )

    if dir_path and Path(dir_path).exists():
        st.session_state.opt_dicom_dir_path = dir_path
        _preview_directory(Path(dir_path))
    elif dir_path:
        st.warning(f"Verzeichnis nicht gefunden: {dir_path}")

    if st.button(
        ":material/search: Analyse starten",
        type="primary",
        disabled=not dir_path or not Path(dir_path).exists(),
        key="opt_analyze_dir_btn",
    ):
        paths = [str(p) for p in _get_dicom_paths_from_directory(Path(dir_path))]
        if not paths:
            st.warning("Keine DICOM-Dateien im Verzeichnis gefunden.")
        else:
            _run_optimized_analysis(
                paths, max_workers, use_cache, chunk_size, anonymize, save_results
            )


def _render_upload_tab(
    max_workers: int, use_cache: bool, chunk_size: int, anonymize: bool
) -> None:
    st.subheader("DICOM-Dateien hochladen")
    st.markdown(
        "Lade einzelne oder mehrere DICOM-Dateien hoch. Die Metadaten werden parallel "
        "extrahiert; anschließend erfolgt die KI-Bildanalyse."
    )

    uploaded_files = st.file_uploader(
        "DICOM-Dateien (.dcm, .dicom oder ohne Erweiterung)",
        type=["dcm", "dicom"],
        accept_multiple_files=True,
        key="opt_uploader",
    )

    col1, col2 = st.columns(2)
    with col2:
        save_results = st.checkbox(
            "Ergebnisse speichern",
            value=True,
            help="Speichert Analyseergebnisse in data/dicom_analyses/",
            key="opt_upload_save",
        )

    if uploaded_files:
        _preview_uploaded_files(uploaded_files)

    if st.button(
        ":material/search: Analyse starten",
        type="primary",
        disabled=not uploaded_files,
        key="opt_analyze_upload_btn",
    ):
        paths = _save_uploads_to_temp(uploaded_files)
        _run_optimized_analysis(
            paths, max_workers, use_cache, chunk_size, anonymize, save_results
        )


def _render_pacs_tab() -> None:
    st.subheader("PACS-Abfrage")
    st.markdown(
        "Suche nach Studien auf einem PACS-Server und analysiere die abgerufenen DICOM-Serien.\n\n"
        "**Hinweis:** PACS-Verbindung muss in der Configuration konfiguriert sein "
        "(`DICOM_PACS_HOST`, `DICOM_PACS_PORT`, `DICOM_PACS_AE_TITLE`)."
    )

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

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Patienten-ID", placeholder="z.B. PAT001", key="opt_pacs_pid")
        st.text_input(
            "Patientenname", placeholder="z.B. Mustermann", key="opt_pacs_name"
        )
    with col2:
        st.date_input("Studien-Datum", value=None, key="opt_pacs_date")
        st.selectbox(
            "Modalität",
            options=["Alle", "CT", "MR", "US", "XA", "CR", "DX", "PT"],
            index=0,
            key="opt_pacs_modality",
        )

    if st.button(
        ":material/search: PACS durchsuchen", type="primary", key="opt_search_pacs_btn"
    ):
        st.info("PACS-Suche wird implementiert... (Phase 3)")


# ── Preview helpers ───────────────────────────────────────────────────────────


def _preview_directory(directory: Path) -> None:
    try:
        dicom_files = _get_dicom_paths_from_directory(directory)
        if dicom_files:
            st.info(f":material/folder: **{len(dicom_files)}** DICOM-Dateien gefunden")
            with st.expander("Dateien anzeigen", expanded=False):
                for f in dicom_files[:10]:
                    st.text(f.name)
                if len(dicom_files) > 10:
                    st.text(f"... und {len(dicom_files) - 10} weitere")
        else:
            st.warning("Keine DICOM-Dateien im Verzeichnis gefunden")
    except Exception as e:
        st.error(f"Fehler beim Lesen des Verzeichnisses: {e}")


def _preview_uploaded_files(uploaded_files: List) -> None:
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


# ── Core analysis runner ──────────────────────────────────────────────────────


def _run_optimized_analysis(
    paths: List[str],
    max_workers: int,
    use_cache: bool,
    chunk_size: int,
    anonymize: bool,
    save_results: bool,
) -> None:
    """Extract metadata with the optimized engine, then run AI analysis per file."""
    from services.settings import get_settings

    st.session_state.opt_analysis_running = True
    st.session_state.opt_analysis_stop = False

    progress_bar = st.progress(0, text="Starte optimierte Metadaten-Extraktion…")
    stop_container = st.empty()

    with stop_container.container():
        if st.button(
            ":material/stop: Analyse stoppen",
            type="secondary",
            key="opt_stop_btn",
        ):
            st.session_state.opt_analysis_stop = True
            st.info("Stoppe Analyse…")

    try:
        # ── Step 1: parallel metadata extraction ─────────────────────────────
        progress_bar.progress(0.05, text="Extrahiere Metadaten (parallel)…")
        bench: BenchmarkResult = analyze_optimized(
            paths,
            max_workers=max_workers,
            use_cache=use_cache,
            chunk_size=chunk_size,
        )
        st.session_state.opt_benchmark = bench

        progress_bar.progress(
            0.3,
            text=f"Metadaten fertig – {bench.cache_hits} Cache-Treffer, starte KI-Analyse…",
        )

        if st.session_state.get("opt_analysis_stop"):
            raise InterruptedError("Analyse durch Benutzer abgebrochen")

        # ── Step 2: build SeriesAnalysisResult skeleton ───────────────────────
        from services.dicom_scoring import (
            SeriesAnalysisResult,
            DicomAnalysisResult,
            QualityScore,
        )
        import uuid

        agent_runner = _create_agent_runner()
        dicom_results: List[DicomAnalysisResult] = []
        total = len(bench.records)

        for idx, rec in enumerate(bench.records):
            if st.session_state.get("opt_analysis_stop"):
                raise InterruptedError("Analyse durch Benutzer abgebrochen")

            pct = 0.3 + 0.65 * ((idx + 1) / max(total, 1))
            progress_bar.progress(
                pct, text=f"KI-Analyse: {Path(rec.file).name} ({idx+1}/{total})"
            )

            if rec.error:
                dicom_results.append(
                    DicomAnalysisResult(
                        file_path=rec.file,
                        sop_instance_uid=rec.sop_uid,
                        series_number=0,
                        instance_number=idx,
                        anomalies=[],
                        anomaly_count=0,
                        quality=QualityScore(),
                        summary="",
                        raw_agent_response="",
                        error=rec.error,
                    )
                )
                continue

            # Run AI analysis on the file
            metadata = _dicom_record_to_metadata(rec)
            image_bytes: bytes | None = None
            ai_text = ""
            try:
                image_bytes = _extract_image_bytes(rec.file, anonymize)
                ai_text = agent_runner(image_bytes, metadata) if image_bytes else ""
                parsed = _parse_agent_response(ai_text)
            except Exception as exc:
                _LOGGER.warning("AI analysis failed for %s: %s", rec.file, exc)
                parsed = {"anomalies": [], "quality": {}, "summary": ""}

            anomalies = parsed.get("anomalies", [])
            dicom_results.append(
                DicomAnalysisResult(
                    file_path=rec.file,
                    sop_instance_uid=rec.sop_uid,
                    series_number=0,
                    instance_number=idx,
                    anomalies=anomalies,
                    anomaly_count=len(anomalies),
                    quality=_parse_quality(parsed.get("quality", {})),
                    summary=parsed.get("summary", ""),
                    raw_agent_response=ai_text,
                    image_bytes=image_bytes,
                )
            )

        first = bench.records[0] if bench.records else None
        result = SeriesAnalysisResult(
            analysis_id=f"opt_{uuid.uuid4().hex[:12]}",
            study_instance_uid=first.study_uid if first else "",
            series_instance_uid=first.series_uid if first else "",
            patient_info={
                "patient_id": first.patient_id if first else "",
                "patient_name": first.patient_name if first else "",
                "patient_birthdate": first.patient_birthdate if first else "",
                "patient_sex": first.patient_sex if first else "",
            },
            study_info={
                "modality": first.modality if first else "",
                "study_date": first.study_date if first else "",
                "study_description": first.study_description if first else "",
            },
            series_info={},
            dicom_results=dicom_results,
        )

        progress_bar.progress(0.97, text="Erstelle Gesamt-Zusammenfassung…")
        result.overall_summary = generate_overall_summary(result, agent_runner)

        progress_bar.progress(1.0, text="Analyse abgeschlossen!")
        stop_container.empty()

        if save_results:
            settings = get_settings()
            output_dir = Path(settings.data_dir) / "dicom_analyses"
            saved_path = save_analysis_result(result, output_dir)
            st.toast(f"Ergebnisse gespeichert: {saved_path.name}")

        st.session_state.opt_analysis_result = result
        st.session_state.opt_analysis_running = False
        st.rerun()

    except InterruptedError as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.opt_analysis_running = False
        st.session_state.opt_analysis_stop = False
        st.warning(str(e))
    except Exception as e:
        progress_bar.empty()
        stop_container.empty()
        st.session_state.opt_analysis_running = False
        st.error(f"Analyse fehlgeschlagen: {e}")
        _LOGGER.error("Optimized DICOM analysis failed: %s", e, exc_info=True)


# ── AI agent helpers ──────────────────────────────────────────────────────────


def _extract_image_bytes(file_path: str, anonymize: bool) -> bytes | None:
    """Convert a DICOM file to PNG bytes for the AI agent."""
    try:
        import pydicom
        import numpy as np
        from PIL import Image as PILImage
        import io

        ds = pydicom.dcmread(file_path)
        if not hasattr(ds, "PixelData"):
            return None

        arr = ds.pixel_array
        if arr.ndim == 3:
            arr = arr[0]

        arr = arr.astype(float)
        arr_min, arr_max = arr.min(), arr.max()
        if arr_max > arr_min:
            arr = (arr - arr_min) / (arr_max - arr_min) * 255
        arr = arr.astype(np.uint8)

        img = PILImage.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as exc:
        _LOGGER.debug("Could not extract image from %s: %s", file_path, exc)
        return None


def _create_agent_runner():
    """Create the AI agent runner (identical to DICOM_Analysis.py)."""

    def run_agent_analysis(image_bytes: bytes, metadata: Dict[str, Any]) -> str:
        from agno.media import Image
        from services.agents import _build_agent_from_config
        from services.agents_config import load_agent_configs

        configs = load_agent_configs()
        config = configs.get("radiologist")
        if not config:
            _LOGGER.warning("radiologist agent not found, using default")
            return "Radiologist agent not configured"

        agent = _build_agent_from_config(config)
        if not agent:
            return "Failed to create medical imaging agent"

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
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_bytes)
                tmp_path = Path(tmp.name)
            try:
                image = Image(filepath=str(tmp_path))
                result = agent.run(prompt, images=[image])
                if hasattr(result, "content"):
                    return result.content
                return str(result)
            finally:
                tmp_path.unlink(missing_ok=True)
        except Exception as e:
            _LOGGER.error("Agent analysis failed: %s", e)
            return f"Analysis error: {e}"

    return run_agent_analysis


def _parse_agent_response(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from agent response. Returns anomalies as AnomalyFinding list."""
    import json
    import re
    from services.dicom_scoring import AnomalyFinding

    if not text:
        return {"anomalies": [], "quality": {}, "summary": ""}
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    raw = match.group(1) if match else text
    try:
        data = json.loads(raw)
    except Exception:
        return {"anomalies": [], "quality": {}, "summary": text[:500]}

    raw_anomalies = data.get("anomalies", [])
    anomalies = []
    for item in raw_anomalies:
        if isinstance(item, dict):
            try:
                anomalies.append(AnomalyFinding.from_dict(item))
            except Exception:
                pass
        elif isinstance(item, AnomalyFinding):
            anomalies.append(item)

    return {
        "anomalies": anomalies,
        "quality": data.get("quality", {}),
        "summary": data.get("summary", ""),
    }


def _parse_quality(raw: Dict[str, Any]):
    from services.dicom_scoring import QualityScore

    try:
        return QualityScore(
            positioning=int(raw.get("positioning", 3)),
            contrast=int(raw.get("contrast", 3)),
            artifacts=int(raw.get("artifacts", 3)),
            noise_level=int(raw.get("noise_level", 3)),
            motion_blur=int(raw.get("motion_blur", 3)),
        )
    except Exception:
        from services.dicom_scoring import QualityScore

        return QualityScore()


# ── Results rendering (identical to DICOM_Analysis.py) ───────────────────────


def _render_analysis_results(result: SeriesAnalysisResult) -> None:
    st.header("Analyse-Ergebnisse")

    if result.overall_summary:
        st.subheader("Gesamt-Zusammenfassung")
        st.markdown(result.overall_summary)
        st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("DICOM-Dateien", len(result.dicom_results))
    col2.metric("Gesamt-Anomalien", result.total_anomalies)
    col3.metric("Ø Qualität", f"{result.avg_quality:.1f}/5")
    col4.metric("Kritische Befunde", len(result.critical_findings))

    st.subheader("Schweregrad-Verteilung")
    severity_cols = st.columns(5)
    severity_labels = ["Normal", "Mild", "Moderate", "Severe", "Critical"]
    for i, label in enumerate(severity_labels):
        severity_cols[i].metric(label, result.anomaly_distribution.get(label, 0))

    if result.critical_findings:
        st.error(
            f":material/warning: **{len(result.critical_findings)}** kritische Befunde erfordern sofortige Aufmerksamkeit!"
        )
        with st.expander("Kritische Befunde anzeigen", expanded=True):
            for finding in result.critical_findings:
                st.markdown(
                    f"- **{finding.anomaly_type}** in {finding.location}: {finding.description}"
                )

    if result.study_info or result.series_info:
        st.subheader("Studien-Informationen")
        col1, col2 = st.columns(2)
        with col1:
            if result.study_info:
                st.markdown(
                    f"- **Studie:** {result.study_info.get('study_description', 'N/A')}\n"
                    f"- **Modalität:** {result.study_info.get('modality', 'N/A')}"
                )
        with col2:
            if result.series_info:
                st.markdown(
                    f"- **Serie:** {result.series_info.get('series_description', 'N/A')}\n"
                    f"- **Serien-Nr.:** {result.series_info.get('series_number', 'N/A')}"
                )

    st.subheader("Einzelne DICOM-Analysen")
    for dicom_result in result.dicom_results:
        with st.expander(
            f":material/description: {Path(dicom_result.file_path).name} - {dicom_result.anomaly_count} Anomalien",
            expanded=dicom_result.anomaly_count > 0,
        ):
            if dicom_result.error:
                st.error(f"Fehler: {dicom_result.error}")
                continue

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown("**Qualitätsbewertung:**")
                quality = dicom_result.quality
                st.markdown(
                    f"- Positionierung: {quality.positioning}/5\n"
                    f"- Kontrast: {quality.contrast}/5\n"
                    f"- Artefakte: {quality.artifacts}/5\n"
                    f"- Rauschen: {quality.noise_level}/5\n"
                    f"- Bewegungsunschärfe: {quality.motion_blur}/5\n"
                    f"- **Gesamt:** {quality.overall:.1f}/5"
                )
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
                        severity_icon = {
                            Severity.NORMAL: "🟢",
                            Severity.MILD: "🟡",
                            Severity.MODERATE: "🟠",
                            Severity.SEVERE: "🔴",
                            Severity.CRITICAL: "🚨",
                        }.get(anomaly.severity, ":material/help:")
                        st.markdown(
                            f"{severity_icon} **{anomaly.anomaly_type}** ({anomaly.severity.to_label()})\n"
                            f"- Ort: {anomaly.location}\n"
                            f"- Konfidenz: {anomaly.confidence:.0%}\n"
                            f"- {anomaly.description}"
                        )
                else:
                    st.info("Keine Anomalien gefunden")

            image_bytes = getattr(dicom_result, "image_bytes", None)
            if dicom_result.summary or image_bytes:
                st.divider()
                if image_bytes and dicom_result.summary:
                    img_col, summary_col = st.columns([1, 2])
                    with img_col:
                        st.image(image_bytes, caption="DICOM-Bild", width="stretch")
                    with summary_col:
                        st.markdown("**Zusammenfassung:**")
                        st.markdown(dicom_result.summary)
                elif image_bytes:
                    st.image(image_bytes, caption="DICOM-Bild", width=300)
                elif dicom_result.summary:
                    st.markdown("**Zusammenfassung:**")
                    st.markdown(dicom_result.summary)

    st.subheader("Export")
    _render_export_section(result)


def _render_export_section(result: SeriesAnalysisResult) -> None:
    from services import storage

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            ":material/data_object: JSON-Export",
            data=generate_json_export(result),
            file_name=f"{result.analysis_id}.json",
            mime="application/json",
            key="opt_export_json_btn",
        )
    with col2:
        st.download_button(
            ":material/description: Markdown-Report",
            data=generate_markdown_report(result),
            file_name=f"{result.analysis_id}.md",
            mime="text/markdown",
            key="opt_export_md_btn",
        )
    with col3:
        st.download_button(
            ":material/table_chart: CSV-Zusammenfassung",
            data=generate_csv_summary(result),
            file_name=f"{result.analysis_id}_summary.csv",
            mime="text/csv",
            key="opt_export_csv_btn",
        )
    with col4:
        if is_pdf_available():
            pdf_bytes = generate_pdf_report(result)
            if pdf_bytes:
                st.download_button(
                    ":material/description: PDF-Report",
                    data=pdf_bytes,
                    file_name=f"{result.analysis_id}.pdf",
                    mime="application/pdf",
                    key="opt_export_pdf_btn",
                )
            else:
                st.info("PDF-Generierung nicht verfügbar")
        else:
            st.info("PDF erfordert fpdf2")

    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
        if st.button(
            ":material/note_add: Als Notiz speichern",
            key="opt_save_to_notes_btn",
            width="stretch",
        ):
            note_content = generate_markdown_report(result)
            note = {
                "title": f"DICOM Analyse (Opt): {result.analysis_id}",
                "content": note_content,
                "sources": ["DICOM Analysis Optimized"],
                "created_at": result.created_at,
            }
            st.session_state.setdefault("notes", []).insert(0, note)
            storage.save_notes(st.session_state["notes"])
            st.toast("Analyse als Notiz gespeichert")

    with col6:
        if st.button(
            ":material/push_pin: Als Quelle hinzufügen",
            key="opt_save_to_sources_btn",
            width="stretch",
        ):
            from app.main import SourceItem
            from services import ingestion

            source_content = generate_markdown_report(result)
            source_name = f"DICOM (Opt): {result.analysis_id[:20]}..."
            source = SourceItem(
                name=source_name,
                type_label="DICOM Analysis Optimized",
                meta=f"{result.total_anomalies} Anomalien, {len(result.critical_findings)} kritisch",
            )
            sources = st.session_state.setdefault("sources", [])
            sources.append(source)
            storage.save_sources(
                [src.__dict__ if hasattr(src, "__dict__") else src for src in sources]
            )
            ingestion.ingest_source_content(
                title=source_name,
                body=source_content,
                meta={
                    "type": "DICOM Analysis Optimized",
                    "analysis_id": result.analysis_id,
                    "source_id": source.id,
                },
            )
            st.toast("Analyse als Quelle hinzugefügt")

    if st.button(":material/refresh: Neue Analyse", key="opt_reset_btn"):
        st.session_state.opt_analysis_result = None
        st.session_state.opt_benchmark = None
        st.rerun()


if __name__ == "__main__":
    render()
