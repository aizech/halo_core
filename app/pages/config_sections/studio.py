from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

from app.pages.config_sections import shared

_LANG_OPTIONS = ["Deutsch", "English"]
_TONE_OPTIONS = ["Neutral", "Förmlich", "Locker"]


def _get_templates_path() -> Path:
    return Path(__file__).parents[3] / "templates" / "studio_templates.json"


def _load_templates_raw() -> List[Dict]:
    path = _get_templates_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("templates", []) if isinstance(payload, dict) else []
    except (json.JSONDecodeError, OSError):
        return []


def _save_template_defaults(
    template_id: str,
    language: str,
    tone: str,
    instructions: str,
) -> bool:
    path = _get_templates_path()
    if not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(payload, dict):
        return False
    templates = payload.get("templates", [])
    for template in templates:
        if isinstance(template, dict) and template.get("id") == template_id:
            defaults = template.setdefault("defaults", {})
            defaults["language"] = language
            defaults["tone"] = tone
            defaults["instructions"] = instructions
            break
    else:
        return False
    try:
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return True
    except OSError:
        return False


def _render_settings_panel(
    container: st.delta_generator.DeltaGenerator,
    templates: List[Dict],
) -> None:
    titles = [str(t.get("title", t.get("id", ""))) for t in templates]
    template_ids = [str(t.get("id", "")) for t in templates]

    selected_id = st.session_state.get("studio_selected_template")
    if selected_id not in template_ids:
        selected_id = template_ids[0] if template_ids else None

    selected_title = container.selectbox(
        "Vorlage",
        options=titles,
        index=template_ids.index(selected_id) if selected_id in template_ids else 0,
        key="studio_cfg_selected_template_title",
    )
    selected_template: Optional[Dict] = next(
        (t for t in templates if t.get("title") == selected_title), None
    )
    if not selected_template:
        return

    template_id = str(selected_template.get("id", ""))
    st.session_state["studio_selected_template"] = template_id

    defaults = (
        selected_template.get("defaults", {})
        if isinstance(selected_template.get("defaults"), dict)
        else {}
    )
    agent = (
        selected_template.get("agent", {})
        if isinstance(selected_template.get("agent"), dict)
        else {}
    )

    lang_key = f"studio_cfg_lang_{template_id}"
    tone_key = f"studio_cfg_tone_{template_id}"
    instr_key = f"studio_cfg_instr_{template_id}"

    st.session_state.setdefault(lang_key, defaults.get("language", "Deutsch"))
    st.session_state.setdefault(tone_key, defaults.get("tone", "Neutral"))
    st.session_state.setdefault(
        instr_key,
        defaults.get("instructions")
        or agent.get("instructions")
        or str(selected_template.get("description", "")),
    )

    details_box = container.container(border=True)
    details_box.markdown(
        f"**{selected_title}**  \n" f"{selected_template.get('description', '')}"
    )

    settings_box = container.container(border=True)
    settings_box.markdown("**Standardwerte**")

    lang_default = st.session_state.get(lang_key, "Deutsch")
    lang_idx = _LANG_OPTIONS.index(lang_default) if lang_default in _LANG_OPTIONS else 0
    settings_box.selectbox(
        "Sprache",
        options=_LANG_OPTIONS,
        index=lang_idx,
        key=lang_key,
    )

    tone_default = st.session_state.get(tone_key, "Neutral")
    tone_idx = _TONE_OPTIONS.index(tone_default) if tone_default in _TONE_OPTIONS else 0
    settings_box.selectbox(
        "Ton",
        options=_TONE_OPTIONS,
        index=tone_idx,
        key=tone_key,
    )

    settings_box.text_area(
        "Anweisungen",
        key=instr_key,
        height=140,
    )

    studio_payload = {
        "template_id": template_id,
        "language": st.session_state.get(lang_key, "Deutsch"),
        "tone": st.session_state.get(tone_key, "Neutral"),
        "instructions": st.session_state.get(instr_key, ""),
    }
    shared.render_config_dirty_hint(
        container,
        f"studio_{template_id}",
        studio_payload,
        "Ungespeicherte Vorlagen-Änderungen.",
    )

    if container.button(
        "Vorlage speichern",
        key=f"studio_cfg_save_{template_id}",
    ):
        language = str(st.session_state.get(lang_key, "Deutsch"))
        tone = str(st.session_state.get(tone_key, "Neutral"))
        instructions = str(st.session_state.get(instr_key, ""))
        success = _save_template_defaults(template_id, language, tone, instructions)
        if success:
            session_templates = st.session_state.get("studio_templates", [])
            for tmpl in session_templates:
                if hasattr(tmpl, "template_id") and tmpl.template_id == template_id:
                    if hasattr(tmpl, "defaults") and isinstance(tmpl.defaults, dict):
                        tmpl.defaults["language"] = language
                        tmpl.defaults["tone"] = tone
                        tmpl.defaults["instructions"] = instructions
                    break
            shared.mark_config_saved(
                container,
                f"studio_{template_id}",
                "Vorlage gespeichert",
                payload=studio_payload,
            )
        else:
            container.error(
                "Vorlage konnte nicht gespeichert werden (Datei nicht gefunden)."
            )


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render studio template configuration (migrated from main._render_studio_configuration)."""
    shared.render_config_saved_caption(container, "studio")
    container.subheader("Studio Vorlagen")
    container.caption(
        "Studio-Vorlagen definieren vorgefertigte Ausgabe-Workflows (z.B. Berichte, Zusammenfassungen). "
        "Jede Vorlage hat eigene Standardwerte für Sprache, Ton und Anweisungen. "
        "Änderungen hier beeinflussen nur das Studio – nicht den regulären Chat."
    )

    session_templates = st.session_state.get("studio_templates", [])
    raw_templates = _load_templates_raw()

    if raw_templates:
        _render_settings_panel(container, raw_templates)
    elif session_templates and isinstance(session_templates, list):
        raw_from_session: List[Dict] = []
        for tmpl in session_templates:
            if hasattr(tmpl, "template_id"):
                raw_from_session.append(
                    {
                        "id": tmpl.template_id,
                        "title": getattr(tmpl, "title", tmpl.template_id),
                        "description": getattr(tmpl, "description", ""),
                        "defaults": getattr(tmpl, "defaults", {}),
                        "agent": getattr(tmpl, "agent", {}),
                    }
                )
        if raw_from_session:
            _render_settings_panel(container, raw_from_session)
        else:
            container.caption("Keine Studio-Vorlagen verfügbar.")
    else:
        container.caption("Keine Studio-Vorlagen verfügbar.")
