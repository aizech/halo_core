from __future__ import annotations

import streamlit as st

from app.pages.config_sections import shared
from services import auth_service, storage


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render preferences configuration (migrated from main._render_preferences_configuration)."""
    shared.render_config_saved_caption(container, "preferences")
    shared.render_config_saved_caption(container, "app_auth")

    config = st.session_state.get("config", {})
    container.caption(
        "Configure authentication, access control, and system preferences."
    )

    # Authentication & Access Section
    auth_box = container.container(border=True)
    auth_box.markdown("**Auth & Access**")

    auth_mode_value = auth_service.normalize_auth_mode(config.get("auth_mode"))
    auth_mode = auth_box.selectbox(
        "Auth-Modus",
        options=["local_only", "auth_optional", "auth_required"],
        index=["local_only", "auth_optional", "auth_required"].index(auth_mode_value),
        key="cfg_auth_mode",
    )
    enable_auth_services = auth_box.checkbox(
        "Auth-Services aktivieren",
        value=bool(config.get("enable_auth_services", False)),
        key="cfg_enable_auth_services",
    )
    enable_auth_ui = auth_box.checkbox(
        "Login/Logout UI anzeigen",
        value=bool(config.get("enable_auth_ui", False)),
        key="cfg_enable_auth_ui",
    )
    enable_access_guards = auth_box.checkbox(
        "Access Guards aktivieren",
        value=bool(config.get("enable_access_guards", False)),
        key="cfg_enable_access_guards",
    )
    auth_provider = auth_box.text_input(
        "Auth Provider",
        value=str(config.get("auth_provider") or "auth0"),
        key="cfg_auth_provider",
        help="z.B. auth0",
    )
    auth_provider_value = str(auth_provider).strip()

    # Show auth readiness status
    auth_preview_config = {
        **config,
        "auth_mode": auth_mode,
        "enable_auth_services": bool(enable_auth_services),
        "enable_auth_ui": bool(enable_auth_ui),
        "enable_access_guards": bool(enable_access_guards),
    }
    if auth_provider_value:
        auth_preview_config["auth_provider"] = auth_provider_value
    elif "auth_provider" in auth_preview_config:
        del auth_preview_config["auth_provider"]

    auth_runtime_enabled_preview = auth_service.is_auth_enabled(auth_preview_config)
    if auth_mode == "local_only":
        auth_box.info(
            "Auth ist auf local_only gesetzt. Login/Logout und Access Guards bleiben inaktiv."
        )
    elif not bool(enable_auth_services):
        auth_box.warning(
            "Auth-Modus aktiv, aber Auth-Services sind deaktiviert. Aktiviere sie für Login/Logout."
        )
    elif not bool(enable_auth_ui):
        auth_box.warning(
            "Auth-Services sind aktiv, aber die Login/Logout UI ist ausgeblendet."
        )
    elif auth_runtime_enabled_preview:
        auth_box.success(
            "Auth-Setup ist aktiv. Login/Logout UI und Guards können verwendet werden."
        )
    else:
        auth_box.warning(
            "Auth ist teilweise konfiguriert. Pruefe Provider und Streamlit Auth-Konfiguration."
        )

    auth_box.markdown("**Auth Readiness**")
    auth_box.markdown(
        f"- [{'x' if auth_mode != 'local_only' else ' '}] Auth mode ist nicht `local_only`"
    )
    auth_box.markdown(
        f"- [{'x' if bool(enable_auth_services) else ' '}] `enable_auth_services` ist aktiv"
    )
    auth_box.markdown(
        f"- [{'x' if bool(enable_auth_ui) else ' '}] `enable_auth_ui` ist aktiv"
    )
    auth_box.markdown(
        f"- [{'x' if bool(enable_access_guards) else ' '}] `enable_access_guards` ist aktiv (optional)"
    )
    auth_box.markdown(
        f"- [{'x' if bool(auth_provider_value) else ' '}] Auth Provider ist gesetzt"
    )

    auth_payload = {
        "auth_mode": auth_mode,
        "enable_auth_services": bool(enable_auth_services),
        "enable_auth_ui": bool(enable_auth_ui),
        "enable_access_guards": bool(enable_access_guards),
        "auth_provider": auth_provider_value,
    }

    shared.render_config_dirty_hint(
        auth_box,
        "preferences",
        auth_payload,
        "Ungespeicherte Auth-Änderungen.",
    )

    if auth_box.button("Auth-Einstellungen speichern", key="save_auth_preferences"):
        st.session_state["config"]["auth_mode"] = auth_mode
        st.session_state["config"]["enable_auth_services"] = bool(enable_auth_services)
        st.session_state["config"]["enable_auth_ui"] = bool(enable_auth_ui)
        st.session_state["config"]["enable_access_guards"] = bool(enable_access_guards)
        provider_value = str(auth_provider).strip()
        if provider_value:
            st.session_state["config"]["auth_provider"] = provider_value
        elif "auth_provider" in st.session_state["config"]:
            del st.session_state["config"]["auth_provider"]
        storage.save_config(st.session_state["config"])
        shared.mark_config_saved(
            auth_box,
            "preferences",
            "Auth-Einstellungen gespeichert.",
            payload=auth_payload,
        )
        st.rerun()
