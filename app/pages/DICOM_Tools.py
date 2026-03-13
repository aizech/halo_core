"""DICOM Tools page for medical imaging anonymization."""

from __future__ import annotations

import io
from datetime import datetime

import streamlit as st

from app import main
from services import dicom_anonymizer, parsers


def render():
    """Render the DICOM Tools page."""
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()

    st.title("DICOM Tools")
    st.markdown(
        "Anonymisierung medizinischer Bilddaten (DICOM) für Datenschutz "
        "und Forschungszwecke."
    )

    st.header("DICOM-Dateien anonymisieren")

    st.markdown("""
        ### Was wird anonymisiert?
        
        Standardmäßig werden folgende HIPAA-Identifikatoren entfernt:
        - Patientendaten (Name, ID, Geburtsdatum, Geschlecht, Adresse)
        - Institutionsdaten (Name, Adresse)
        - Ärztedaten (Zuweisender Arzt, Durchführender Arzt)
        - Studien-/Serien-Metadaten (Study ID, Accession Number, Datum/Zeit)
        - DICOM UIDs (Study/Series/SOP Instance UIDs werden neu generiert)
        
        Private Tags werden ebenfalls entfernt.
        """)

    # Upload section
    st.subheader("Dateien hochladen")

    uploaded_files = st.file_uploader(
        "DICOM-Dateien (.dcm, .dicom oder ohne Erweiterung)",
        type=["dcm", "dicom"],
        accept_multiple_files=True,
        help="Lade eine oder mehrere DICOM-Dateien hoch. "
        "Dateien ohne Erweiterung werden automatisch erkannt.",
    )

    # Configuration options
    st.subheader("Anonymisierungsoptionen")

    col1, col2 = st.columns(2)

    with col1:
        regenerate_uids = st.checkbox(
            "UIDs neu generieren",
            value=True,
            help="Generiert neue Study/Series/SOP Instance UIDs",
        )
        remove_private_tags = st.checkbox(
            "Private Tags entfernen",
            value=True,
            help="Entfernt herstellerspezifische private DICOM-Tags",
        )

    with col2:
        # Tag selection
        st.markdown("**Zu anonymisierende Tags:**")
        anonymize_patient = st.checkbox("Patientendaten", value=True)
        anonymize_institution = st.checkbox("Institutionsdaten", value=True)
        anonymize_study = st.checkbox("Studiendaten", value=True)
        anonymize_dates = st.checkbox("Datumsangaben", value=True)

    # Build tag list based on selection
    tags_to_anonymize = []
    if anonymize_patient:
        tags_to_anonymize.extend(
            [
                "PatientName",
                "PatientID",
                "PatientBirthDate",
                "PatientSex",
                "PatientAge",
                "PatientAddress",
                "PatientWeight",
                "PatientTelephoneNumbers",
                "OtherPatientIDs",
                "OtherPatientNames",
                "EthnicGroup",
            ]
        )
    if anonymize_institution:
        tags_to_anonymize.extend(
            [
                "InstitutionName",
                "InstitutionAddress",
                "ReferringPhysicianName",
                "PhysiciansOfRecord",
                "PerformingPhysicianName",
                "OperatorsName",
            ]
        )
    if anonymize_study:
        tags_to_anonymize.extend(
            [
                "StudyID",
                "AccessionNumber",
            ]
        )
    if anonymize_dates:
        tags_to_anonymize.extend(
            [
                "StudyDate",
                "SeriesDate",
                "AcquisitionDate",
                "ContentDate",
                "StudyTime",
                "SeriesTime",
                "AcquisitionTime",
                "ContentTime",
            ]
        )

    # Preview section
    if uploaded_files:
        st.subheader("Vorschau der identifizierbaren Daten")

        preview_file = st.selectbox(
            "Datei für Vorschau auswählen",
            options=range(len(uploaded_files)),
            format_func=lambda i: uploaded_files[i].name,
        )

        if preview_file is not None:
            selected_file = uploaded_files[preview_file]
            data = selected_file.read()
            selected_file.seek(0)  # Reset for later use

            # Check if it's a DICOM file
            if parsers.is_dicom_file(data):
                identifiable = dicom_anonymizer.get_dicom_identifiable_fields(data)

                if "error" in identifiable:
                    st.error(f"Fehler beim Lesen: {identifiable['error']}")
                else:
                    st.markdown("**Gefundene identifizierbare Felder:**")
                    for tag, value in identifiable.items():
                        if value:
                            # Highlight fields that will be anonymized
                            will_anon = (
                                tag in tags_to_anonymize
                                or tag in dicom_anonymizer.UID_TAGS
                            )
                            if will_anon:
                                st.markdown(
                                    f"- **{tag}**: `{value}` :material/check: wird anonymisiert"
                                )
                            else:
                                st.markdown(f"- {tag}: `{value}`")
            else:
                st.warning("Die ausgewählte Datei ist keine gültige DICOM-Datei.")

    # Initialize session state for results
    if "dicom_results" not in st.session_state:
        st.session_state.dicom_results = None
    if "dicom_config" not in st.session_state:
        st.session_state.dicom_config = None

    # Anonymize button
    if st.button("Anonymisieren", type="primary", disabled=not uploaded_files):
        if not uploaded_files:
            st.warning("Bitte lade zuerst DICOM-Dateien hoch.")
        else:
            config = dicom_anonymizer.AnonymizationConfig(
                tags_to_anonymize=[(tag, "") for tag in tags_to_anonymize],
                regenerate_uids=regenerate_uids,
                remove_private_tags=remove_private_tags,
            )

            results = []
            progress_bar = st.progress(0, text="Anonymisiere Dateien...")

            for i, uploaded_file in enumerate(uploaded_files):
                data = uploaded_file.read()
                uploaded_file.seek(0)

                result = dicom_anonymizer.anonymize_dicom_bytes(
                    data, uploaded_file.name, config
                )
                results.append(result)

                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(
                    progress, text=f"Verarbeitet: {uploaded_file.name}"
                )

            progress_bar.empty()

            # Store results in session state
            st.session_state.dicom_results = results
            st.session_state.dicom_config = config

    # Show results from session state
    if st.session_state.dicom_results:
        results = st.session_state.dicom_results
        config = st.session_state.dicom_config

        st.subheader("Ergebnisse")

        success_count = sum(1 for r in results if not r.error)
        error_count = len(results) - success_count

        col1, col2, col3 = st.columns(3)
        col1.metric("Erfolgreich", success_count)
        col2.metric("Fehler", error_count)
        with col3:
            if st.button(":material/refresh: Neue Dateien", key="reset_dicom"):
                st.session_state.dicom_results = None
                st.session_state.dicom_config = None
                st.rerun()

        # Show errors if any
        if error_count > 0:
            with st.expander("Fehlerdetails", expanded=True):
                for result in results:
                    if result.error:
                        st.error(f"**{result.original_filename}**: {result.error}")

        # Download section
        if success_count > 0:
            st.subheader("Download")

            # Create ZIP with anonymized files
            zip_data = dicom_anonymizer.create_anonymized_zip(results)

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label=":material/download: Anonymisierte Dateien (ZIP)",
                    data=zip_data,
                    file_name=f"{datetime.now().strftime('%Y%m%d_%H%M')}_anonymized_dicom_{config.anonymization_id}.zip",
                    mime="application/zip",
                    key="download_zip_btn",
                )

            with col2:
                # Create mapping CSV
                csv_buffer = io.StringIO()
                import csv

                writer = csv.writer(csv_buffer)
                writer.writerow(
                    [
                        "original_id",
                        "anonymization_id",
                        "filename",
                        "tags_anonymized",
                        "uids_regenerated",
                    ]
                )
                for result in results:
                    if not result.error:
                        writer.writerow(
                            [
                                result.original_id,
                                result.anonymization_id,
                                result.original_filename,
                                ",".join(result.tags_anonymized),
                                ",".join(result.uids_regenerated),
                            ]
                        )

                st.download_button(
                    label=":material/table_chart: Mapping-CSV",
                    data=csv_buffer.getvalue(),
                    file_name=f"anonymization_mapping_{config.anonymization_id}.csv",
                    mime="text/csv",
                    key="download_csv_btn",
                )

            # Option to import to Sources
            st.subheader("In Quellen importieren")
            if st.button(
                "Anonymisierte Dateien zu Quellen hinzufügen",
                key="import_to_sources_btn",
            ):
                from app.main import SourceItem, _now_iso
                from services import storage

                imported_count = 0
                for result in results:
                    if result.error:
                        continue

                    # Create source entry with binary file storage
                    source = SourceItem(
                        name=f"DICOM: {result.original_filename}",
                        type_label="DICOM",
                        meta=f"Anonymisiert ({result.anonymization_id[:8]})",
                    )

                    # Save DICOM binary to disk
                    file_path = storage.save_dicom_file(
                        source.id,
                        result.original_filename,
                        result.anonymized_data,
                    )
                    source.file_path = file_path

                    # Add to sources.json for Home page display
                    source_entry = {
                        "id": source.id,
                        "name": source.name,
                        "type_label": source.type_label,
                        "meta": source.meta,
                        "selected": True,
                        "created_at": _now_iso(),
                        "file_path": file_path,
                    }

                    # Load, append, save
                    current_sources = storage.load_sources()
                    current_sources.append(source_entry)
                    storage.save_sources(current_sources)

                    # Also update session state if already loaded
                    if "sources" in st.session_state:
                        st.session_state["sources"].append(source)

                    imported_count += 1

                st.success(
                    f"{imported_count} anonymisierte DICOM-Dateien zu Quellen hinzugefügt."
                )

    # Directory anonymization section
    st.divider()
    st.header("Verzeichnis anonymisieren")

    st.markdown("""
        Für die Batch-Anonymisierung ganzer Verzeichnisse mit DICOM-Dateien
        kann die Kommandozeile verwendet werden:
        
        ```bash
        python -m services.dicom_anonymizer /pfad/zum/input /pfad/zum/output
        ```
        """)

    # Settings link
    st.divider()
    st.markdown("""
        **Einstellungen:** 
        
        Die automatische Anonymisierung beim Upload kann in der Configuration 
        aktiviert werden. Setze `DICOM_ANONYMIZE_ON_UPLOAD=true` in der `.env` Datei.
        """)


if __name__ == "__main__":
    render()
