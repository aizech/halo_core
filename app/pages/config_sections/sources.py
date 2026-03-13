from __future__ import annotations

import streamlit as st

from app.pages.config_sections import shared
from services import connectors


def render(container: st.delta_generator.DeltaGenerator) -> None:
    container.subheader("Quellen & Connectoren")

    # Test mode toggle
    test_mode = container.toggle(
        "Test-Modus",
        value=st.session_state["config"].get("connector_test_mode", False),
        help="Im Test-Modus können Connector-Credentials direkt hier eingegeben werden. "
        "In Produktion werden Credentials aus .env gelesen.",
    )

    if test_mode:
        container.caption(
            "⚠️ Test-Modus aktiv. Credentials werden in der Session gespeichert, nicht persistent. "
            "Für Produktion verwende die .env-Datei."
        )
    else:
        container.caption(
            "Credentials werden aus Umgebungsvariablen (.env) gelesen. "
            "Aktiviere Test-Modus für temporäre Test-Credentials."
        )

    # Test mode: show credential input fields
    test_credentials = st.session_state["config"].get("connector_test_credentials", {})

    # Show connector configuration status
    status = connectors.get_connector_status(
        test_mode=test_mode, test_credentials=test_credentials
    )

    with container.expander("Connector-Status", expanded=True):
        for slug, info in status.items():
            col1, col2 = st.columns([1, 2])
            with col1:
                if info["configured"]:
                    st.markdown(f"✅ **{info['name']}**")
                else:
                    st.markdown(f"⚠️ **{info['name']}**")
            with col2:
                if info["configured"]:
                    st.caption("Bereit für Sync")
                else:
                    missing = info.get("missing_env_vars", [])
                    if missing:
                        st.caption(f"Fehlt: {', '.join(missing)}")

    if test_mode:
        with container.expander("Test-Credentials eingeben", expanded=False):
            _render_test_credentials_form(test_credentials)

    enabled = container.multiselect(
        "Aktivierte Connectoren",
        options=list(connectors.AVAILABLE_CONNECTORS.keys()),
        default=st.session_state["config"].get("enabled_connectors", []),
        format_func=lambda key: connectors.AVAILABLE_CONNECTORS[key].name,
    )

    container.subheader("Bildgenerierung")
    image_model = container.selectbox(
        "Bildmodell",
        options=["gpt-image-1.5"],
        index=0,
    )

    if container.button("Speichern", key="cfg_sources_save_connectors"):
        updates = {
            "enabled_connectors": enabled,
            "image_model": image_model,
            "connector_test_mode": test_mode,
            "connector_test_credentials": test_credentials,
            "log_agent_payload": bool(st.session_state.get("log_agent_payload", True)),
            "log_agent_response": bool(
                st.session_state.get("log_agent_response", True)
            ),
            "log_agent_errors": bool(st.session_state.get("log_agent_errors", True)),
            "log_user_requests": bool(st.session_state.get("log_user_requests", True)),
            "log_stream_events": bool(st.session_state.get("log_stream_events", False)),
        }
        shared.save_payload(st.session_state["config"], updates)
        container.success("Connector-Einstellungen aktualisiert")


def _render_test_credentials_form(
    test_credentials: dict,
) -> None:
    """Render credential input fields for each connector in test mode."""
    # Notion
    st.markdown("**Notion**")
    notion_key = st.text_input(
        "NOTION_API_KEY",
        value=test_credentials.get("notion", {}).get("api_key", ""),
        type="password",
        key="test_notion_api_key",
    )
    if notion_key:
        test_credentials["notion"] = {"api_key": notion_key}

    st.divider()

    # Google Drive
    st.markdown("**Google Drive**")
    drive_creds = st.text_input(
        "GOOGLE_OAUTH_CREDENTIALS (Pfad oder JSON)",
        value=test_credentials.get("drive", {}).get("oauth_credentials", ""),
        type="password",
        key="test_drive_creds",
    )
    if drive_creds:
        test_credentials["drive"] = {"oauth_credentials": drive_creds}

    st.divider()

    # OneDrive / Microsoft 365
    st.markdown("**OneDrive / Microsoft 365**")
    onedrive_creds = test_credentials.get("onedrive", {})
    msal_tenant = st.text_input(
        "MSAL_TENANT_ID",
        value=onedrive_creds.get("tenant_id", ""),
        key="test_msal_tenant",
    )
    msal_client_id = st.text_input(
        "MSAL_CLIENT_ID",
        value=onedrive_creds.get("client_id", ""),
        key="test_msal_client_id",
    )
    msal_secret = st.text_input(
        "MSAL_CLIENT_SECRET",
        value=onedrive_creds.get("client_secret", ""),
        type="password",
        key="test_msal_secret",
    )
    if msal_tenant or msal_client_id or msal_secret:
        test_credentials["onedrive"] = {
            "tenant_id": msal_tenant,
            "client_id": msal_client_id,
            "client_secret": msal_secret,
        }

    st.divider()

    # DICOM PACS
    st.markdown("**DICOM PACS**")
    dicom_creds = test_credentials.get("dicom-pacs", {})
    dicom_host = st.text_input(
        "DICOM_PACS_HOST",
        value=dicom_creds.get("host", ""),
        key="test_dicom_host",
    )
    dicom_port = st.text_input(
        "DICOM_PACS_PORT",
        value=dicom_creds.get("port", ""),
        key="test_dicom_port",
    )
    dicom_ae = st.text_input(
        "DICOM_PACS_AE_TITLE",
        value=dicom_creds.get("ae_title", ""),
        key="test_dicom_ae",
    )
    if dicom_host or dicom_port or dicom_ae:
        test_credentials["dicom-pacs"] = {
            "host": dicom_host,
            "port": dicom_port,
            "ae_title": dicom_ae,
        }
