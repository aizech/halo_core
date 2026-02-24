"""Streamlit entrypoint for the NotebookLM-style MVP."""

from __future__ import annotations

import json
import logging
import sys
import re
import uuid
import base64
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
from uuid import uuid4
from textwrap import shorten

import streamlit as st
from agno.media import Image

try:
    from agno.agent import RunEvent
except ImportError:  # pragma: no cover
    RunEvent = None
from streamlit import components
from pydantic import BaseModel, Field, ValidationError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
project_root_str = str(PROJECT_ROOT)
sys.path = [
    path
    for path in sys.path
    if path
    and Path(path).resolve() != PROJECT_ROOT
    and not str(Path(path)).casefold().endswith("\\onedrive\\dev\\halo_core")
    and not str(Path(path)).casefold().endswith("\\onedrive\\dev\\halo_core\\app")
]
sys.path.insert(0, project_root_str)

import services  # noqa: E402
from services import connectors, ingestion, pipelines, retrieval, storage  # noqa: E402
from services import chat_state  # noqa: E402
from services import menu_settings  # noqa: E402
from services import theme_presets  # noqa: E402
from services import presets  # noqa: E402
from services import user_memory  # noqa: E402
import services.agents as agents  # noqa: E402
from services import agents_config  # noqa: E402
from services import exports  # noqa: E402
from services.streaming_adapter import stream_agent_response  # noqa: E402
from services.chat_runtime import ChatTurnInput, run_chat_turn  # noqa: E402

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)
_LOGGER.info("main.py path: %s", __file__)
_LOGGER.info("sys.path[0]: %s", sys.path[0])
_LOGGER.info("services module path: %s", services.__file__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceItem:
    name: str
    type_label: str
    meta: str
    selected: bool = True
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=_now_iso)


@dataclass
class StudioAction:
    action_id: str
    label: str


@dataclass
class StudioTemplate:
    template_id: str
    title: str
    description: str
    status: str = ""
    icon: str = "🧩"
    color: str = "#f5f5f5"
    badge: Optional[str] = None
    actions: List[StudioAction] = field(default_factory=list)
    agent: Dict[str, str] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)


class StudioActionConfig(BaseModel):
    id: str = Field("generate", alias="id")
    label: str = "Generieren"


class StudioTemplateConfig(BaseModel):
    id: str
    title: str
    description: str
    status: str = ""
    icon: str = "🧩"
    color: str = "#f5f5f5"
    badge: Optional[str] = None
    actions: list[StudioActionConfig] = Field(default_factory=list)
    agent: dict[str, str] = Field(default_factory=dict)
    defaults: dict[str, str] = Field(default_factory=dict)


class StudioTemplatesConfig(BaseModel):
    templates: list[StudioTemplateConfig] = Field(default_factory=list)


StudioTemplateConfig.model_rebuild()
StudioTemplatesConfig.model_rebuild()


def _get_studio_template(template_id: str) -> Optional[StudioTemplate]:
    for template in st.session_state.get("studio_templates", []):
        if template.template_id == template_id:
            return template
    return None


def _get_agent_config(agent_id: str) -> Dict[str, object] | None:
    configs = st.session_state.get("agent_configs", {})
    config = configs.get(agent_id)
    if isinstance(config, dict):
        if config.get("enabled", True) is False:
            return None
        return config
    return None


def _default_studio_templates() -> List[StudioTemplate]:
    default_actions = [
        StudioAction("generate", "Generieren"),
        StudioAction("configure", "Konfigurieren"),
    ]
    return [
        StudioTemplate(
            template_id="podcast",
            title="Podcast",
            description="Konvertiere Erkenntnisse in Hörstücke.",
            status="BETA",
            icon="🎧",
            color="#F3ECFF",
            badge="BETA",
            actions=default_actions,
            agent={"instructions": "Erzeuge ein strukturiertes Podcast-Skript."},
        ),
        StudioTemplate(
            template_id="video_overview",
            title="Videoübersicht",
            description="Erstelle ein kurzes Drehbuch für Clips.",
            icon="🎬",
            color="#DFF5EC",
            actions=default_actions,
            agent={"instructions": "Erstelle ein Clip-Storyboard mit Szenen."},
        ),
        StudioTemplate(
            template_id="mindmap",
            title="Mindmap",
            description="Visualisiere Kernthemen und Beziehungen.",
            icon="🕸️",
            color="#FFEEDB",
            actions=default_actions,
            agent={"instructions": "Extrahiere Hauptthemen und Beziehungen."},
        ),
        StudioTemplate(
            template_id="reports",
            title="Berichte",
            description="Fasse Erkenntnisse in professionellen Reports zusammen.",
            icon="📊",
            color="#E7F0FF",
            actions=default_actions,
            agent={"instructions": "Erstelle einen Bericht mit klaren Abschnitten."},
        ),
        StudioTemplate(
            template_id="flashcards",
            title="Karteikarten",
            description="Lerne mit automatisch generierten Fragen.",
            icon="🗂️",
            color="#FFE4E2",
            actions=default_actions,
            agent={"instructions": "Erzeuge Q&A-Karteikarten."},
        ),
        StudioTemplate(
            template_id="quiz",
            title="Quiz",
            description="Teste dein Wissen mit individuellen Quizfragen.",
            icon="❔",
            color="#E0F4FF",
            actions=default_actions,
            agent={"instructions": "Erstelle Quizfragen mit Lösungen."},
        ),
        StudioTemplate(
            template_id="infographic",
            title="Infografik",
            description="Stelle Statistiken grafisch dar.",
            status="BETA",
            icon="📈",
            color="#EDE7FF",
            badge="BETA",
            actions=default_actions,
            agent={"instructions": "Fasse Kennzahlen als Infografik-Story zusammen."},
        ),
        StudioTemplate(
            template_id="presentation",
            title="Präsentation",
            description="Erstelle Slides als Grundlage für Vorträge.",
            status="BETA",
            icon="🖥️",
            color="#FFF4E0",
            badge="BETA",
            actions=default_actions,
            agent={"instructions": "Erzeuge eine Folienstruktur mit Agenda."},
        ),
        StudioTemplate(
            template_id="datatable",
            title="Datentabelle",
            description="Strukturiere Fakten in tabellarischer Form.",
            icon="📋",
            color="#F1F5F9",
            actions=default_actions,
            agent={"instructions": "Erstelle eine tabellarische Zusammenfassung."},
        ),
    ]


def _load_studio_templates() -> List[StudioTemplate]:
    templates_path = PROJECT_ROOT / "templates" / "studio_templates.json"
    if not templates_path.exists():
        return _default_studio_templates()
    try:
        payload = json.loads(templates_path.read_text(encoding="utf-8"))
        parsed = StudioTemplatesConfig.model_validate(payload)
    except (json.JSONDecodeError, ValidationError):
        return _default_studio_templates()
    templates: List[StudioTemplate] = []
    for item in parsed.templates:
        actions = [StudioAction(action.id, action.label) for action in item.actions]
        templates.append(
            StudioTemplate(
                template_id=item.id,
                title=item.title,
                description=item.description,
                status=item.status,
                icon=item.icon,
                color=item.color,
                badge=item.badge,
                actions=actions,
                agent=item.agent,
                defaults=item.defaults,
            )
        )
    return templates or _default_studio_templates()


def _normalize_studio_output_payload(
    payload: Dict[str, str] | str,
) -> Dict[str, object]:
    if isinstance(payload, dict):
        return {
            "content": payload.get("content", ""),
            "sources": payload.get("sources", []),
            "generated_at": payload.get("generated_at"),
            "image_path": payload.get("image_path"),
        }
    return {
        "content": payload,
        "sources": [],
        "generated_at": None,
        "image_path": None,
    }


def _generate_studio_output(
    template_name: str,
    instructions: str,
    sources: List[str],
    agent_config: Dict[str, str] | None = None,
) -> str:
    try:
        return pipelines.generate_studio_artifact(
            template_name,
            instructions,
            sources,
            agent_config,
        )
    except TypeError:
        return pipelines.generate_studio_artifact(template_name, instructions, sources)


def _get_studio_outputs_list() -> List[Dict[str, object]]:
    outputs = st.session_state.get("studio_outputs", [])
    if isinstance(outputs, list):
        return outputs
    if isinstance(outputs, dict):
        legacy_list: List[Dict[str, object]] = []
        for template_id, payload in outputs.items():
            normalized = _normalize_studio_output_payload(payload)
            template = _get_studio_template(template_id)
            legacy_list.append(
                {
                    "output_id": uuid4().hex,
                    "template_id": template_id,
                    "title": template.title if template else template_id,
                    "content": normalized.get("content", ""),
                    "sources": normalized.get("sources", []),
                    "generated_at": normalized.get("generated_at"),
                    "image_path": normalized.get("image_path"),
                }
            )
        return legacy_list
    return []


def _summarize_text(text: str, limit: int = 220) -> str:
    condensed = " ".join(text.strip().split())
    if len(condensed) <= limit:
        return condensed
    return condensed[:limit].rstrip() + "…"


def _truncate_label(text: str, limit: int = 48) -> str:
    condensed = " ".join(text.strip().split())
    if len(condensed) <= limit:
        return condensed
    return condensed[: limit - 1].rstrip() + "…"


def _format_relative_timestamp(timestamp: Optional[str]) -> str:
    if not timestamp:
        return "Gerade eben"
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return "Gerade eben"
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - parsed
    minutes = max(int(delta.total_seconds() // 60), 0)
    if minutes < 1:
        return "Gerade eben"
    if minutes < 60:
        return f"Vor {minutes} Minuten"
    hours = minutes // 60
    if hours < 24:
        return f"Vor {hours} Stunden"
    days = hours // 24
    return f"Vor {days} Tagen"


def _format_absolute_date(timestamp: Optional[str]) -> str:
    if not timestamp:
        return datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M")
    try:
        parsed = datetime.fromisoformat(timestamp)
    except ValueError:
        return timestamp
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone().strftime("%d.%m.%Y %H:%M")


def _sanitize_filename_base(text: str) -> str:
    cleaned = "".join(ch for ch in text if ch.isalnum()).lower()
    return cleaned or "download"


def _build_download_filename(
    title: str, timestamp: Optional[str], extension: str
) -> str:
    if timestamp:
        try:
            parsed = datetime.fromisoformat(timestamp)
        except ValueError:
            parsed = datetime.now(timezone.utc)
    else:
        parsed = datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    date_prefix = parsed.strftime("%Y%m%d")
    base = _sanitize_filename_base(title)[:18].ljust(18, "_")
    return f"{date_prefix}_{base}.{extension}"


def configure_page() -> None:
    st.set_page_config(
        page_title="HALO NotebookLM",
        page_icon="📓",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _apply_theme_preset_to_config(
    config: Dict[str, object], *, preset_name: str
) -> None:
    preset = theme_presets.THEME_PRESETS.get(preset_name)
    if not preset:
        return

    current = menu_settings.get_menu_settings(config)
    updated: Dict[str, object] = dict(current)
    updated["theme_preset_name"] = preset_name
    for key, value in preset.items():
        updated[key] = value
    menu_settings.save_menu_settings(config, updated)


def _handle_theme_mode_change(*, config: Dict[str, object], toggle_key: str) -> None:
    is_dark = bool(st.session_state.get(toggle_key))
    menu_cfg = menu_settings.get_menu_settings(config)
    menu_cfg["theme_mode"] = "dark" if is_dark else "light"
    menu_settings.save_menu_settings(config, menu_cfg)

    preset_name = (
        str(menu_cfg.get("theme_preset_dark") or "").strip()
        if is_dark
        else str(menu_cfg.get("theme_preset_light") or "").strip()
    )
    if preset_name:
        _apply_theme_preset_to_config(config, preset_name=preset_name)

    st.session_state["config"] = dict(config)


def _src_to_css_url(src: str) -> str:
    cleaned = str(src or "").strip()
    if not cleaned:
        return ""
    if cleaned.startswith("http://") or cleaned.startswith("https://"):
        return cleaned

    candidate = Path(cleaned)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / cleaned
    if not candidate.exists() or not candidate.is_file():
        return ""

    mime, _ = mimetypes.guess_type(str(candidate))
    if not mime:
        mime = "application/octet-stream"
    encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_sidebar() -> None:
    menu_cfg = menu_settings.get_menu_settings(st.session_state.get("config", {}))

    theme_mode = str(menu_cfg.get("theme_mode") or "light").strip().lower()
    if theme_mode not in {"light", "dark"}:
        theme_mode = "light"

    separator_color = (
        str(menu_cfg.get("sidebar_separator_color_dark") or "").strip()
        if theme_mode == "dark"
        else str(menu_cfg.get("sidebar_separator_color_light") or "").strip()
    )
    if not separator_color:
        separator_color = str(
            menu_cfg.get("sidebar_separator_color") or "#6C757D"
        ).strip()

    logo_src = (
        str(menu_cfg.get("logo_src_dark") or "").strip()
        if theme_mode == "dark"
        else str(menu_cfg.get("logo_src_light") or "").strip()
    )
    icon_src = (
        str(menu_cfg.get("icon_src_dark") or "").strip()
        if theme_mode == "dark"
        else str(menu_cfg.get("icon_src_light") or "").strip()
    )

    logo_css_url = _src_to_css_url(logo_src)
    icon_css_url = _src_to_css_url(icon_src)

    logo_render_height_px = int(menu_cfg.get("logo_render_height_px") or 36)
    icon_render_height_px = int(menu_cfg.get("icon_render_height_px") or 24)
    if logo_css_url or icon_css_url:
        st.sidebar.markdown(
            """
            <div class="halo-brand">
              <div class="halo-brand-icon"></div>
              <div class="halo-brand-logo"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <style>
                section[data-testid='stSidebar'] .halo-brand {
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 12px 8px 6px 8px;
                }
                section[data-testid='stSidebar'] .halo-brand-icon,
                section[data-testid='stSidebar'] .halo-brand-logo {
                    background-repeat: no-repeat;
                    background-position: center;
                    background-size: contain;
                    width: 100%;
                }
                section[data-testid='stSidebar']:hover .halo-brand-icon {
                    display: none;
                }
                section[data-testid='stSidebar']:not(:hover) .halo-brand-logo {
                    display: none;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if icon_css_url:
            st.sidebar.markdown(
                f"""<style>.halo-brand-icon{{background-image:url('{icon_css_url}');height:{icon_render_height_px}px;width:{icon_render_height_px}px;flex:0 0 {icon_render_height_px}px;}}</style>""",
                unsafe_allow_html=True,
            )
        if logo_css_url:
            st.sidebar.markdown(
                f"""<style>.halo-brand-logo{{background-image:url('{logo_css_url}');height:{logo_render_height_px}px;max-width:100%;}}</style>""",
                unsafe_allow_html=True,
            )

    logo_height_px = int(menu_cfg.get("logo_height_px") or 0)
    if (logo_css_url or icon_css_url) and logo_height_px > 0:
        st.sidebar.markdown(
            f"<div style='height: {logo_height_px}px;'></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <style>
            :root {{
                --sidebar-bg: {menu_cfg['sidebar_bg']};
                --sidebar-text: {menu_cfg['sidebar_text_color']};
                --sidebar-icon: {menu_cfg['sidebar_icon_color']};
                --sidebar-hover-bg: {menu_cfg['sidebar_hover_bg']};
                --sidebar-hover-text: {menu_cfg.get('sidebar_hover_text_color', menu_cfg['sidebar_text_color'])};
                --sidebar-active-bg: {menu_cfg['sidebar_active_bg']};
                --sidebar-focus-outline: {menu_cfg['sidebar_focus_outline']};
                --sidebar-separator-color: {separator_color};
                --sidebar-font-size: {menu_cfg['sidebar_font_size_px']}px;
                --sidebar-icon-size: {menu_cfg.get('sidebar_icon_size_px', 22)}px;
                --sidebar-collapsed-width: {menu_cfg['sidebar_collapsed_width_px']}px;
                --sidebar-hover-width: {menu_cfg['sidebar_hover_width_px']}px;
                --sidebar-item-gap: {menu_cfg.get('sidebar_item_gap_px', 8)}px;
                --sidebar-transition: {menu_cfg['sidebar_transition']};
            }}
            section[data-testid='stSidebar'] {{
                background-color: var(--sidebar-bg);
                min-width: var(--sidebar-collapsed-width) !important;
                max-width: var(--sidebar-collapsed-width) !important;
                width: var(--sidebar-collapsed-width) !important;
                transition: width var(--sidebar-transition);
                overflow-x: hidden;
            }}
            section[data-testid='stSidebarNav'] {{
                display: none;
            }}
            section[data-testid='stSidebarNavItems'] {{
                display: none;
            }}
            section[data-testid='stSidebar']:hover {{
                min-width: var(--sidebar-hover-width) !important;
                max-width: var(--sidebar-hover-width) !important;
                width: var(--sidebar-hover-width) !important;
            }}
            section[data-testid='stSidebar'] * {{
                color: var(--sidebar-text) !important;
                font-size: var(--sidebar-font-size) !important;
            }}
            section[data-testid='stSidebar'] .stButton > button {{
                width: 100%;
                text-align: left;
                border: none;
                background: transparent;
                border-radius: 10px;
                padding: 10px 12px;
                color: var(--sidebar-text) !important;
                font-weight: 600;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a {{
                display: flex;
                align-items: center;
                gap: 10px;
                border-radius: 10px;
                padding: 10px 12px;
                text-decoration: none;
                white-space: nowrap;
                overflow: hidden;
                transition: background-color var(--sidebar-transition);
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] {{
                margin-bottom: var(--sidebar-item-gap);
            }}
            section[data-testid='stSidebar'] .halo-menu-separator {{
                height: 1px;
                margin: calc(var(--sidebar-item-gap) / 2) 12px;
                background-color: var(--sidebar-separator-color);
                opacity: 0.8;
            }}
            section[data-testid='stSidebar'] .halo-menu-spacer {{
                width: 100%;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'] > div,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] div {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a svg {{
                fill: var(--sidebar-icon) !important;
                width: var(--sidebar-icon-size) !important;
                height: var(--sidebar-icon-size) !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-current='page'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-selected='true'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-selected='true'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-active='true'] {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'][aria-current='page'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'][aria-selected='true'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'][data-selected='true'],
            section[data-testid='stSidebar'] [data-testid='stPageLink'][data-active='true'] {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-current='page'] > div:first-child,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-selected='true'] > div:first-child,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-selected='true'] > div:first-child,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-active='true'] > div:first-child {{
                background-color: transparent !important;
                width: auto;
                height: auto;
                border-radius: 0;
                display: block;
                padding: 0;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-current='page'] div,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-selected='true'] div,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-selected='true'] div,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-active='true'] div {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-current='page'] svg,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[aria-selected='true'] svg,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-selected='true'] svg,
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a[data-active='true'] svg {{
                display: block;
                background-color: var(--sidebar-hover-bg) !important;
                border-radius: 999px;
                padding: 6px;
                box-sizing: content-box;
            }}
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a {{
                justify-content: center;
                padding-left: 8px;
                padding-right: 8px;
                border-radius: 0;
                background-color: transparent !important;
                box-shadow: none !important;
            }}
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a:hover,
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a[aria-current='page'],
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a[aria-selected='true'],
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a[data-selected='true'],
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a[data-active='true'] {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [aria-current='page'],
            section[data-testid='stSidebar'] [aria-selected='true'],
            section[data-testid='stSidebar'] [data-selected='true'],
            section[data-testid='stSidebar'] [data-active='true'] {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [aria-current='page']::before,
            section[data-testid='stSidebar'] [aria-selected='true']::before,
            section[data-testid='stSidebar'] [data-selected='true']::before,
            section[data-testid='stSidebar'] [data-active='true']::before,
            section[data-testid='stSidebar'] [aria-current='page']::after,
            section[data-testid='stSidebar'] [aria-selected='true']::after,
            section[data-testid='stSidebar'] [data-selected='true']::after,
            section[data-testid='stSidebar'] [data-active='true']::after {{
                background-color: transparent !important;
                box-shadow: none !important;
                border: none !important;
            }}
            section[data-testid='stSidebar'] [aria-current='page'] svg,
            section[data-testid='stSidebar'] [aria-selected='true'] svg,
            section[data-testid='stSidebar'] [data-selected='true'] svg,
            section[data-testid='stSidebar'] [data-active='true'] svg {{
                display: block;
                background-color: var(--sidebar-hover-bg) !important;
                border-radius: 999px;
                padding: 6px;
                box-sizing: content-box;
            }}
            section[data-testid='stSidebar']:not(:hover) [data-testid='stPageLink'] a p {{
                opacity: 0;
                max-width: 0;
                margin: 0;
                overflow: hidden;
            }}
            section[data-testid='stSidebar']:not(:hover) h1,
            section[data-testid='stSidebar']:not(:hover) h2,
            section[data-testid='stSidebar']:not(:hover) h3,
            section[data-testid='stSidebar']:not(:hover) [data-testid='stSidebarUserContent'] > div > div > p,
            section[data-testid='stSidebar']:not(:hover) .stCaption,
            section[data-testid='stSidebar']:not(:hover) .stMarkdown p,
            section[data-testid='stSidebar']:not(:hover) .stButton {{
                opacity: 0;
                max-height: 0;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden;
                pointer-events: none;
            }}
            section[data-testid='stSidebar']:hover [data-testid='stPageLink'] a p {{
                opacity: 1;
                max-width: 260px;
                transition: opacity var(--sidebar-transition);
            }}
            section[data-testid='stSidebar'] button:hover {{
                background-color: var(--sidebar-hover-bg) !important;
                color: var(--sidebar-hover-text) !important;
            }}
            section[data-testid='stSidebar'] button:hover svg {{
                fill: var(--sidebar-hover-text) !important;
                stroke: var(--sidebar-hover-text) !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a:hover {{
                background-color: var(--sidebar-hover-bg) !important;
                color: var(--sidebar-hover-text) !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a:hover svg {{
                fill: var(--sidebar-hover-text) !important;
                stroke: var(--sidebar-hover-text) !important;
            }}
            section[data-testid='stSidebar'] [data-testid='stPageLink'] a:hover p {{
                color: var(--sidebar-hover-text) !important;
            }}
            section[data-testid='stSidebar'] button:focus {{
                outline-color: var(--sidebar-focus-outline) !important;
            }}
            section[data-testid='stSidebar'] div[data-testid='stToggle'] {{
                padding: 6px 12px;
                margin-bottom: var(--sidebar-item-gap);
                border-radius: 10px;
            }}
            section[data-testid='stSidebar']:not(:hover) div[data-testid='stToggle'] {{
                display: flex;
                justify-content: center;
                padding-left: 8px;
                padding-right: 8px;
                border-radius: 0;
            }}
            section[data-testid='stSidebar']:not(:hover)
            div[data-testid='stHorizontalBlock']:has(.halo-theme-toggle-label) {{
                justify-content: center;
                gap: 0 !important;
            }}
            section[data-testid='stSidebar'] .halo-theme-toggle-label {{
                display: flex;
                align-items: center;
                height: 100%;
            }}
            section[data-testid='stSidebar']:not(:hover) .halo-theme-toggle-label {{
                display: none;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    render_theme_toggle = False
    for index, item in enumerate(menu_cfg.get("items", [])):
        item_kind = str(item.get("kind", "link")).strip().lower()
        if item_kind == "separator":
            st.sidebar.markdown(
                "<div class='halo-menu-separator'></div>",
                unsafe_allow_html=True,
            )
            continue
        if item_kind == "spacer":
            try:
                spacer_px = int(item.get("spacer_px", 16))
            except (TypeError, ValueError):
                spacer_px = 16
            spacer_px = max(4, min(64, spacer_px))
            st.sidebar.markdown(
                f"<div class='halo-menu-spacer' style='height: {spacer_px}px;'></div>",
                unsafe_allow_html=True,
            )
            continue
        if item_kind == "theme_toggle":
            render_theme_toggle = True
            continue
        label = str(item.get("label", "")).strip()
        page = str(item.get("page", "")).strip()
        icon = str(item.get("icon", "")).strip()
        if not label or not page:
            continue
        icon_token = f":material/{icon}:" if icon else None
        try:
            st.sidebar.page_link(
                page,
                label=label,
                icon=icon_token,
                use_container_width=True,
            )
            continue
        except Exception:
            pass

        nav_key = f"nav_{index}_{label.lower().replace(' ', '_')}"
        if st.sidebar.button(label, key=nav_key, width="stretch"):
            try:
                st.switch_page(page)
            except Exception:
                st.sidebar.error(f"{label} navigation requires Streamlit multipage.")

    if render_theme_toggle:
        toggle_key = "menu_theme_mode_toggle"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = (
                str(menu_cfg.get("theme_mode") or "light") == "dark"
            )
        toggle_cols = st.sidebar.columns([1, 3], vertical_alignment="center")
        toggle_cols[0].toggle(
            "Dark mode",
            key=toggle_key,
            on_change=_handle_theme_mode_change,
            kwargs={
                "config": st.session_state.get("config", {}),
                "toggle_key": toggle_key,
            },
            help="Dark mode",
            label_visibility="collapsed",
        )
        toggle_cols[1].markdown(
            "<div class='halo-theme-toggle-label'>Dark mode</div>",
            unsafe_allow_html=True,
        )

    st.sidebar.button("New Notebook", width="stretch", key="new_notebook")
    st.sidebar.divider()
    st.sidebar.caption("Need help? Visit AGENTS.md or join the #halo-support channel.")


def _init_state() -> None:
    _ensure = chat_state.ensure_state_key

    _ensure(st.session_state, "session_id", chat_state.new_session_id)

    if "sources" not in st.session_state:
        stored_sources = storage.load_sources()
        if stored_sources:
            hydrated: List[SourceItem] = []
            needs_resave = False
            for item in stored_sources:
                if "id" not in item:
                    item = {**item, "id": uuid4().hex}
                    needs_resave = True
                if "created_at" not in item:
                    item = {**item, "created_at": _now_iso()}
                    needs_resave = True
                hydrated.append(SourceItem(**item))
            st.session_state["sources"] = hydrated
            if needs_resave:
                _persist_sources()
        else:
            st.session_state["sources"] = []
    _sync_source_checkbox_state()

    _ensure(
        st.session_state,
        "chat_history",
        lambda: chat_state.load_or_default_chat_history(
            st.session_state.get("session_id")
        ),
    )
    _ensure(st.session_state, "persistent_tool_calls", dict)
    _ensure(st.session_state, "studio_templates", _load_studio_templates)
    _ensure(st.session_state, "notes", storage.load_notes)

    if "all_sources_summary_content" not in st.session_state:
        stored_summary = storage.load_all_sources_summary() or {}
        if isinstance(stored_summary, dict):
            st.session_state["all_sources_summary_content"] = str(
                stored_summary.get("content") or ""
            )
            st.session_state["all_sources_summary_signature"] = stored_summary.get(
                "signature"
            )
            st.session_state["all_sources_summary_generated_at"] = stored_summary.get(
                "generated_at"
            )
            st.session_state["all_sources_summary_source_count"] = stored_summary.get(
                "source_count"
            )
            st.session_state["all_sources_summary_stale"] = bool(
                stored_summary.get("stale", False)
            )
        else:
            st.session_state["all_sources_summary_content"] = ""
            st.session_state["all_sources_summary_signature"] = None
            st.session_state["all_sources_summary_generated_at"] = None
            st.session_state["all_sources_summary_source_count"] = 0
            st.session_state["all_sources_summary_stale"] = False

    if "studio_outputs" not in st.session_state:
        st.session_state["studio_outputs"] = storage.load_studio_outputs() or []
    elif isinstance(st.session_state.get("studio_outputs"), dict):
        st.session_state["studio_outputs"] = _get_studio_outputs_list()
        storage.save_studio_outputs(st.session_state["studio_outputs"])

    _ensure(
        st.session_state,
        "config",
        lambda: chat_state.load_or_default_config(
            stored_config=storage.load_config(),
            enabled_connectors=list(connectors.AVAILABLE_CONNECTORS.keys()),
        ),
    )
    if not str(st.session_state["config"].get("user_id") or "").strip():
        st.session_state["config"]["user_id"] = "local-user"
        storage.save_config(st.session_state["config"])
    _ensure(
        st.session_state,
        "agent_configs",
        agents_config.load_agent_configs,
    )


def _normalize_agent_tools(raw_tools: object) -> List[str]:
    normalized: List[str] = []
    if isinstance(raw_tools, list):
        for tool in raw_tools:
            if isinstance(tool, str):
                normalized.append(tool)
            else:
                tool_name = type(tool).__name__.lower()
                if "pubmed" in tool_name:
                    normalized.append("pubmed")
                elif "wikipedia" in tool_name:
                    normalized.append("wikipedia")
                elif "mermaid" in tool_name:
                    normalized.append("mermaid")
    return normalized


_MENU_EDITOR_ITEMS_KEY = "menu_editor_items"
_MENU_EDITOR_SIGNATURE_KEY = "menu_editor_signature"


def _normalize_menu_editor_items(items: object) -> List[Dict[str, object]]:
    if not isinstance(items, list):
        return []
    normalized: List[Dict[str, object]] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        item_kind = str(raw_item.get("kind", "link")).strip().lower()
        editor_item: Dict[str, object] = {
            "_editor_id": uuid.uuid4().hex,
            "kind": (
                item_kind
                if item_kind in {"link", "separator", "spacer", "theme_toggle"}
                else "link"
            ),
        }
        if editor_item["kind"] == "separator":
            normalized.append(editor_item)
            continue
        if editor_item["kind"] == "spacer":
            try:
                spacer_px = int(raw_item.get("spacer_px", 16))
            except (TypeError, ValueError):
                spacer_px = 16
            editor_item["spacer_px"] = max(4, min(64, spacer_px))
            normalized.append(editor_item)
            continue
        if editor_item["kind"] == "theme_toggle":
            normalized.append(editor_item)
            continue
        editor_item["label"] = str(raw_item.get("label", "")).strip()
        editor_item["icon"] = str(raw_item.get("icon", "")).strip()
        editor_item["page"] = str(raw_item.get("page", "")).strip()
        normalized.append(editor_item)
    return normalized


def _menu_items_signature(items: object) -> str:
    if not isinstance(items, list):
        return "[]"
    serializable = [item for item in items if isinstance(item, dict)]
    return json.dumps(serializable, sort_keys=True)


def _strip_editor_metadata(items: object) -> List[Dict[str, object]]:
    if not isinstance(items, list):
        return []
    cleaned: List[Dict[str, object]] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        cleaned.append(
            {key: value for key, value in raw_item.items() if key != "_editor_id"}
        )
    return cleaned


def _render_app_design_configuration(
    container: st.delta_generator.DeltaGenerator | None = None,
) -> None:
    if container is None:
        container = st.sidebar

    container.subheader("Sidebar Menu")
    current_menu = menu_settings.get_menu_settings(st.session_state["config"])
    container.caption("Farben, Größen und Theme-Einstellungen für das Sidebar-Menü.")

    theme_mode_value = str(current_menu.get("theme_mode", "dark")).strip().lower()
    if theme_mode_value not in {"light", "dark"}:
        theme_mode_value = "dark"
    theme_box = container.container(border=True)
    theme_box.markdown("**Theme & Presets**")
    theme_mode = theme_box.selectbox(
        "Theme Modus (default)",
        options=["light", "dark"],
        index=0 if theme_mode_value == "light" else 1,
        key="menu_theme_mode_selector",
    )

    preset_names = sorted(theme_presets.THEME_PRESETS.keys())
    theme_light_default = str(current_menu.get("theme_preset_light") or "").strip()
    theme_dark_default = str(current_menu.get("theme_preset_dark") or "").strip()
    if theme_light_default not in preset_names and preset_names:
        theme_light_default = preset_names[0]
    if theme_dark_default not in preset_names and preset_names:
        theme_dark_default = preset_names[-1]
    theme_preset_light = theme_box.selectbox(
        "Theme Preset (Light)",
        options=preset_names,
        index=preset_names.index(theme_light_default) if preset_names else None,
        key="menu_theme_preset_light",
    )
    theme_preset_dark = theme_box.selectbox(
        "Theme Preset (Dark)",
        options=preset_names,
        index=preset_names.index(theme_dark_default) if preset_names else None,
        key="menu_theme_preset_dark",
    )

    color_box = container.container(border=True)
    color_box.markdown("**Farben**")
    color_left, color_right = color_box.columns(2)
    with color_left:
        sidebar_bg = st.color_picker(
            "Sidebar Hintergrund",
            value=str(current_menu.get("sidebar_bg", "#343A40")),
            key="menu_sidebar_bg",
        )
        sidebar_text = st.color_picker(
            "Sidebar Textfarbe",
            value=str(current_menu.get("sidebar_text_color", "#F8F9FA")),
            key="menu_sidebar_text",
        )
        sidebar_hover = st.color_picker(
            "Hover Farbe",
            value=str(current_menu.get("sidebar_hover_bg", "#F22222")),
            key="menu_sidebar_hover",
        )
        sidebar_hover_text = st.color_picker(
            "Hover Textfarbe",
            value=str(
                current_menu.get(
                    "sidebar_hover_text_color",
                    current_menu.get("sidebar_text_color", "#F8F9FA"),
                )
            ),
            key="menu_sidebar_hover_text",
        )
        sidebar_separator = st.color_picker(
            "Separator Farbe",
            value=str(current_menu.get("sidebar_separator_color", "#6C757D")),
            key="menu_sidebar_separator",
        )
    with color_right:
        sidebar_icon = st.color_picker(
            "Icon Farbe",
            value=str(current_menu.get("sidebar_icon_color", "#F8F9FA")),
            key="menu_sidebar_icon",
        )
        sidebar_active = st.color_picker(
            "Aktive Farbe",
            value=str(current_menu.get("sidebar_active_bg", "#CC1E1E")),
            key="menu_sidebar_active",
        )
        sidebar_focus = st.color_picker(
            "Focus Outline",
            value=str(current_menu.get("sidebar_focus_outline", "#F22222")),
            key="menu_sidebar_focus",
        )
        sidebar_separator_light = st.color_picker(
            "Separator Farbe (Light)",
            value=str(
                current_menu.get(
                    "sidebar_separator_color_light",
                    current_menu.get("sidebar_separator_color", "#D0D0D0"),
                )
            ),
            key="menu_sidebar_separator_light",
        )
        sidebar_separator_dark = st.color_picker(
            "Separator Farbe (Dark)",
            value=str(
                current_menu.get(
                    "sidebar_separator_color_dark",
                    current_menu.get("sidebar_separator_color", "#6C757D"),
                )
            ),
            key="menu_sidebar_separator_dark",
        )

    sizing_box = container.container(border=True)
    sizing_box.markdown("**Größen & Layout**")
    sizing_left, sizing_right = sizing_box.columns(2)
    with sizing_left:
        sidebar_font_size = st.slider(
            "Schriftgröße (px)",
            min_value=12,
            max_value=24,
            value=int(current_menu.get("sidebar_font_size_px", 16)),
            key="menu_sidebar_font_size",
        )
        sidebar_icon_size = st.slider(
            "Icon Größe (px)",
            min_value=16,
            max_value=32,
            value=int(current_menu.get("sidebar_icon_size_px", 22)),
            key="menu_sidebar_icon_size",
        )
        sidebar_item_gap = st.slider(
            "Abstand zwischen Menüpunkten (px)",
            min_value=0,
            max_value=32,
            value=int(current_menu.get("sidebar_item_gap_px", 8)),
            key="menu_sidebar_item_gap",
        )
    with sizing_right:
        sidebar_collapsed_width = st.slider(
            "Breite eingeklappt (px)",
            min_value=56,
            max_value=120,
            value=int(current_menu.get("sidebar_collapsed_width_px", 64)),
            key="menu_sidebar_collapsed_width",
        )
        sidebar_hover_width = st.slider(
            "Breite bei Hover (px)",
            min_value=180,
            max_value=360,
            value=int(current_menu.get("sidebar_hover_width_px", 240)),
            key="menu_sidebar_hover_width",
        )

    branding_box = container.container(border=True)
    branding_box.markdown("**Branding (Logo & Icon)**")
    branding_col_1, branding_col_2 = branding_box.columns(2)
    with branding_col_1:
        logo_src_light = st.text_input(
            "Logo Quelle (Light)",
            value=str(current_menu.get("logo_src_light", "")),
            key="menu_logo_src_light",
        )
        icon_src_light = st.text_input(
            "Icon Quelle (Light)",
            value=str(current_menu.get("icon_src_light", "")),
            key="menu_icon_src_light",
        )
    with branding_col_2:
        logo_src_dark = st.text_input(
            "Logo Quelle (Dark)",
            value=str(current_menu.get("logo_src_dark", "")),
            key="menu_logo_src_dark",
        )
        icon_src_dark = st.text_input(
            "Icon Quelle (Dark)",
            value=str(current_menu.get("icon_src_dark", "")),
            key="menu_icon_src_dark",
        )

    logo_height_px = branding_box.slider(
        "Logo Platzhöhe (px)",
        min_value=24,
        max_value=128,
        value=int(current_menu.get("logo_height_px", 44)),
        key="menu_logo_height",
    )
    logo_render_height_px = branding_box.slider(
        "Logo Renderhöhe (px)",
        min_value=20,
        max_value=96,
        value=int(current_menu.get("logo_render_height_px", 36)),
        key="menu_logo_render_height",
    )
    icon_render_height_px = branding_box.slider(
        "Icon Renderhöhe (px)",
        min_value=16,
        max_value=64,
        value=int(current_menu.get("icon_render_height_px", 24)),
        key="menu_icon_render_height",
    )

    menu_items = current_menu.get("items", [])
    menu_items_signature = _menu_items_signature(menu_items)
    editor_signature = st.session_state.get(_MENU_EDITOR_SIGNATURE_KEY)
    editor_items = st.session_state.get(_MENU_EDITOR_ITEMS_KEY)
    if editor_signature != menu_items_signature or not isinstance(editor_items, list):
        st.session_state[_MENU_EDITOR_ITEMS_KEY] = _normalize_menu_editor_items(
            menu_items
        )
        st.session_state[_MENU_EDITOR_SIGNATURE_KEY] = menu_items_signature
    editor_items = st.session_state.get(_MENU_EDITOR_ITEMS_KEY, [])

    page_options: List[str] = []
    page_labels: Dict[str, str] = {}
    for source_items in (
        menu_settings.DEFAULT_MENU_SETTINGS.get("items", []),
        menu_items,
    ):
        if not isinstance(source_items, list):
            continue
        for source_item in source_items:
            if not isinstance(source_item, dict):
                continue
            if str(source_item.get("kind", "link")).strip().lower() != "link":
                continue
            page = str(source_item.get("page", "")).strip()
            if not page:
                continue
            label = str(source_item.get("label", "")).strip()
            if page not in page_options:
                page_options.append(page)
            if label:
                page_labels[page] = label

    menu_caption_cols = container.columns([4, 2])
    menu_caption_cols[0].caption(
        "Menüeinträge: mit ↑ / ↓ sortieren, Spacer / Separator / Theme Toggle einfügen"
    )
    menu_caption_cols[1].markdown(
        "[Google Material Icons](https://fonts.google.com/icons)",
        help="Icon-Namen für das Feld 'Icon (Material)'",
    )
    pending_action_name: str | None = None
    pending_action_index = -1

    for index, item in enumerate(editor_items):
        if not isinstance(item, dict):
            continue
        row_id = str(item.get("_editor_id") or uuid.uuid4().hex)
        item["_editor_id"] = row_id
        item_box = container.container(border=True)

        kind_options = ["link", "spacer", "separator", "theme_toggle"]
        kind_labels = {
            "link": "Link",
            "spacer": "Spacer",
            "separator": "Separator",
            "theme_toggle": "Theme Toggle",
        }
        current_kind = str(item.get("kind", "link")).strip().lower()
        if current_kind not in kind_options:
            current_kind = "link"
        header_cols = item_box.columns([2.4, 6.2, 0.6, 0.6, 0.6])
        header_cols[0].markdown(
            f"<div style='font-weight: 700; font-size: 1.05rem;'>Eintrag {index + 1}</div>",
            unsafe_allow_html=True,
        )
        selected_kind = header_cols[1].selectbox(
            "Typ",
            options=kind_options,
            index=kind_options.index(current_kind),
            format_func=lambda value: kind_labels.get(value, value),
            key=f"menu_item_kind_{row_id}",
            label_visibility="collapsed",
        )
        item["kind"] = selected_kind

        if header_cols[2].button(
            "↑",
            key=f"menu_item_up_{row_id}",
            disabled=index == 0,
        ):
            pending_action_name = "up"
            pending_action_index = index
        if header_cols[3].button(
            "↓",
            key=f"menu_item_down_{row_id}",
            disabled=index >= len(editor_items) - 1,
        ):
            pending_action_name = "down"
            pending_action_index = index
        if header_cols[4].button("✕", key=f"menu_item_delete_{row_id}"):
            pending_action_name = "delete"
            pending_action_index = index

        if selected_kind == "link":
            link_cols = item_box.columns([2.2, 1.6, 3.2])
            item["label"] = link_cols[0].text_input(
                "Label",
                value=str(item.get("label", "")),
                key=f"menu_item_label_{row_id}",
            )
            item["icon"] = link_cols[1].text_input(
                "Icon (Material)",
                value=str(item.get("icon", "")),
                key=f"menu_item_icon_{row_id}",
            )
            page_value = str(item.get("page", "")).strip()
            if page_value and page_value not in page_options:
                page_options.append(page_value)
            if page_options:
                default_page = (
                    page_value if page_value in page_options else page_options[0]
                )
                item["page"] = link_cols[2].selectbox(
                    "Seite",
                    options=page_options,
                    index=page_options.index(default_page),
                    format_func=lambda page: f"{page_labels.get(page, page)} ({page})",
                    key=f"menu_item_page_{row_id}",
                )
            else:
                item["page"] = link_cols[2].text_input(
                    "Seite",
                    value=page_value,
                    key=f"menu_item_page_{row_id}",
                )
        elif selected_kind == "spacer":
            item["spacer_px"] = item_box.slider(
                "Spacer Höhe (px)",
                min_value=4,
                max_value=64,
                value=int(item.get("spacer_px", 16)),
                key=f"menu_item_spacer_{row_id}",
            )

    add_cols = container.columns(4)
    if add_cols[0].button("+ Link", key="menu_item_add_link"):
        pending_action_name = "add_link"
    if add_cols[1].button("+ Spacer", key="menu_item_add_spacer"):
        pending_action_name = "add_spacer"
    if add_cols[2].button("+ Separator", key="menu_item_add_separator"):
        pending_action_name = "add_separator"
    if add_cols[3].button("+ Theme Toggle", key="menu_item_add_theme_toggle"):
        pending_action_name = "add_theme_toggle"

    if pending_action_name:
        next_items = _normalize_menu_editor_items(editor_items)
        if pending_action_name == "up" and pending_action_index > 0:
            next_items[pending_action_index - 1], next_items[pending_action_index] = (
                next_items[pending_action_index],
                next_items[pending_action_index - 1],
            )
        elif (
            pending_action_name == "down"
            and 0 <= pending_action_index < len(next_items) - 1
        ):
            next_items[pending_action_index + 1], next_items[pending_action_index] = (
                next_items[pending_action_index],
                next_items[pending_action_index + 1],
            )
        elif pending_action_name == "delete" and 0 <= pending_action_index < len(
            next_items
        ):
            del next_items[pending_action_index]
        elif pending_action_name == "add_link":
            default_page = page_options[0] if page_options else "main.py"
            next_items.append(
                {
                    "_editor_id": uuid.uuid4().hex,
                    "kind": "link",
                    "label": page_labels.get(default_page, "Neuer Menüpunkt"),
                    "icon": "chevron_right",
                    "page": default_page,
                }
            )
        elif pending_action_name == "add_spacer":
            next_items.append(
                {
                    "_editor_id": uuid.uuid4().hex,
                    "kind": "spacer",
                    "spacer_px": 16,
                }
            )
        elif pending_action_name == "add_separator":
            next_items.append(
                {
                    "_editor_id": uuid.uuid4().hex,
                    "kind": "separator",
                }
            )
        elif pending_action_name == "add_theme_toggle":
            next_items.append(
                {
                    "_editor_id": uuid.uuid4().hex,
                    "kind": "theme_toggle",
                }
            )

        st.session_state[_MENU_EDITOR_ITEMS_KEY] = next_items
        st.rerun()

    if container.button("Sidebar Menu speichern", key="save_sidebar_menu"):
        updated_items: List[Dict[str, object]] = []
        for item in editor_items:
            if not isinstance(item, dict):
                continue
            row_id = str(item.get("_editor_id") or "")
            item_kind = (
                str(
                    st.session_state.get(
                        f"menu_item_kind_{row_id}",
                        item.get("kind", "link"),
                    )
                )
                .strip()
                .lower()
            )
            if item_kind == "separator":
                updated_items.append({"kind": "separator"})
                continue
            if item_kind == "spacer":
                try:
                    spacer_px = int(
                        st.session_state.get(
                            f"menu_item_spacer_{row_id}",
                            item.get("spacer_px", 16),
                        )
                    )
                except (TypeError, ValueError):
                    spacer_px = 16
                updated_items.append(
                    {
                        "kind": "spacer",
                        "spacer_px": max(4, min(64, spacer_px)),
                    }
                )
                continue
            if item_kind == "theme_toggle":
                updated_items.append({"kind": "theme_toggle"})
                continue

            label = str(
                st.session_state.get(
                    f"menu_item_label_{row_id}",
                    item.get("label", ""),
                )
            ).strip()
            icon = str(
                st.session_state.get(
                    f"menu_item_icon_{row_id}",
                    item.get("icon", ""),
                )
            ).strip()
            page = str(
                st.session_state.get(
                    f"menu_item_page_{row_id}",
                    item.get("page", ""),
                )
            ).strip()
            if not label or not page:
                continue
            updated_items.append(
                {
                    "kind": "link",
                    "label": label,
                    "icon": icon,
                    "page": page,
                }
            )

        updated_menu = menu_settings.save_menu_settings(
            st.session_state["config"],
            {
                "sidebar_bg": sidebar_bg,
                "sidebar_text_color": sidebar_text,
                "sidebar_icon_color": sidebar_icon,
                "sidebar_hover_bg": sidebar_hover,
                "sidebar_hover_text_color": sidebar_hover_text,
                "sidebar_active_bg": sidebar_active,
                "sidebar_focus_outline": sidebar_focus,
                "sidebar_separator_color": sidebar_separator,
                "sidebar_separator_color_light": sidebar_separator_light,
                "sidebar_separator_color_dark": sidebar_separator_dark,
                "sidebar_font_size_px": sidebar_font_size,
                "sidebar_icon_size_px": sidebar_icon_size,
                "sidebar_collapsed_width_px": sidebar_collapsed_width,
                "sidebar_hover_width_px": sidebar_hover_width,
                "sidebar_item_gap_px": sidebar_item_gap,
                "theme_mode": theme_mode,
                "theme_preset_light": theme_preset_light,
                "theme_preset_dark": theme_preset_dark,
                "theme_preset_name": (
                    theme_preset_dark if theme_mode == "dark" else theme_preset_light
                ),
                "logo_src_light": logo_src_light,
                "logo_src_dark": logo_src_dark,
                "icon_src_light": icon_src_light,
                "icon_src_dark": icon_src_dark,
                "logo_height_px": logo_height_px,
                "logo_render_height_px": logo_render_height_px,
                "icon_render_height_px": icon_render_height_px,
                "items": updated_items,
                "sidebar_transition": str(
                    current_menu.get("sidebar_transition", "0.3s")
                ),
            },
        )
        storage.save_config(st.session_state["config"])
        st.session_state[_MENU_EDITOR_ITEMS_KEY] = _normalize_menu_editor_items(
            updated_menu.get("items", [])
        )
        st.session_state[_MENU_EDITOR_SIGNATURE_KEY] = _menu_items_signature(
            _strip_editor_metadata(st.session_state[_MENU_EDITOR_ITEMS_KEY])
        )
        container.success("Sidebar Menu gespeichert")

    if container.button("Sidebar Menu zurücksetzen", key="reset_sidebar_menu"):
        reset_menu = menu_settings.save_menu_settings(
            st.session_state["config"], menu_settings.DEFAULT_MENU_SETTINGS
        )
        storage.save_config(st.session_state["config"])
        st.session_state[_MENU_EDITOR_ITEMS_KEY] = _normalize_menu_editor_items(
            reset_menu.get("items", [])
        )
        st.session_state[_MENU_EDITOR_SIGNATURE_KEY] = _menu_items_signature(
            _strip_editor_metadata(st.session_state[_MENU_EDITOR_ITEMS_KEY])
        )
        container.success("Sidebar Menu auf Standard zurückgesetzt")


def _render_configuration_panel(
    container: st.delta_generator.DeltaGenerator | None = None,
) -> None:
    _render_app_design_configuration(container)


def _render_sources_configuration(
    container: st.delta_generator.DeltaGenerator,
) -> None:
    container.subheader("Quellen & Connectoren")
    enabled = container.multiselect(
        "Aktivierte Connectoren",
        options=list(connectors.AVAILABLE_CONNECTORS.keys()),
        default=st.session_state["config"].get("enabled_connectors", []),
        format_func=lambda key: connectors.AVAILABLE_CONNECTORS[key].name,
    )
    container.subheader("Bildgenerierung")
    image_model = container.selectbox(
        "Bildmodell",
        options=["gpt-image-1", "dall-e-3"],
        index=["gpt-image-1", "dall-e-3"].index(
            st.session_state["config"].get("image_model", "gpt-image-1")
        ),
    )
    if container.button("Speichern", key="save_connectors"):
        st.session_state["config"]["enabled_connectors"] = enabled
        st.session_state["config"]["image_model"] = image_model
        st.session_state["config"]["log_agent_payload"] = bool(
            st.session_state.get("log_agent_payload", True)
        )
        st.session_state["config"]["log_agent_response"] = bool(
            st.session_state.get("log_agent_response", True)
        )
        st.session_state["config"]["log_agent_errors"] = bool(
            st.session_state.get("log_agent_errors", True)
        )
        st.session_state["config"]["log_user_requests"] = bool(
            st.session_state.get("log_user_requests", True)
        )
        st.session_state["config"]["log_stream_events"] = bool(
            st.session_state.get("log_stream_events", False)
        )
        storage.save_config(st.session_state["config"])
        container.success("Connector-Einstellungen aktualisiert")


def _render_chat_memory_configuration(
    container: st.delta_generator.DeltaGenerator,
) -> None:
    payload_key = "cfg_chat_log_agent_payload"
    response_key = "cfg_chat_log_agent_response"
    errors_key = "cfg_chat_log_agent_errors"
    requests_key = "cfg_chat_log_user_requests"
    stream_events_key = "cfg_chat_log_stream_events"

    container.subheader("Agent-Logging")
    container.checkbox(
        "Agent payload loggen",
        value=bool(st.session_state["config"].get("log_agent_payload", True)),
        key=payload_key,
    )
    container.checkbox(
        "Agent response loggen",
        value=bool(st.session_state["config"].get("log_agent_response", True)),
        key=response_key,
    )
    container.checkbox(
        "Agent Fehler loggen",
        value=bool(st.session_state["config"].get("log_agent_errors", True)),
        key=errors_key,
    )
    container.checkbox(
        "User Requests loggen",
        value=bool(st.session_state["config"].get("log_user_requests", True)),
        key=requests_key,
    )
    container.checkbox(
        "Stream-Events debug",
        value=bool(st.session_state["config"].get("log_stream_events", False)),
        key=stream_events_key,
    )

    st.session_state["log_agent_payload"] = bool(
        st.session_state.get(payload_key, True)
    )
    st.session_state["log_agent_response"] = bool(
        st.session_state.get(response_key, True)
    )
    st.session_state["log_agent_errors"] = bool(st.session_state.get(errors_key, True))
    st.session_state["log_user_requests"] = bool(
        st.session_state.get(requests_key, True)
    )
    st.session_state["log_stream_events"] = bool(
        st.session_state.get(stream_events_key, False)
    )

    agents.set_logging_preferences(
        log_payload=bool(st.session_state.get("log_agent_payload", True)),
        log_response=bool(st.session_state.get("log_agent_response", True)),
        log_errors=bool(st.session_state.get("log_agent_errors", True)),
    )

    container.subheader("Chat Presets")
    presets_payload = presets.load_presets()
    preset_names = sorted(presets_payload.keys())
    if preset_names:
        current_preset = st.session_state.get("config", {}).get(
            "chat_preset", "Default"
        )
        preset_index = (
            preset_names.index(current_preset) if current_preset in preset_names else 0
        )
        selected_preset = container.selectbox(
            "Preset",
            options=preset_names,
            index=preset_index,
            key="chat_preset_selector",
        )
        if container.button("Preset anwenden", key="cfg_chat_apply_preset"):
            try:
                updated = presets.apply_preset_to_chat(selected_preset)
            except ValueError as exc:
                container.error(str(exc))
            else:
                st.session_state["config"]["chat_preset"] = selected_preset
                storage.save_config(st.session_state["config"])
                agent_configs = st.session_state.get("agent_configs", {})
                agent_configs["chat"] = updated
                st.session_state["agent_configs"] = agent_configs
                container.success("Chat-Preset angewendet")
    else:
        container.caption("Keine Presets gefunden (presets.json fehlt).")

    container.subheader("Chat Modell & Tools")
    agent_configs = st.session_state.get("agent_configs", {})
    chat_config = (
        agent_configs.get("chat", {}) if isinstance(agent_configs, dict) else {}
    )
    member_options = [
        agent_id for agent_id in agent_configs.keys() if agent_id != "chat"
    ]
    available_tools = {
        "pubmed": "PubMed Suche",
        "websearch": "Web Search",
        "youtube": "YouTube",
        "duckduckgo": "DuckDuckGo Suche",
        "arxiv": "arXiv Papers",
        "website": "Website Inhalte",
        "hackernews": "Hacker News",
        "yfinance": "Yahoo Finance",
        "calculator": "Calculator",
        "wikipedia": "Wikipedia Suche",
        "mermaid": "Mermaid Diagramme",
    }
    chat_model_key = "chat_cfg_model"
    chat_members_key = "chat_cfg_members"
    chat_tools_key = "chat_cfg_tools"
    container.text_input(
        "Chat Model",
        value=str(chat_config.get("model", "openai:gpt-5.2")),
        key=chat_model_key,
        help="Format: provider:model (z.B. openai:gpt-5.2)",
    )
    container.multiselect(
        "Chat Team",
        options=member_options,
        default=(
            chat_config.get("members", [])
            if isinstance(chat_config.get("members"), list)
            else []
        ),
        key=chat_members_key,
    )
    normalized_chat_tools = _normalize_agent_tools(chat_config.get("tools", []))
    if chat_tools_key in st.session_state:
        stored_tools = st.session_state.get(chat_tools_key)
        if isinstance(stored_tools, list) and any(
            not isinstance(tool, str) for tool in stored_tools
        ):
            st.session_state[chat_tools_key] = normalized_chat_tools
    container.multiselect(
        "Chat Tools",
        options=list(available_tools.keys()),
        default=[
            tool_id for tool_id in normalized_chat_tools if tool_id in available_tools
        ],
        format_func=lambda tool_id: available_tools.get(tool_id, tool_id),
        key=chat_tools_key,
    )
    if container.button("Chat speichern", key="cfg_chat_save_config"):
        updated = {
            **chat_config,
            "model": st.session_state.get(chat_model_key, "openai:gpt-5.2"),
            "members": st.session_state.get(chat_members_key, []),
            "tools": st.session_state.get(chat_tools_key, []),
        }
        agents_config.save_agent_config("chat", updated)
        agent_configs["chat"] = updated
        st.session_state["agent_configs"] = agent_configs
        container.success("Chat-Konfiguration gespeichert")


def _render_advanced_configuration(
    container: st.delta_generator.DeltaGenerator,
) -> None:
    container.subheader("Agenten")
    agent_configs = st.session_state.get("agent_configs", {})
    agent_ids = sorted(agent_configs.keys())
    if not agent_ids:
        container.caption("Keine Agenten-Konfigurationen gefunden.")
        return

    name_counts: Dict[str, int] = {}
    for agent_id in agent_ids:
        label = str(agent_configs.get(agent_id, {}).get("name", agent_id))
        name_counts[label] = name_counts.get(label, 0) + 1

    def _format_agent_label(agent_id: str) -> str:
        label = str(agent_configs.get(agent_id, {}).get("name", agent_id))
        if name_counts.get(label, 0) > 1:
            return f"{label} ({agent_id})"
        return label

    selected_agent_id = container.selectbox(
        "Agent auswählen",
        options=agent_ids,
        format_func=_format_agent_label,
    )
    selected_agent = agent_configs.get(selected_agent_id, {})
    key_suffix = selected_agent_id
    enabled_key = f"agent_cfg_enabled_{key_suffix}"
    name_key = f"agent_cfg_name_{key_suffix}"
    role_key = f"agent_cfg_role_{key_suffix}"
    description_key = f"agent_cfg_description_{key_suffix}"
    instructions_key = f"agent_cfg_instructions_{key_suffix}"
    model_key = f"agent_cfg_model_{key_suffix}"
    members_key = f"agent_cfg_members_{key_suffix}"
    tools_key = f"agent_cfg_tools_{key_suffix}"
    pubmed_email_key = f"agent_cfg_pubmed_email_{key_suffix}"
    pubmed_max_key = f"agent_cfg_pubmed_max_{key_suffix}"
    pubmed_enable_key = f"agent_cfg_pubmed_enable_{key_suffix}"
    pubmed_all_key = f"agent_cfg_pubmed_all_{key_suffix}"
    websearch_backend_key = f"agent_cfg_websearch_backend_{key_suffix}"
    websearch_results_key = f"agent_cfg_websearch_results_{key_suffix}"
    youtube_captions_key = f"agent_cfg_youtube_captions_{key_suffix}"
    youtube_video_info_key = f"agent_cfg_youtube_video_info_{key_suffix}"
    youtube_timestamps_key = f"agent_cfg_youtube_timestamps_{key_suffix}"
    duckduckgo_search_key = f"agent_cfg_duckduckgo_search_{key_suffix}"
    duckduckgo_news_key = f"agent_cfg_duckduckgo_news_{key_suffix}"
    duckduckgo_results_key = f"agent_cfg_duckduckgo_results_{key_suffix}"
    duckduckgo_timeout_key = f"agent_cfg_duckduckgo_timeout_{key_suffix}"
    duckduckgo_ssl_key = f"agent_cfg_duckduckgo_ssl_{key_suffix}"
    arxiv_max_results_key = f"agent_cfg_arxiv_max_results_{key_suffix}"
    arxiv_sort_by_key = f"agent_cfg_arxiv_sort_by_{key_suffix}"
    website_max_pages_key = f"agent_cfg_website_max_pages_{key_suffix}"
    website_timeout_key = f"agent_cfg_website_timeout_{key_suffix}"
    website_domains_key = f"agent_cfg_website_domains_{key_suffix}"
    hackernews_top_key = f"agent_cfg_hackernews_top_{key_suffix}"
    hackernews_user_key = f"agent_cfg_hackernews_user_{key_suffix}"
    hackernews_all_key = f"agent_cfg_hackernews_all_{key_suffix}"
    yfinance_price_key = f"agent_cfg_yfinance_price_{key_suffix}"
    yfinance_analyst_key = f"agent_cfg_yfinance_analyst_{key_suffix}"
    member_options = [
        agent_id for agent_id in agent_ids if agent_id != selected_agent_id
    ]

    container.checkbox(
        "Aktiviert",
        value=bool(selected_agent.get("enabled", True)),
        key=enabled_key,
    )
    container.text_input(
        "Name",
        value=str(selected_agent.get("name", "")),
        key=name_key,
    )
    container.text_input(
        "Rolle",
        value=str(selected_agent.get("role", "")),
        key=role_key,
    )
    container.text_area(
        "Beschreibung",
        value=str(selected_agent.get("description", "")),
        key=description_key,
        height=100,
    )
    container.text_area(
        "Anweisungen",
        value=str(selected_agent.get("instructions", "")),
        key=instructions_key,
        height=160,
    )
    container.text_input(
        "Model",
        value=str(selected_agent.get("model", "openai:gpt-5.2")),
        key=model_key,
        help="Format: provider:model (z.B. openai:gpt-5.2)",
    )

    available_tools = {
        "pubmed": "PubMed Suche",
        "websearch": "Web Search",
        "youtube": "YouTube",
        "duckduckgo": "DuckDuckGo Suche",
        "arxiv": "arXiv Papers",
        "website": "Website Inhalte",
        "hackernews": "Hacker News",
        "yfinance": "Yahoo Finance",
        "calculator": "Calculator",
        "wikipedia": "Wikipedia Suche",
        "mermaid": "Mermaid Diagramme",
    }
    normalized_tools = _normalize_agent_tools(selected_agent.get("tools", []))
    if tools_key in st.session_state:
        stored_tools = st.session_state.get(tools_key)
        if isinstance(stored_tools, list) and any(
            not isinstance(tool, str) for tool in stored_tools
        ):
            st.session_state[tools_key] = normalized_tools
    selected_tools = container.multiselect(
        "Tools",
        options=list(available_tools.keys()),
        default=[tool_id for tool_id in normalized_tools if tool_id in available_tools],
        format_func=lambda tool_id: available_tools.get(tool_id, tool_id),
        key=tools_key,
    )
    tool_settings = (
        selected_agent.get("tool_settings", {})
        if isinstance(selected_agent.get("tool_settings"), dict)
        else {}
    )
    if "pubmed" in selected_tools:
        pubmed_settings = tool_settings.get("pubmed", {})
        container.text_input(
            "PubMed E-Mail",
            value=str(pubmed_settings.get("email", "")),
            key=pubmed_email_key,
        )
        container.number_input(
            "PubMed Max Results",
            min_value=1,
            value=int(pubmed_settings.get("max_results") or 5),
            key=pubmed_max_key,
        )
        container.checkbox(
            "PubMed Suche aktiv",
            value=bool(pubmed_settings.get("enable_search_pubmed", True)),
            key=pubmed_enable_key,
        )
        container.checkbox(
            "PubMed Alle Quellen",
            value=bool(pubmed_settings.get("all", False)),
            key=pubmed_all_key,
        )
    if "websearch" in selected_tools:
        websearch_settings = tool_settings.get("websearch", {})
        container.selectbox(
            "WebSearch Backend",
            options=["", "duckduckgo", "google", "bing", "brave", "yandex"],
            index=["", "duckduckgo", "google", "bing", "brave", "yandex"].index(
                str(websearch_settings.get("backend", ""))
                if str(websearch_settings.get("backend", ""))
                in ["", "duckduckgo", "google", "bing", "brave", "yandex"]
                else ""
            ),
            key=websearch_backend_key,
        )
        container.number_input(
            "WebSearch Max Results",
            min_value=1,
            value=int(websearch_settings.get("num_results") or 5),
            key=websearch_results_key,
        )
    if "youtube" in selected_tools:
        youtube_settings = tool_settings.get("youtube", {})
        container.checkbox(
            "YouTube Captions aktiv",
            value=bool(youtube_settings.get("fetch_captions", True)),
            key=youtube_captions_key,
        )
        container.checkbox(
            "YouTube Video-Infos aktiv",
            value=bool(youtube_settings.get("fetch_video_info", True)),
            key=youtube_video_info_key,
        )
        container.checkbox(
            "YouTube Timestamps aktiv",
            value=bool(youtube_settings.get("fetch_timestamps", False)),
            key=youtube_timestamps_key,
        )
    if "duckduckgo" in selected_tools:
        duckduckgo_settings = tool_settings.get("duckduckgo", {})
        container.checkbox(
            "DuckDuckGo Suche aktiv",
            value=bool(duckduckgo_settings.get("enable_search", True)),
            key=duckduckgo_search_key,
        )
        container.checkbox(
            "DuckDuckGo News aktiv",
            value=bool(duckduckgo_settings.get("enable_news", True)),
            key=duckduckgo_news_key,
        )
        container.number_input(
            "DuckDuckGo Max Results",
            min_value=1,
            value=int(duckduckgo_settings.get("fixed_max_results") or 5),
            key=duckduckgo_results_key,
        )
        container.number_input(
            "DuckDuckGo Timeout (Sek)",
            min_value=1,
            value=int(duckduckgo_settings.get("timeout") or 10),
            key=duckduckgo_timeout_key,
        )
        container.checkbox(
            "DuckDuckGo SSL verifizieren",
            value=bool(duckduckgo_settings.get("verify_ssl", True)),
            key=duckduckgo_ssl_key,
        )
    if "arxiv" in selected_tools:
        arxiv_settings = (
            tool_settings.get("arxiv", {})
            if isinstance(tool_settings.get("arxiv"), dict)
            else {}
        )
        arxiv_sort_options = ["", "submittedDate", "lastUpdatedDate", "relevance"]
        arxiv_sort_default = str(arxiv_settings.get("sort_by", ""))
        if arxiv_sort_default not in arxiv_sort_options:
            arxiv_sort_default = ""
        container.number_input(
            "arXiv Max Results",
            min_value=1,
            max_value=50,
            value=int(arxiv_settings.get("max_results") or 5),
            key=arxiv_max_results_key,
        )
        container.selectbox(
            "arXiv Sortierung",
            options=arxiv_sort_options,
            index=arxiv_sort_options.index(arxiv_sort_default),
            key=arxiv_sort_by_key,
        )
    if "website" in selected_tools:
        website_settings = (
            tool_settings.get("website", {})
            if isinstance(tool_settings.get("website"), dict)
            else {}
        )
        container.number_input(
            "Website Max Pages",
            min_value=1,
            max_value=20,
            value=max(1, min(20, int(website_settings.get("max_pages") or 5))),
            key=website_max_pages_key,
        )
        container.number_input(
            "Website Timeout (Sek)",
            min_value=1,
            max_value=120,
            value=max(1, min(120, int(website_settings.get("timeout") or 10))),
            key=website_timeout_key,
        )
        container.text_area(
            "Website erlaubte Domains (eine pro Zeile)",
            value="\n".join(
                str(domain).strip()
                for domain in website_settings.get("allowed_domains", [])
                if str(domain).strip()
            ),
            key=website_domains_key,
        )
    if "hackernews" in selected_tools:
        hackernews_settings = tool_settings.get("hackernews", {})
        container.checkbox(
            "HackerNews Top Stories aktiv",
            value=bool(hackernews_settings.get("enable_get_top_stories", True)),
            key=hackernews_top_key,
        )
        container.checkbox(
            "HackerNews User-Details aktiv",
            value=bool(hackernews_settings.get("enable_get_user_details", True)),
            key=hackernews_user_key,
        )
        container.checkbox(
            "HackerNews Alle Funktionen",
            value=bool(hackernews_settings.get("all", False)),
            key=hackernews_all_key,
        )
    if "yfinance" in selected_tools:
        yfinance_settings = tool_settings.get("yfinance", {})
        container.checkbox(
            "YFinance Aktienkurs aktiv",
            value=bool(yfinance_settings.get("stock_price", True)),
            key=yfinance_price_key,
        )
        container.checkbox(
            "YFinance Analystenempfehlungen aktiv",
            value=bool(yfinance_settings.get("analyst_recommendations", True)),
            key=yfinance_analyst_key,
        )
    container.multiselect(
        "Team-Mitglieder",
        options=member_options,
        default=(
            selected_agent.get("members", [])
            if isinstance(selected_agent.get("members"), list)
            else []
        ),
        key=members_key,
    )
    if container.button("Agent speichern", key="cfg_advanced_save_agent_config"):
        updated_tool_settings: Dict[str, object] = {}
        if "pubmed" in selected_tools:
            email = st.session_state.get(pubmed_email_key, "").strip()
            max_results = int(st.session_state.get(pubmed_max_key, 5))
            updated_tool_settings["pubmed"] = {
                "email": email or None,
                "max_results": max_results,
                "enable_search_pubmed": bool(
                    st.session_state.get(pubmed_enable_key, True)
                ),
                "all": bool(st.session_state.get(pubmed_all_key, False)),
            }
        if "websearch" in selected_tools:
            backend = st.session_state.get(websearch_backend_key, "").strip()
            updated_tool_settings["websearch"] = {
                "backend": backend or None,
                "num_results": int(st.session_state.get(websearch_results_key, 5)),
            }
        if "youtube" in selected_tools:
            updated_tool_settings["youtube"] = {
                "fetch_captions": bool(
                    st.session_state.get(youtube_captions_key, True)
                ),
                "fetch_video_info": bool(
                    st.session_state.get(youtube_video_info_key, True)
                ),
                "fetch_timestamps": bool(
                    st.session_state.get(youtube_timestamps_key, False)
                ),
            }
        if "duckduckgo" in selected_tools:
            updated_tool_settings["duckduckgo"] = {
                "enable_search": bool(
                    st.session_state.get(duckduckgo_search_key, True)
                ),
                "enable_news": bool(st.session_state.get(duckduckgo_news_key, True)),
                "fixed_max_results": int(
                    st.session_state.get(duckduckgo_results_key, 5)
                ),
                "timeout": int(st.session_state.get(duckduckgo_timeout_key, 10)),
                "verify_ssl": bool(st.session_state.get(duckduckgo_ssl_key, True)),
            }
        if "arxiv" in selected_tools:
            sort_by = str(st.session_state.get(arxiv_sort_by_key, "")).strip()
            updated_tool_settings["arxiv"] = {
                "max_results": int(st.session_state.get(arxiv_max_results_key, 5)),
                "sort_by": sort_by or None,
            }
        if "website" in selected_tools:
            raw_domains = str(st.session_state.get(website_domains_key, ""))
            updated_tool_settings["website"] = {
                "max_pages": int(st.session_state.get(website_max_pages_key, 5)),
                "timeout": int(st.session_state.get(website_timeout_key, 10)),
                "allowed_domains": [
                    line.strip() for line in raw_domains.splitlines() if line.strip()
                ],
            }
        if "hackernews" in selected_tools:
            updated_tool_settings["hackernews"] = {
                "enable_get_top_stories": bool(
                    st.session_state.get(hackernews_top_key, True)
                ),
                "enable_get_user_details": bool(
                    st.session_state.get(hackernews_user_key, True)
                ),
                "all": bool(st.session_state.get(hackernews_all_key, False)),
            }
        if "yfinance" in selected_tools:
            updated_tool_settings["yfinance"] = {
                "stock_price": bool(st.session_state.get(yfinance_price_key, True)),
                "analyst_recommendations": bool(
                    st.session_state.get(yfinance_analyst_key, True)
                ),
            }
        updated = {
            **selected_agent,
            "enabled": bool(st.session_state.get(enabled_key, True)),
            "name": st.session_state.get(name_key, ""),
            "role": st.session_state.get(role_key, ""),
            "description": st.session_state.get(description_key, ""),
            "instructions": st.session_state.get(instructions_key, ""),
            "model": st.session_state.get(model_key, "openai:gpt-5.2"),
            "members": st.session_state.get(members_key, []),
            "tools": st.session_state.get(tools_key, []),
            "tool_settings": updated_tool_settings,
        }
        agents_config.save_agent_config(selected_agent_id, updated)
        agent_configs[selected_agent_id] = updated
        st.session_state["agent_configs"] = agent_configs
        container.success("Agent-Konfiguration gespeichert")


def _add_source(name: str, type_label: str, meta: str, body: str | None = None) -> None:
    source = SourceItem(name=name, type_label=type_label, meta=meta)
    st.session_state["sources"].append(source)
    _persist_sources()
    ingestion.ingest_source_content(
        title=name,
        body=body or "",
        meta={"type": type_label, "meta": meta, "source_id": source.id},
    )


def _toggle_source(source_id: str) -> None:
    current_value = st.session_state.get(f"src_{source_id}", True)
    sources = st.session_state.get("sources")
    if not isinstance(sources, list):
        return
    for source in sources:
        if source.id == source_id:
            source.selected = current_value
            break
    _persist_sources()


def _add_document_payload(payload: Dict[str, str], fallback_meta: str) -> None:
    meta = payload.get("meta") or payload.get("source_path") or fallback_meta
    _add_source(
        payload["title"],
        payload.get("type_label", "Doc"),
        meta,
        payload.get("body", ""),
    )


def _persist_sources() -> None:
    storage.save_sources([src.__dict__ for src in st.session_state["sources"]])


def _persist_studio_outputs() -> None:
    storage.save_studio_outputs(_get_studio_outputs_list())


def _sync_source_checkbox_state() -> None:
    if "sources" not in st.session_state:
        return
    for src in st.session_state["sources"]:
        st.session_state.setdefault(f"src_{src.id}", src.selected)


def _set_all_sources(selected: bool) -> None:
    for src in st.session_state["sources"]:
        src.selected = selected
        st.session_state[f"src_{src.id}"] = selected
    _persist_sources()


def _delete_sources(source_ids: List[str]) -> None:
    if not source_ids:
        return
    remaining: List[SourceItem] = []
    removed: List[SourceItem] = []
    for src in st.session_state["sources"]:
        if src.id in source_ids:
            removed.append(src)
        else:
            remaining.append(src)
    if not removed:
        return
    st.session_state["sources"] = remaining
    _persist_sources()
    for src in removed:
        retrieval.delete_source_chunks(src.id, title=src.name)
        st.session_state.pop(f"src_{src.id}", None)
    st.toast(f"{len(removed)} Quelle(n) entfernt")
    st.rerun()


def _rename_source(source_id: str, new_name: str) -> None:
    normalized = new_name.strip()
    if not normalized:
        st.warning("Neuer Name darf nicht leer sein")
        return
    for src in st.session_state["sources"]:
        if src.id == source_id:
            if src.name == normalized:
                st.info("Name unverändert")
                return
            previous_title = src.name
            src.name = normalized
            _persist_sources()
            retrieval.rename_source(src.id, normalized, previous_title)
            st.toast("Quelle umbenannt")
            st.rerun()
            return


def _selected_source_names() -> List[str]:
    return [src.name for src in st.session_state["sources"] if src.selected]


def _all_source_names() -> List[str]:
    return [src.name for src in st.session_state["sources"]]


def _sources_signature(names: List[str]) -> str:
    return "|".join(sorted(name.strip() for name in names if name and name.strip()))


def _generate_all_sources_summary() -> str:
    sources = st.session_state.get("sources", [])
    source_names = _all_source_names()
    source_blocks: List[str] = []
    for src in sources:
        chunk_texts = retrieval.get_source_chunk_texts(
            source_id=getattr(src, "id", None),
            title=getattr(src, "name", None),
        )
        if chunk_texts:
            joined = "\n".join(chunk_texts)
            source_blocks.append(f"### {src.name}\n{joined}")
        else:
            source_blocks.append(
                f"### {getattr(src, 'name', 'Quelle')}\n[MISSING_SOURCE_CONTENT]"
            )
    sources_payload = "\n\n".join(source_blocks).strip()

    instructions = (
        "Synthesize the sources into a single, coherent summary.\n"
        "Begin with a concise, fitting title (max 8 words).\n"
        "Follow these rules:\n"
        "- Extract only the essential themes, methods, and strategic goals.\n"
        "- Highlight how the sources connect and reinforce each other.\n"
        "- Maintain a neutral, professional, and concise tone.\n"
        "- Limit the summary to 1–2 paragraphs, max 150 words.\n"
        "- Emphasize technological approaches, practical user benefits, and strategic context.\n"
        "- Avoid repetition and do not list the sources individually.\n"
        "After the summary, provide one distilled key message in no more than 20 words.\n"
        "Sources:\n"
        f"{sources_payload or '[NO_SOURCES]'}"
    )
    try:
        return _generate_studio_output(
            "Bericht",
            instructions,
            source_names,
            _get_agent_config("reports"),
        )
    except TypeError:
        return _generate_studio_output("Bericht", instructions, source_names)


def _serialize_tool_calls(tool_calls: object) -> List[Dict[str, object]] | None:
    return chat_state.serialize_tool_calls(tool_calls)


def _append_chat(
    role: Literal["user", "assistant"],
    content: str,
    trace: Dict[str, object] | None = None,
    tool_calls: object | None = None,
    images: List[Dict[str, object]] | None = None,
) -> None:
    chat_state.append_and_persist_chat(
        st.session_state["chat_history"],
        st.session_state.get("session_id"),
        role,
        content,
        trace=trace,
        tool_calls=tool_calls,
        images=images,
    )


def _display_tool_calls(
    tool_calls_container: st.delta_generator.DeltaGenerator, tools: object
) -> None:
    if tools is None:
        return
    if tool_calls_container is None:
        return
    try:
        with tool_calls_container.container():
            if isinstance(tools, dict):
                tools = [tools]
            elif isinstance(tools, (str, int, float, bool)):
                tools = [{"name": "Tool Call", "content": str(tools)}]
            elif not isinstance(tools, list):
                try:
                    tools = list(tools)
                except (TypeError, ValueError):
                    return
            if not tools:
                return
            for tool_call in tools:
                if tool_call is None:
                    continue
                if hasattr(tool_call, "get"):
                    tool_name = tool_call.get("tool_name") or tool_call.get(
                        "name", "Unknown Tool"
                    )
                    tool_args = tool_call.get("tool_args") or tool_call.get("args", {})
                    content = tool_call.get("content")
                else:
                    tool_name = getattr(tool_call, "tool_name", None) or getattr(
                        tool_call, "name", "Unknown Tool"
                    )
                    tool_args = getattr(tool_call, "tool_args", None) or getattr(
                        tool_call, "args", {}
                    )
                    content = getattr(tool_call, "content", None)
                with st.expander(f"Tool: {tool_name}", expanded=False):
                    if tool_args:
                        st.code(json.dumps(tool_args, ensure_ascii=True, indent=2))
                    if content:
                        st.markdown(str(content))
    except Exception as exc:
        _LOGGER.warning("Failed to render tool calls: %s", exc)


def _render_thinking_trace(trace: Dict[str, object]) -> None:
    agent_name = trace.get("agent_name") or trace.get("agent_id") or "Agent"
    agent_type = trace.get("agent_type")
    agent_tools = trace.get("agent_tools_runtime") or trace.get("agent_tools") or []
    agent_members = (
        trace.get("agent_members_runtime") or trace.get("agent_members") or []
    )
    payload = trace.get("payload")
    error = trace.get("error")

    st.markdown(f"**Agent:** {agent_name}" + (f" ({agent_type})" if agent_type else ""))
    if agent_members:
        st.markdown(f"**Team members:** {', '.join(agent_members)}")
    if agent_tools:
        st.markdown(f"**Tools:** {', '.join(agent_tools)}")
    if payload:
        st.markdown("**Input:**")
        st.code(str(payload), language="text")
    if error:
        st.markdown("**Error:**")
        st.code(str(error), language="text")


def _stream_agent_response(
    agent,
    payload: str,
    response_container: st.delta_generator.DeltaGenerator | None = None,
    tool_calls_container: st.delta_generator.DeltaGenerator | None = None,
    images: List[Image] | None = None,
    stream_events: bool = True,
) -> Dict[str, object] | None:
    def _update_response(value: str) -> None:
        if response_container is not None:
            response_container.markdown(value)

    def _update_tools(tools: List[object]) -> None:
        if tool_calls_container is not None:
            _display_tool_calls(tool_calls_container, tools)

    return stream_agent_response(
        agent,
        payload,
        images=images,
        stream_events=stream_events,
        run_event=RunEvent,
        logger=_LOGGER,
        log_stream_events=bool(
            st.session_state.get("config", {}).get("log_stream_events")
        ),
        on_response=_update_response,
        on_tools=_update_tools,
    )


def _extract_mermaid_blocks(content: str) -> tuple[str, List[str]]:
    blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
    cleaned = re.sub(r"```mermaid\n(.*?)```", "", content, flags=re.DOTALL)
    return cleaned.strip(), [block.strip() for block in blocks]


def _sanitize_mermaid_block(block: str) -> str:
    sanitized = block.strip()

    def _replace_newlines_in_delimited_text(
        text: str,
        open_char: str,
        close_char: str,
    ) -> str:
        output: List[str] = []
        depth = 0
        for char in text:
            if char == open_char:
                depth += 1
                output.append(char)
                continue
            if char == close_char and depth:
                depth -= 1
                output.append(char)
                continue
            if char == "\n" and depth:
                output.append("<br/>")
                continue
            output.append(char)
        return "".join(output)

    sanitized = sanitized.replace("\r\n", "\n").replace("\r", "\n")
    sanitized = _replace_newlines_in_delimited_text(sanitized, "[", "]")
    sanitized = _replace_newlines_in_delimited_text(sanitized, "(", ")")

    pattern = re.compile(r'"([^"]*)"\s+"([^"]*)"', re.DOTALL)
    while True:
        updated = pattern.sub(
            lambda match: f'"{match.group(1)}<br/>{match.group(2)}"', sanitized
        )
        if updated == sanitized:
            break
        sanitized = updated
    return sanitized


def _render_mermaid_diagram(block: str) -> None:
    diagram_id = f"mermaid-{uuid.uuid4().hex}"
    zoom_in_id = f"zoom-in-{uuid.uuid4().hex}"
    zoom_out_id = f"zoom-out-{uuid.uuid4().hex}"
    zoom_reset_id = f"zoom-reset-{uuid.uuid4().hex}"
    lines = max(4, len(block.splitlines()))
    height = min(800, 120 + lines * 24)
    mermaid_code = json.dumps(block)
    html = """
    <style>
      .mermaid-zoom-wrap {{
        position: relative;
        border: 1px solid rgba(0,0,0,0.08);
        border-radius: 12px;
        overflow: hidden;
        background: #fff;
      }}
      .mermaid-zoom-controls {{
        position: absolute;
        top: 8px;
        right: 8px;
        display: flex;
        gap: 6px;
        z-index: 2;
      }}
      .mermaid-zoom-controls button {{
        border: 1px solid rgba(0,0,0,0.12);
        background: #fff;
        border-radius: 8px;
        padding: 4px 8px;
        cursor: pointer;
        font-size: 12px;
      }}
      .mermaid-zoom-canvas {{
        width: 100%;
        height: 100%;
        min-height: 360px;
      }}
      .mermaid-error {{
        color: #b91c1c;
        padding: 12px;
        font-size: 0.85rem;
        white-space: pre-wrap;
      }}
    </style>
    <div class="mermaid-zoom-wrap" id="wrap-{diagram_id}">
      <div class="mermaid-zoom-controls">
        <button id="{zoom_in_id}">＋</button>
        <button id="{zoom_out_id}">－</button>
        <button id="{zoom_reset_id}">Reset</button>
      </div>
      <div class="mermaid-zoom-canvas" id="{diagram_id}"></div>
    </div>
    <script>
      const target = document.getElementById("{diagram_id}");
      const code = {mermaid_code};
      const ensureScript = (src) => new Promise((resolve, reject) => {{
        if (document.querySelector(`script[src="${{src}}"]`)) {{
          const check = () => (src.includes("mermaid") ? window.mermaid : window.panzoom);
          if (check()) return resolve();
        }}
        const script = document.createElement("script");
        script.src = src;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error(`Failed to load ${{src}}`));
        document.head.appendChild(script);
      }});

      Promise.all([
        ensureScript("https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"),
        ensureScript("https://cdn.jsdelivr.net/npm/panzoom@9.4.0/dist/panzoom.min.js"),
      ])
        .then(() => {{
          if (!target) throw new Error("Mermaid container not found");
          if (!window.mermaid) throw new Error("Mermaid library unavailable");
          mermaid.initialize({{ startOnLoad: false, securityLevel: "loose" }});
          return mermaid.render("{diagram_id}-svg", code);
        }})
        .then((result) => {{
          const svgCode = result?.svg || result;
          if (!target) return;
          target.innerHTML = svgCode;
          const svg = target.querySelector("svg");
          if (!svg || !window.panzoom) return;
          const zoom = window.panzoom(svg, {{
            maxZoom: 4,
            minZoom: 0.4,
            zoomSpeed: 0.2,
            bounds: true,
            boundsPadding: 0.1,
          }});
          document.getElementById("{zoom_in_id}")?.addEventListener("click", () => zoom.smoothZoom(0, 0, 1.2));
          document.getElementById("{zoom_out_id}")?.addEventListener("click", () => zoom.smoothZoom(0, 0, 0.8));
          document.getElementById("{zoom_reset_id}")?.addEventListener("click", () => {{
            zoom.moveTo(0, 0);
            zoom.zoomAbs(0, 0, 1);
          }});
          if (typeof result?.bindFunctions === "function") {{
            result.bindFunctions(target);
          }}
        }})
        .catch((err) => {{
          if (target) {{
            target.innerHTML = `<div class='mermaid-error'>${{err}}</div>`;
          }}
        }});
    </script>
    """.format(
        diagram_id=diagram_id,
        zoom_in_id=zoom_in_id,
        zoom_out_id=zoom_out_id,
        zoom_reset_id=zoom_reset_id,
        mermaid_code=mermaid_code,
    )
    components.v1.html(html, height=height, scrolling=False)


def _render_chat_markdown(content: str) -> None:
    cleaned, mermaid_blocks = _extract_mermaid_blocks(content)
    if cleaned:
        st.markdown(cleaned, unsafe_allow_html=False)
    for block in mermaid_blocks:
        _render_mermaid_diagram(_sanitize_mermaid_block(block))


def _normalize_chat_response_text(content: str) -> str:
    if not content:
        return content
    normalized = content
    # Ensure markdown headings have a separating space, e.g. "###1" -> "### 1"
    normalized = re.sub(r"(^|\n)(#{1,6})(?=\S)", r"\1\2 ", normalized)
    # Add a blank line before headings if they are glued to previous text.
    normalized = re.sub(r"([^\n])(\n#{1,6}\s)", r"\1\n\2", normalized)
    # Remove markdown heading lines in chat answers.
    lines: list[str] = []
    in_code_fence = False
    for line in normalized.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_code_fence = not in_code_fence
            lines.append(line)
            continue
        if in_code_fence:
            lines.append(line)
            continue
        match = re.match(r"^(\s*[\ufeff\u200b\u200c\u200d]*)(#{1,6})(\s+.*)$", line)
        if not match:
            lines.append(line)
            continue
        # Drop markdown headings entirely from chat output.
        continue
    normalized = "\n".join(lines)
    return normalized.strip()


def _split_thinking_from_response(content: str) -> tuple[str | None, str]:
    if not content:
        return None, content

    working = content
    thinking_parts: list[str] = []
    stripped = working.lstrip()
    if stripped.startswith("think("):
        start_idx = working.find(stripped)
        split_candidates = []
        for token in ("\n\n", "\n##", "##", "\n# ", "# "):
            idx = working.find(token, start_idx)
            if idx != -1:
                split_candidates.append(idx)
        if not split_candidates:
            return stripped, ""
        split_at = min(split_candidates)
        thinking_parts.append(working[:split_at].strip())
        working = working[split_at:].lstrip()

    story_match = re.search(
        r"^##\s*(-?Story\b|Infografik-Story\b)",
        working,
        flags=re.MULTILINE,
    )
    if story_match:
        line_end = working.find("\n", story_match.end())
        if line_end != -1 and line_end + 1 < len(working):
            preamble = working[: line_end + 1].strip()
            if preamble:
                thinking_parts.append(preamble)
                working = working[line_end + 1 :].lstrip()

    story_lines = list(re.finditer(r"^.*Story.*Quelle.*$", working, flags=re.MULTILINE))
    if story_lines:
        last_story = story_lines[-1]
        if last_story.start() > 0:
            preamble = working[: last_story.start()].strip()
            if preamble:
                thinking_parts.append(preamble)
            working = working[last_story.start() :].lstrip()

    if not thinking_parts:
        thinking_text = None
    else:
        thinking_text = "\n\n".join(thinking_parts)

    delegate_lines = []
    kept_lines = []
    for line in working.splitlines():
        if "delegate_task_to_member" in line:
            delegate_lines.append(line.strip())
        else:
            kept_lines.append(line)
    if delegate_lines:
        delegate_block = "\n".join(delegate_lines).strip()
        if delegate_block:
            thinking_text = (
                f"{thinking_text}\n\n{delegate_block}"
                if thinking_text
                else delegate_block
            )
    cleaned_response = "\n".join(kept_lines).strip()
    if cleaned_response:
        first_line = next(
            (line for line in cleaned_response.splitlines() if line.strip()), ""
        )
        if first_line:
            second_idx = cleaned_response.find(first_line, len(first_line))
            if second_idx != -1:
                cleaned_response = cleaned_response[second_idx:].lstrip()
    cleaned_response = _normalize_chat_response_text(cleaned_response)
    return thinking_text, cleaned_response


def _save_uploaded_images(
    uploaded_files: List[st.runtime.uploaded_file_manager.UploadedFile],
) -> tuple[List[Dict[str, object]], List[Image]]:
    uploads_dir = PROJECT_ROOT / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    saved_images: List[Dict[str, object]] = []
    image_artifacts: List[Image] = []
    for uploaded_file in uploaded_files:
        safe_name = f"{uuid.uuid4().hex}_{uploaded_file.name}"
        target_path = uploads_dir / safe_name
        target_path.write_bytes(uploaded_file.getvalue())
        saved_images.append(
            {
                "filepath": str(target_path),
                "name": uploaded_file.name,
                "mime_type": uploaded_file.type,
            }
        )
        image_artifacts.append(Image(filepath=str(target_path)))
    return saved_images, image_artifacts


def _save_note_from_message(content: str) -> None:
    note = {
        "content": content,
        "sources": _selected_source_names(),
        "created_at": _now_iso(),
    }
    st.session_state.setdefault("notes", []).append(note)
    storage.save_notes(st.session_state["notes"])
    st.toast("Als Notiz gespeichert")


def _save_note_from_all_sources_summary(content: str) -> None:
    note = {
        "content": content,
        "sources": _all_source_names(),
        "created_at": _now_iso(),
    }
    st.session_state.setdefault("notes", []).append(note)
    storage.save_notes(st.session_state["notes"])
    st.toast("Als Notiz gespeichert")


def render_sources_panel() -> None:
    st.subheader("Quellen")
    st.markdown(
        """
        <style>
        .source-row {
            margin-bottom: 8px;
        }
        .source-row .source-title {
            margin: 0;
        }
        .source-row .source-meta {
            margin-top: 2px;
            font-size: 0.85rem;
            color: #777;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    def _open_add_sources_dialog() -> None:
        @st.dialog("Quellen hinzufügen")
        def _dialog() -> None:
            st.markdown(
                "<div style='text-align:center; font-size:18px; font-weight:600;'>"
                "Dateien importieren  "
                "&nbsp;"
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("&nbsp;", unsafe_allow_html=True)
            upload_label = "PDF, DOCX, CSV, XLSX, PPTX, Bilder, Audio/Video oder Textdateien hochladen"
            uploaded_files = st.file_uploader(
                upload_label,
                type=[
                    "pdf",
                    "docx",
                    "txt",
                    "md",
                    "csv",
                    "xlsx",
                    "pptx",
                    "png",
                    "jpg",
                    "jpeg",
                    "webp",
                    "gif",
                    "mp3",
                    "wav",
                    "m4a",
                    "aac",
                    "flac",
                    "ogg",
                    "opus",
                    "mp4",
                    "mov",
                    "mkv",
                    "webm",
                    "avi",
                ],
                accept_multiple_files=True,
                label_visibility="collapsed",
                key="dialog_file_uploader",
            )
            upload_meta = st.text_input(
                "Metainfo", value="Upload • Heute", key="dialog_upload_meta"
            )
            if uploaded_files and st.button(
                "Dokumente importieren", width="stretch", key="dialog_import"
            ):
                imported = 0
                for file in uploaded_files:
                    try:
                        payload = ingestion.extract_document_payload(
                            file.name, file.getvalue()
                        )
                    except ValueError as exc:
                        st.error(f"{file.name}: {exc}")
                        continue
                    _add_document_payload(
                        payload, upload_meta or f"Upload • {datetime.now():%d.%m.%Y}"
                    )
                    imported += 1
                if imported:
                    st.toast(f"{imported} Dokument(e) importiert")
                    st.rerun()

            st.markdown(
                "<hr>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div style='text-align:center; font-size:18px; font-weight:600;'>"
                "Im Web suchen & importieren  "
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown("&nbsp;", unsafe_allow_html=True)
            search_cols = st.columns([0.85, 0.15])
            search_query = search_cols[0].text_input(
                "Im Web nach neuen Quellen suchen",
                placeholder="Im Web nach neuen Quellen suchen",
                label_visibility="collapsed",
                key="dialog_search_query",
            )
            if search_cols[1].button("➜", width="stretch", key="dialog_search_button"):
                if search_query:
                    st.session_state["dialog_search_trigger"] = True
            filter_cols = st.columns([0.3, 0.4, 0.3])
            filter_cols[0].selectbox(
                "Suchquelle",
                ["Web", "YouTube"],
                key="dialog_search_source",
                label_visibility="collapsed",
            )
            filter_cols[1].selectbox(
                "Suchmodus",
                ["Schnelle Recherche", "Deep Research"],
                key="dialog_search_mode",
                label_visibility="collapsed",
            )
            filter_cols[2].write("")
            if search_query and st.session_state.get("dialog_search_trigger"):
                results = ingestion.search_web(search_query)
                with st.container(border=True):
                    st.caption("Vorschläge aus Web & System APIs")
                    for idx, result in enumerate(results):
                        st.markdown(f"**{result['title']}**  — {result['description']}")
                        st.caption(result["meta"])
                        if st.button("Übernehmen", key=f"dialog_web_result_{idx}"):
                            _add_source(
                                result["title"],
                                result["type"],
                                result["meta"],
                                result.get("description"),
                            )
                            st.toast("Quelle übernommen")

        _dialog()

    #    def _open_rename_output_dialog(output_id: str, title: str) -> None:
    #        @st.dialog("Studio-Ausgabe umbenennen")
    #        def _dialog() -> None:
    #            new_title = st.text_input(
    #                "Neuer Titel",
    #                value=title,
    #                key=f"rename_output_input_{output_id}",
    #            ).strip()
    #            confirm_col, cancel_col = st.columns(2)
    #            if confirm_col.button(
    #                "Speichern",
    #                key=f"confirm_output_rename_{output_id}",
    #                width="stretch",
    #            ):
    #                if new_title:
    #                    updated_outputs = []
    #                    for item in outputs_list:
    #                        if item.get("output_id") == output_id:
    #                            updated_outputs.append({**item, "title": new_title})
    #                        else:
    #                            updated_outputs.append(item)
    #                    st.session_state["studio_outputs"] = updated_outputs
    #                    st.toast("Titel aktualisiert")
    #                st.session_state["confirm_rename_output_id"] = None
    #                st.rerun()
    #            if cancel_col.button(
    #                "Abbrechen",
    #                key=f"cancel_output_rename_{output_id}",
    #                width="stretch",
    #            ):
    #                st.session_state["confirm_rename_output_id"] = None
    #                st.rerun()
    #
    #        _dialog()

    def _open_rename_source_dialog(source_id: str, source_name: str) -> None:
        @st.dialog("Quelle umbenennen")
        def _dialog() -> None:
            new_name = st.text_input(
                "Neuer Name",
                value=source_name,
                key=f"source_rename_input_{source_id}",
            )
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Speichern",
                key=f"confirm_source_rename_{source_id}",
                width="stretch",
            ):
                st.session_state["confirm_rename_source_id"] = None
                _rename_source(source_id, new_name)
            if cancel_col.button(
                "Abbrechen",
                key=f"cancel_source_rename_{source_id}",
                width="stretch",
            ):
                st.session_state["confirm_rename_source_id"] = None
                st.rerun()

        _dialog()

    def _open_bulk_delete_dialog(selected_ids: List[str]) -> None:
        @st.dialog("Quellen löschen")
        def _dialog() -> None:
            st.write(f"{len(selected_ids)} Quelle(n) wirklich löschen?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Löschen", key="confirm_bulk_delete_dialog", width="stretch"
            ):
                st.session_state["confirm_bulk_delete"] = False
                _delete_sources(selected_ids)
            if cancel_col.button(
                "Abbrechen", key="cancel_bulk_delete_dialog", width="stretch"
            ):
                st.session_state["confirm_bulk_delete"] = False
                st.rerun()

        _dialog()

    def _open_delete_source_dialog(source_id: str, source_name: str) -> None:
        dialog_title = f"Quelle löschen: {source_name}"

        @st.dialog(dialog_title)
        def _dialog() -> None:
            st.write(f"Quelle **{source_name}** wirklich löschen?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Löschen", key="confirm_remove_dialog", width="stretch"
            ):
                st.session_state["confirm_delete_source_id"] = None
                st.session_state["confirm_delete_source_name"] = None
                _delete_sources([source_id])
            if cancel_col.button(
                "Abbrechen", key="cancel_remove_dialog", width="stretch"
            ):
                st.session_state["confirm_delete_source_id"] = None
                st.session_state["confirm_delete_source_name"] = None
                st.rerun()

        _dialog()

    if st.button("＋ Quellen hinzufügen", width="stretch", key="open_add_sources"):
        _open_add_sources_dialog()
    connector_options = list(connectors.AVAILABLE_CONNECTORS.keys())
    connector_selection = st.multiselect(
        "System-Konnektoren verbinden",
        options=connector_options,
        format_func=lambda key: connectors.AVAILABLE_CONNECTORS[key].name,
        default=st.session_state["config"].get("enabled_connectors", []),
    )
    if connector_selection and st.button("Quellen abrufen", key="fetch_connectors"):
        connector_results = connectors.collect_connector_results(connector_selection)
        with st.container(border=True):
            st.caption("Ergebnisse aus verbundenen Systemen")
            for idx, result in enumerate(connector_results):
                st.markdown(f"**{result.title}**  — {result.description}")
                st.caption(result.meta)
                if st.button("Importieren", key=f"connector_result_{idx}"):
                    _add_source(
                        result.title, result.type_label, result.meta, result.description
                    )
    sources = st.session_state["sources"]
    if sources:
        all_selected = all(src.selected for src in sources)
        select_all_choice = st.checkbox("Alle Quellen auswählen", value=all_selected)
        if select_all_choice != all_selected:
            _set_all_sources(select_all_choice)
        selected_ids = [src.id for src in sources if src.selected]
        bulk_cols = st.columns([0.2, 0.2, 0.6])
        with bulk_cols[0]:
            if st.button(
                "🗑️",
                disabled=not selected_ids,
                help="Entfernt alle markierten Quellen aus dem Projekt.",
                width="content",
                key="bulk_delete_button",
            ):
                st.session_state["confirm_bulk_delete"] = True
        if st.session_state.get("confirm_bulk_delete") and selected_ids:
            _open_bulk_delete_dialog(selected_ids)
        bulk_cols[1].markdown(
            f"<div style='white-space: nowrap;'>{len(selected_ids)} ausgewählt</div>",
            unsafe_allow_html=True,
        )
        for src in sources:
            cols = st.columns([0.08, 0.74, 0.18])
            cols[0].checkbox(
                label=f"Quelle auswählen: {src.name}",
                key=f"src_{src.id}",
                on_change=lambda sid=src.id: _toggle_source(sid),
                label_visibility="collapsed",
            )
            timestamp = _format_relative_timestamp(getattr(src, "created_at", None))
            cols[1].markdown(
                f"""
                <div class="source-row">
                    <div class="source-title"><strong>{_truncate_label(src.name, 56)}</strong></div>
                    <div class="source-meta">{src.type_label} • {timestamp}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with cols[2]:
                with st.popover("", width="stretch"):
                    if st.button(
                        "Umbenennen",
                        key=f"source_rename_{src.id}",
                        icon=":material/edit:",
                        icon_position="left",
                        width="stretch",
                    ):
                        st.session_state["confirm_rename_source_id"] = src.id
                        _open_rename_source_dialog(src.id, src.name)
                    elif st.session_state.get("confirm_rename_source_id") == src.id:
                        _open_rename_source_dialog(src.id, src.name)
                    source_download = (
                        f"# {src.name}\n\n"
                        f"Typ: {src.type_label}\n\n"
                        f"Meta: {src.meta}\n"
                    )
                    st.download_button(
                        ":material/download: Herunterladen",
                        data=source_download,
                        file_name=_build_download_filename(
                            src.name, src.created_at, "md"
                        ),
                        mime="text/markdown",
                        key=f"source_download_{src.id}",
                        width="stretch",
                    )
                    st.markdown(
                        "<div class='menu-divider'></div>", unsafe_allow_html=True
                    )
                    if st.button(
                        "Teilen",
                        key=f"source_share_{src.id}",
                        icon=":material/share:",
                        icon_position="left",
                        width="stretch",
                    ):
                        st.toast("Teilen ist bald verfügbar")
                    if st.button(
                        "Löschen",
                        key=f"source_delete_{src.id}",
                        icon=":material/delete:",
                        icon_position="left",
                        width="stretch",
                        help="menu-danger",
                    ):
                        st.session_state["confirm_delete_source_id"] = src.id
                        st.session_state["confirm_delete_source_name"] = src.name
                        st.rerun()
        delete_source_id = st.session_state.get("confirm_delete_source_id")
        delete_source_name = st.session_state.get("confirm_delete_source_name")
        if delete_source_id:
            _open_delete_source_dialog(delete_source_id, delete_source_name or "")
    else:
        st.caption(
            "Noch keine Quellen vorhanden. Füge neue Dokumente hinzu oder verbinde Connectoren."
        )
    st.caption(
        "Diese Liste zeigt deine lokalen Quellen. Der echte Service lädt Daten dynamisch über MCP/System APIs."
    )


def render_chat_panel() -> None:
    st.subheader("Chat")
    all_source_names = _all_source_names()
    all_source_count = len(all_source_names)
    current_signature = _sources_signature(all_source_names)
    stored_signature = st.session_state.get("all_sources_summary_signature")
    if stored_signature != current_signature:
        st.session_state["all_sources_summary_stale"] = True
    # with st.container(border=True, height="calc(100vh - 260px)"):
    with st.container(border=True, height=900, gap="xxsmall"):
        with st.expander(
            f"Zusammenfassung aller Quellen ({all_source_count} Quellen)",
            expanded=True,
        ):
            is_stale = bool(st.session_state.get("all_sources_summary_stale"))
            summary_content = str(
                st.session_state.get("all_sources_summary_content") or ""
            ).strip()
            if not all_source_count:
                st.caption("Noch keine Quellen in der Bibliothek.")
            elif summary_content:
                st.markdown(summary_content)
            else:
                st.caption("Noch keine Zusammenfassung generiert. Bitte aktualisieren.")

            controls = st.columns([0.74, 0.13, 0.13])
            stored_source_count = st.session_state.get(
                "all_sources_summary_source_count"
            )
            used_count = (
                int(stored_source_count)
                if isinstance(stored_source_count, (int, float, str))
                and str(stored_source_count).strip() != ""
                else 0
            )
            delta = all_source_count - used_count
            delta_text = ""
            if used_count and delta:
                delta_text = f" · Δ {delta:+d}"
            status_text = (
                f"Quellen in der Bibliothek: {all_source_count} · Verwendet: {used_count}"
                f"{delta_text}"
            )
            if is_stale:
                status_text = f"{status_text} · Neue Quellen erkannt"
            controls[0].caption(status_text)
            with controls[1]:
                if st.button(
                    "",
                    key="update_all_sources_summary",
                    icon=":material/refresh:",
                    help="Zusammenfassung aktualisieren",
                    width="stretch",
                    disabled=not bool(all_source_count),
                ):
                    st.session_state["all_sources_summary_content"] = (
                        _generate_all_sources_summary() if all_source_count else ""
                    )
                    st.session_state["all_sources_summary_signature"] = (
                        current_signature
                    )
                    st.session_state["all_sources_summary_generated_at"] = _now_iso()
                    st.session_state["all_sources_summary_source_count"] = (
                        all_source_count
                    )
                    st.session_state["all_sources_summary_stale"] = False
                    storage.save_all_sources_summary(
                        {
                            "content": st.session_state.get(
                                "all_sources_summary_content"
                            )
                            or "",
                            "signature": st.session_state.get(
                                "all_sources_summary_signature"
                            ),
                            "generated_at": st.session_state.get(
                                "all_sources_summary_generated_at"
                            ),
                            "source_count": st.session_state.get(
                                "all_sources_summary_source_count"
                            ),
                            "stale": st.session_state.get("all_sources_summary_stale"),
                        }
                    )
                    st.rerun()
            with controls[2]:
                if st.button(
                    "",
                    key="pin_all_sources_summary",
                    icon=":material/push_pin:",
                    help="Zusammenfassung als Notiz speichern",
                    width="stretch",
                    disabled=not bool(summary_content),
                ):
                    _save_note_from_all_sources_summary(summary_content)
        for idx, message in enumerate(st.session_state["chat_history"]):
            with st.chat_message(message["role"]):
                message_key = (
                    f"{message['role']}_{hash(message.get('content', ''))}_{idx}"
                )
                if message["role"] == "assistant":
                    trace = message.get("trace") if isinstance(message, dict) else None
                    if trace:
                        with st.expander("Agent Actions", expanded=False):
                            _render_thinking_trace(trace)
                if message.get("tool_calls"):
                    st.session_state["persistent_tool_calls"][message_key] = message[
                        "tool_calls"
                    ]
                if message_key in st.session_state.get("persistent_tool_calls", {}):
                    with st.expander("Tool Calls", expanded=False):
                        _display_tool_calls(
                            st.container(),
                            st.session_state["persistent_tool_calls"][message_key],
                        )
                message_images = (
                    message.get("images") if isinstance(message, dict) else None
                )
                if message["role"] == "assistant":
                    thinking, response_body = _split_thinking_from_response(
                        message["content"]
                    )
                    display_content = response_body or message["content"]
                    if thinking:
                        with st.expander("Agent Thinking", expanded=False):
                            st.code(thinking, language="text")
                    _render_chat_markdown(display_content)
                    if message_images:
                        cols = st.columns(2)
                        for img_idx, image in enumerate(message_images):
                            image_path = (
                                image.get("filepath")
                                if isinstance(image, dict)
                                else None
                            )
                            if not image_path:
                                continue
                            with cols[img_idx % 2]:
                                st.image(
                                    image_path,
                                    caption=(
                                        image.get("name")
                                        if isinstance(image, dict)
                                        else None
                                    ),
                                    use_container_width=True,
                                )
                    if st.button("In Notiz speichern", key=f"save_note_{idx}"):
                        _save_note_from_message(display_content)
                else:
                    _render_chat_markdown(message["content"])
                    if message_images:
                        cols = st.columns(2)
                        for img_idx, image in enumerate(message_images):
                            image_path = (
                                image.get("filepath")
                                if isinstance(image, dict)
                                else None
                            )
                            if not image_path:
                                continue
                            with cols[img_idx % 2]:
                                st.image(
                                    image_path,
                                    caption=(
                                        image.get("name")
                                        if isinstance(image, dict)
                                        else None
                                    ),
                                    use_container_width=True,
                                )
    pending_prompt = st.session_state.pop("pending_chat_prompt", None)
    pending_images = st.session_state.pop("pending_chat_images", None)
    if pending_prompt:
        agent_config = _get_agent_config("chat")
        with st.chat_message("assistant"):
            tool_calls_container = st.empty()
            response_container = st.empty()

            def _on_response(value: str) -> None:
                rendered = _normalize_chat_response_text(value)
                with response_container.container():
                    _render_chat_markdown(rendered)

            def _on_tools(tools: List[object]) -> None:
                _display_tool_calls(tool_calls_container, tools)

            turn = ChatTurnInput(
                prompt=pending_prompt,
                sources=_selected_source_names(),
                notes=st.session_state["notes"],
                session_id=st.session_state.get("session_id"),
                user_id=user_memory.resolve_user_id(st.session_state),
                agent_config=agent_config,
                images=pending_images,
                stream_events=bool((agent_config or {}).get("stream_events", True)),
                log_stream_events=bool(
                    st.session_state.get("config", {}).get("log_stream_events")
                ),
                on_response=_on_response,
                on_tools=_on_tools,
            )
            result = run_chat_turn(turn)

        _append_chat(
            "assistant",
            result.response,
            trace=result.trace,
            tool_calls=result.tool_calls,
        )
        st.toast("Antwort generiert – siehe Chat")
        st.rerun()
    selected_count = len(_selected_source_names())
    user_submission = st.chat_input(
        f"Frage stellen oder Audio aufnehmen… ({selected_count} Quellen ausgewählt)",
        accept_audio=True,
        accept_file=True,
        file_type=["jpg", "jpeg", "png"],
    )
    if user_submission:
        user_prompt = (user_submission.text or "").strip()
        uploaded_images: List[Dict[str, object]] = []
        image_artifacts: List[Image] = []
        if getattr(user_submission, "files", None):
            uploaded_images, image_artifacts = _save_uploaded_images(
                list(user_submission.files)
            )
            if user_prompt:
                if len(uploaded_images) == 1:
                    user_prompt = (
                        f"{user_prompt} (Bild: {uploaded_images[0].get('name')})"
                    )
                else:
                    filenames = ", ".join(
                        img.get("name", "Bild") for img in uploaded_images
                    )
                    user_prompt = f"{user_prompt} (Bilder: {filenames})"
            else:
                if len(uploaded_images) == 1:
                    user_prompt = (
                        f"Bitte analysiere das Bild {uploaded_images[0].get('name')}."
                    )
                else:
                    filenames = ", ".join(
                        img.get("name", "Bild") for img in uploaded_images
                    )
                    user_prompt = f"Bitte analysiere die Bilder: {filenames}."
        if user_submission.audio:
            audio_file = user_submission.audio
            audio_name = getattr(audio_file, "name", "audio.wav")
            try:
                payload = ingestion.extract_document_payload(
                    audio_name, audio_file.getvalue()
                )
                audio_text = payload.get("body", "").strip()
                if audio_text:
                    user_prompt = "\n\n".join(
                        part for part in (user_prompt, f"[Audio]\n{audio_text}") if part
                    )
            except ValueError as exc:
                st.error(f"Audio: {exc}")
        if not user_prompt:
            st.warning("Bitte Text eingeben oder Audio aufnehmen.")
            return
        _append_chat("user", user_prompt, images=uploaded_images)
        if st.session_state.get("config", {}).get("log_user_requests", True):
            _LOGGER.info("User request: %s", user_prompt)
        st.session_state["pending_chat_prompt"] = user_prompt
        if image_artifacts:
            st.session_state["pending_chat_images"] = image_artifacts
        st.rerun()


def render_studio_panel() -> None:
    st.subheader("Studio")
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Wähle eine Vorlage, generiere Inhalte und verwalte deine Artefakte.")

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
        .studio-card-anchor {
            display: none;
        }
        div[data-testid="stVerticalBlock"]:has(div[data-testid="stVerticalBlock"] .studio-card-anchor) {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            margin-bottom: 0 !important;
        }
        div[data-testid="column"]:has(.studio-card-anchor) {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        div[data-testid="column"]:has(.studio-card-anchor) > div {
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            box-shadow: none !important;
        }
        div[data-testid="stHorizontalBlock"] > div:has(.studio-card-anchor) {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        div[data-testid="stVerticalBlock"]:has(div[data-testid="stVerticalBlock"] .studio-card-anchor):hover {
            border-color: transparent !important;
            box-shadow: none !important;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) {
            #border: 1px solid rgba(0,0,0,0.05);
            border-radius: 8px;
            padding: 8px;
            #background: #fff;
            background: transparent;
            margin-bottom: 4px;
            position: relative;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 8px !important;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor):hover {
            border-color: rgba(0,0,0,0.12);
            box-shadow: none;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) > div {
            margin: 0px 0px -12px 0px !important;
            padding: 0px !important;
        }
        .studio-desc {
            min-height: 44px;
            color: #666;
            font-size: 0.9rem;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        .studio-meta {
            color: #8a8a8a;
            font-size: 0.8rem;
            margin-top: 6px;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) div[data-testid="stPopover"] button {
            border-radius: 8px !important;
            min-width: 36px !important;
            width: 36px !important;
            height: 32px !important;
            padding: 0 !important;
            padding-right: 9px !important;
            line-height: 1 !important;
            white-space: nowrap !important;
            overflow: hidden !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin-right: 0px !important;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) div[data-testid="stPopover"] button > div {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) div[data-testid="stPopover"] button svg,
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) div[data-testid="stPopover"] button span {
            display: block !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(.studio-card-anchor) button[kind="secondary"] {
            min-height: 32px;
            font-size: 0.9rem;
            padding: 0 12px !important;
            white-space: nowrap !important;
        }
        button[title^="studio-generate-"] {
            width: 100% !important;
            justify-content: flex-start !important;
            text-align: left !important;
            border-radius: 12px !important;
            min-height: 32px !important;
            height: 32px !important;
        }
        button[title^="studio-generate-"] > div {
            justify-content: flex-start !important;
            gap: 8px !important;
        }
        .studio-card-header {
            background-color: var(--studio-color) !important;
        }
        div[data-testid="stPopover"] div[role="dialog"] {
            min-width: 220px;
        }
        .menu-divider {
            height: 1px;
            background: rgba(0,0,0,0.08);
            margin: 6px 0;
        }
        button[title="menu-danger"] {
            color: #b91c1c !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    templates = st.session_state["studio_templates"]
    if templates:
        st.session_state.setdefault(
            "studio_selected_template", templates[0].template_id
        )
        columns = st.columns(2)
        for idx, template in enumerate(templates):
            _render_studio_template_card(columns[idx % 2], template)
    else:
        st.info("Noch keine Vorlagen definiert.")

    st.divider()
    _render_studio_outputs_section()
    st.divider()
    _render_studio_notes_section()


def _render_studio_template_card(
    column: st.delta_generator.DeltaGenerator, template: StudioTemplate
) -> None:
    lang_key = f"studio_lang_{template.template_id}"
    tone_key = f"studio_tone_{template.template_id}"
    instr_key = f"studio_instr_{template.template_id}"
    user_prompt_key = f"studio_user_prompt_{template.template_id}"
    st.session_state.setdefault(lang_key, template.defaults.get("language", "Deutsch"))
    st.session_state.setdefault(tone_key, template.defaults.get("tone", "Neutral"))
    st.session_state.setdefault(
        instr_key,
        template.defaults.get("instructions")
        or template.agent.get("instructions")
        or template.description,
    )
    st.session_state.setdefault(user_prompt_key, "")
    is_selected = (
        st.session_state.get("studio_selected_template") == template.template_id
    )
    outputs_list = _get_studio_outputs_list()

    with column.container():
        selected_marker = " selected" if is_selected else ""
        column.markdown(
            f"<div class='studio-card-anchor{selected_marker}'></div>",
            unsafe_allow_html=True,
        )
        column.markdown(
            f"""
            <style>
            button[title="studio-generate-{template.template_id}"] {{
                background-color: {template.color} !important;
                border: 1px solid rgba(0,0,0,0.04) !important;
                border-radius: 12px !important;
                font-weight: 500 !important;
                justify-content: flex-start !important;
                color: #111 !important;
            }}
            button[title="studio-generate-{template.template_id}"]:hover {{
                background-color: {template.color} !important;
                filter: brightness(0.98);
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        header_cols = column.columns([0.82, 0.18])
        generate_label = f"{template.icon} {template.title}"
        if header_cols[0].button(
            generate_label,
            key=f"studio_generate_{template.template_id}",
            width="stretch",
            help=f"studio-generate-{template.template_id}",
        ):
            st.session_state["studio_selected_template"] = template.template_id
            language = st.session_state.get(lang_key, "Deutsch")
            tone = st.session_state.get(tone_key, "Neutral")
            instructions = st.session_state.get(instr_key, template.description)
            user_prompt = st.session_state.get(user_prompt_key, "").strip()
            prompt = f"Sprache: {language}\nTon: {tone}\nAnweisungen: {instructions}"
            if user_prompt:
                prompt = f"{prompt}\nBenutzerprompt: {user_prompt}"
            if template.template_id == "reports":
                summary_goal = (
                    "Erstelle eine umfassende, prägnante Zusammenfassung der ausgewählten Quellen. "
                    "Strukturiere mit Überschriften und fasse Kernaussagen zusammen."
                )
                contexts = retrieval.query_similar(
                    "Zusammenfassung der ausgewählten Quellen"
                )
                context_chunks = "\n\n".join(
                    f"Snippet: {ctx.get('text')}\nMeta: {ctx.get('meta')}"
                    for ctx in contexts
                )
                prompt = (
                    f"{prompt}\nZiel: {summary_goal}\n\n"
                    f"Kontext (RAG):\n{context_chunks or '-'}"
                )
            selected_sources = _selected_source_names()
            if template.template_id == "infographic":
                agent_config = _get_agent_config(template.template_id) or template.agent
                contexts = retrieval.query_similar(
                    "Zusammenfassung der ausgewählten Quellen für eine Infografik"
                )
                context_chunks = "\n\n".join(
                    f"Snippet: {ctx.get('text')}\nMeta: {ctx.get('meta')}"
                    for ctx in contexts
                )
                output = pipelines.generate_infographic_artifact(
                    template.title,
                    prompt,
                    selected_sources,
                    context_chunks,
                    agent_config,
                    image_model=st.session_state.get("config", {}).get(
                        "image_model", "gpt-image-1"
                    ),
                )
            else:
                agent_config = _get_agent_config(template.template_id) or template.agent
                output = _generate_studio_output(
                    template.title,
                    prompt,
                    selected_sources,
                    agent_config,
                )
            normalized = _normalize_studio_output_payload(output)
            normalized.setdefault("sources", _selected_source_names())
            normalized["generated_at"] = (
                normalized.get("generated_at") or datetime.now(timezone.utc).isoformat()
            )
            outputs_list = _get_studio_outputs_list()
            output_id = uuid4().hex
            outputs_list.insert(
                0,
                {
                    "output_id": output_id,
                    "template_id": template.template_id,
                    "title": template.title,
                    "content": normalized.get("content", ""),
                    "sources": normalized.get("sources", []),
                    "generated_at": normalized.get("generated_at"),
                    "image_path": normalized.get("image_path"),
                },
            )
            st.session_state["studio_outputs"] = outputs_list
            _persist_studio_outputs()
            st.session_state["studio_open_output"] = output_id
            st.toast(f"{template.title} aktualisiert")
        with header_cols[1].popover("", width="stretch"):
            st.caption(template.description)
            st.caption("Vorlage konfigurieren")
            st.text_area(
                "Zusätzlicher Prompt",
                key=user_prompt_key,
                placeholder="Optionaler Zusatzprompt für diese Vorlage",
                height=90,
            )
            st.selectbox("Sprache", ["Deutsch", "Englisch"], key=lang_key)
            st.selectbox(
                "Ton", ["Neutral", "Prägnant", "Analytisch", "Kreativ"], key=tone_key
            )
            st.text_area(
                "Anweisungen",
                key=instr_key,
                placeholder="z. B. Struktur, Stil, Umfang",
                height=120,
            )


def _render_studio_configuration(
    container: st.delta_generator.DeltaGenerator,
) -> None:
    container.subheader("Studio Vorlagen")
    templates = st.session_state.get("studio_templates", [])
    if not isinstance(templates, list) or not templates:
        container.caption("Keine Studio-Vorlagen verfügbar.")
        return
    _render_studio_settings_panel(templates)


def _render_studio_settings_panel(templates: List[StudioTemplate]) -> None:
    titles = [template.title for template in templates]
    template_ids = [template.template_id for template in templates]
    selected_id = st.session_state.get("studio_selected_template")
    if selected_id not in template_ids:
        selected_id = template_ids[0] if template_ids else None
    selected_title = st.selectbox(
        "Vorlage",
        options=titles,
        index=template_ids.index(selected_id) if selected_id in template_ids else 0,
        key="studio_selected_template_title",
    )
    selected_template = next(
        (template for template in templates if template.title == selected_title), None
    )
    if not selected_template:
        return
    st.session_state["studio_selected_template"] = selected_template.template_id
    lang_key = f"studio_lang_{selected_template.template_id}"
    tone_key = f"studio_tone_{selected_template.template_id}"
    instr_key = f"studio_instr_{selected_template.template_id}"
    st.session_state.setdefault(
        lang_key, selected_template.defaults.get("language", "Deutsch")
    )
    st.session_state.setdefault(
        tone_key, selected_template.defaults.get("tone", "Neutral")
    )
    st.session_state.setdefault(
        instr_key,
        selected_template.defaults.get("instructions")
        or selected_template.agent.get("instructions")
        or selected_template.description,
    )

    st.selectbox(
        "Sprache",
        ["Deutsch", "English"],
        key=lang_key,
    )
    st.selectbox(
        "Ton",
        ["Neutral", "Förmlich", "Locker"],
        key=tone_key,
    )
    st.text_area(
        "Anweisungen",
        key=instr_key,
        height=140,
    )
    if st.button("Schließen", key="studio_settings_close"):
        st.session_state["studio_settings_open"] = False
        st.rerun()


def _render_studio_outputs_section() -> None:
    st.markdown("### Studio-Ergebnisse")
    outputs_list = _get_studio_outputs_list()
    if not outputs_list:
        st.caption("Noch keine Studio-Ausgaben generiert.")
        return

    open_id = st.session_state.get("studio_open_output")
    outputs_by_template: Dict[str, List[Dict[str, object]]] = {}
    for entry in outputs_list:
        template_id = str(entry.get("template_id", ""))
        outputs_by_template.setdefault(template_id, []).append(entry)
    ordered_outputs: List[Dict[str, object]] = []
    for template in st.session_state.get("studio_templates", []):
        ordered_outputs.extend(outputs_by_template.get(template.template_id, []))
    if not ordered_outputs:
        ordered_outputs = outputs_list

    def _open_delete_output_dialog(output_id: str, title: str) -> None:
        @st.dialog("Studio-Ausgabe löschen")
        def _dialog() -> None:
            st.write(f"Studio-Ausgabe **{title}** wirklich löschen?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Löschen",
                key=f"confirm_output_delete_{output_id}",
                width="stretch",
            ):
                updated_outputs = [
                    item for item in outputs_list if item.get("output_id") != output_id
                ]
                st.session_state["studio_outputs"] = updated_outputs
                _persist_studio_outputs()
                st.session_state["confirm_delete_output_id"] = None
                st.session_state["confirm_delete_output_title"] = None
                if st.session_state.get("studio_open_output") == output_id:
                    st.session_state["studio_open_output"] = None
                st.toast(f"{title} gelöscht")
                st.rerun()
            if cancel_col.button(
                "Abbrechen",
                key=f"cancel_output_delete_{output_id}",
                width="stretch",
            ):
                st.session_state["confirm_delete_output_id"] = None
                st.session_state["confirm_delete_output_title"] = None
                st.rerun()

        _dialog()

    def _open_rename_output_dialog(output_id: str, title: str) -> None:
        @st.dialog("Studio-Ausgabe umbenennen")
        def _dialog() -> None:
            new_title = st.text_input(
                "Neuer Titel",
                value=title,
                key=f"rename_output_input_{output_id}",
            ).strip()
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Speichern",
                key=f"confirm_output_rename_{output_id}",
                width="stretch",
            ):
                if new_title:
                    updated_outputs = []
                    for item in outputs_list:
                        if item.get("output_id") == output_id:
                            updated_outputs.append({**item, "title": new_title})
                        else:
                            updated_outputs.append(item)
                    st.session_state["studio_outputs"] = updated_outputs
                    _persist_studio_outputs()
                    st.toast("Titel aktualisiert")
                st.session_state["confirm_rename_output_id"] = None
                st.rerun()
            if cancel_col.button(
                "Abbrechen",
                key=f"cancel_output_rename_{output_id}",
                width="stretch",
            ):
                st.session_state["confirm_rename_output_id"] = None
                st.rerun()

        _dialog()

    for entry in ordered_outputs:
        template_id = str(entry.get("template_id", ""))
        template = _get_studio_template(template_id)
        icon = template.icon if template else "🧩"
        title = str(entry.get("title") or (template.title if template else template_id))
        sources = entry.get("sources") or []
        output_id = entry.get("output_id") or uuid4().hex
        generated_at = entry.get("generated_at")
        meta_bits: List[str] = []
        if sources:
            meta_bits.append(f"{len(sources)} Quellen")
        meta_bits.append(_format_relative_timestamp(generated_at))
        with st.expander(f"{icon} {title}", expanded=output_id == open_id):
            st.caption(" • ".join(meta_bits))
            content = str(entry.get("content", ""))
            image_path = entry.get("image_path")
            if image_path:
                try:
                    st.image(image_path, width="stretch")
                except Exception:  # pragma: no cover - file IO errors
                    st.caption("Infografik konnte nicht geladen werden.")
            if content.strip():
                st.markdown(content)
            else:
                st.caption("Keine Inhalte verfügbar.")
            menu_cols = st.columns([0.82, 0.18])
            with menu_cols[1]:
                with st.popover("", width="stretch"):
                    if st.button(
                        "Umbenennen",
                        key=f"studio_output_rename_{output_id}",
                        icon=":material/edit:",
                        icon_position="left",
                        width="stretch",
                    ):
                        st.session_state["confirm_rename_output_id"] = output_id
                        _open_rename_output_dialog(output_id, title)
                    elif st.session_state.get("confirm_rename_output_id") == output_id:
                        _open_rename_output_dialog(output_id, title)
                    if st.button(
                        "Als Quelle nutzen",
                        key=f"studio_output_source_{output_id}",
                        icon=":material/push_pin:",
                        icon_position="left",
                        width="stretch",
                    ):
                        output_title = f"Studio: {title}"
                        _add_source(
                            output_title,
                            "Studio Output",
                            _format_absolute_date(generated_at),
                            content,
                        )
                        st.toast("Studio-Ausgabe als Quelle hinzugefügt")
                        st.rerun()
                    st.download_button(
                        ":material/download: Herunterladen",
                        data=exports.render_markdown(title, content),
                        file_name=_build_download_filename(title, generated_at, "md"),
                        mime="text/markdown",
                        key=f"studio_output_download_{output_id}",
                        width="stretch",
                    )
                    st.markdown(
                        "<div class='menu-divider'></div>", unsafe_allow_html=True
                    )
                    if st.button(
                        "Teilen",
                        key=f"studio_output_share_{output_id}",
                        icon=":material/share:",
                        icon_position="left",
                        width="stretch",
                    ):
                        st.toast("Teilen ist bald verfügbar")
                    if st.button(
                        "Löschen",
                        key=f"studio_output_delete_{output_id}",
                        icon=":material/delete:",
                        icon_position="left",
                        width="stretch",
                        help="menu-danger",
                    ):
                        st.session_state["confirm_delete_output_id"] = output_id
                        st.session_state["confirm_delete_output_title"] = title
                        _open_delete_output_dialog(output_id, title)
                    elif st.session_state.get("confirm_delete_output_id") == output_id:
                        _open_delete_output_dialog(output_id, title)


def _render_studio_notes_section() -> None:
    st.markdown(
        "<h3 class='chat-notes-heading'>Chat-Notizen</h3>",
        unsafe_allow_html=True,
    )
    notes = st.session_state.get("notes", [])
    if not notes:
        st.caption(
            "Noch keine Notizen gespeichert. Speichere Antworten direkt aus dem Chat."
        )
    st.markdown(
        """
        <style>
        .chat-notes-heading {
            margin-top: 0;
            margin-bottom: 2px;
            font-size: 1.3rem;
        }
        #chat-notes-anchor {
            display: none;
        }
        div[data-testid="stVerticalBlock"]:has(#chat-notes-anchor) {
            gap: 0.25rem !important;
        }
        div[data-testid="stVerticalBlock"]:has(#chat-notes-anchor) > div {
            margin: 0 !important;
            padding: 0 !important;
        }
        .note-row [data-testid="column"] {
            padding: 0 !important;
        }
        .note-block [data-testid="stExpander"] > details > summary {
            display: flex;
            align-items: center;
            padding: 0;
        }
        .note-block [data-testid="stExpander"] {
            margin: 0 !important;
        }
        .note-block [data-testid="stExpander"] > details > summary p {
            font-weight: 600;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
        }
        .note-actions {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
        }
        .note-actions button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 6px !important;
            font-size: 1.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div id="chat-notes-anchor"></div>', unsafe_allow_html=True)

    def _open_delete_note_dialog(note_index: int, title: str) -> None:
        @st.dialog("Notiz löschen")
        def _dialog() -> None:
            st.write(f"Notiz **{title}** wirklich löschen?")
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Löschen",
                key=f"confirm_note_delete_{note_index}",
                width="stretch",
            ):
                st.session_state["notes"].pop(note_index)
                storage.save_notes(st.session_state["notes"])
                st.session_state["confirm_delete_note_index"] = None
                st.session_state["confirm_delete_note_title"] = None
                st.toast("Notiz gelöscht")
                st.rerun()
            if cancel_col.button(
                "Abbrechen",
                key=f"cancel_note_delete_{note_index}",
                width="stretch",
            ):
                st.session_state["confirm_delete_note_index"] = None
                st.session_state["confirm_delete_note_title"] = None
                st.rerun()

        _dialog()

    def _open_rename_note_dialog(note_index: int, title: str) -> None:
        @st.dialog("Notiz umbenennen")
        def _dialog() -> None:
            new_title = st.text_input(
                "Neuer Titel",
                value=title,
                key=f"note_rename_input_{note_index}",
            )
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Speichern",
                key=f"confirm_note_rename_{note_index}",
                width="stretch",
            ):
                st.session_state["notes"][note_index]["title"] = (
                    new_title.strip() or title
                )
                storage.save_notes(st.session_state["notes"])
                st.session_state["confirm_rename_note_index"] = None
                st.rerun()
            if cancel_col.button(
                "Abbrechen",
                key=f"cancel_note_rename_{note_index}",
                width="stretch",
            ):
                st.session_state["confirm_rename_note_index"] = None
                st.rerun()

        _dialog()

    for idx, note in enumerate(notes):
        content = note.get("content", "")
        note.setdefault("created_at", _now_iso())
        title = (
            note.get("title") or content.splitlines()[0].strip() or f"Notiz {idx + 1}"
        )
        truncated_title = shorten(title, width=70, placeholder="…")
        sources = note.get("sources", [])
        created_label = _format_absolute_date(note.get("created_at"))
        meta_label = f"{created_label} • {len(sources) or 0} Quelle(n)"
        cols = st.columns([0.9, 0.1], gap="small")
        with cols[0]:
            st.markdown('<div class="note-block">', unsafe_allow_html=True)
            with st.expander(truncated_title, expanded=False):
                st.caption(meta_label)
                if content.strip():
                    _render_chat_markdown(content)
                else:
                    st.write("Keine Inhalte verfügbar.")
                source_names = sources or ["Alle Quellen"]
                st.caption("Quellen: " + ", ".join(source_names))
            st.markdown("</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown('<div class="note-actions">', unsafe_allow_html=True)
            with st.popover("", width="stretch"):
                if st.button(
                    "Umbenennen",
                    key=f"note_rename_button_{idx}",
                    icon=":material/edit:",
                    icon_position="left",
                    width="stretch",
                ):
                    st.session_state["confirm_rename_note_index"] = idx
                    _open_rename_note_dialog(idx, title)
                elif st.session_state.get("confirm_rename_note_index") == idx:
                    _open_rename_note_dialog(idx, title)
                if st.button(
                    "Als Quelle nutzen",
                    key=f"note_source_{idx}",
                    icon=":material/push_pin:",
                    icon_position="left",
                    width="stretch",
                ):
                    note_title = f"Notiz: {title}"
                    _add_source(
                        note_title,
                        "Notiz",
                        _format_absolute_date(note.get("created_at")),
                        content,
                    )
                    st.toast("Notiz als Quelle hinzugefügt")
                    st.rerun()
                st.download_button(
                    ":material/download: Herunterladen",
                    data=content,
                    file_name=_build_download_filename(
                        title, note.get("created_at"), "md"
                    ),
                    mime="text/markdown",
                    key=f"note_export_{idx}",
                    width="stretch",
                )
                st.markdown("<div class='menu-divider'></div>", unsafe_allow_html=True)
                if st.button(
                    "Teilen",
                    key=f"note_share_{idx}",
                    icon=":material/share:",
                    icon_position="left",
                    width="stretch",
                ):
                    st.toast("Teilen ist bald verfügbar")
                if st.button(
                    "Löschen",
                    key=f"note_delete_{idx}",
                    icon=":material/delete:",
                    icon_position="left",
                    width="stretch",
                    help="menu-danger",
                ):
                    st.session_state["confirm_delete_note_index"] = idx
                    st.session_state["confirm_delete_note_title"] = title
                    _open_delete_note_dialog(idx, title)
                elif st.session_state.get("confirm_delete_note_index") == idx:
                    _open_delete_note_dialog(idx, title)
            st.markdown("</div>", unsafe_allow_html=True)

    def _open_add_note_dialog() -> None:
        @st.dialog("Notiz hinzufügen")
        def _dialog() -> None:
            new_content = st.text_area("Notizinhalt", key="note_add_content")
            if st.button("Speichern", key="note_add_save", width="stretch"):
                if new_content.strip():
                    st.session_state.setdefault("notes", []).insert(
                        0,
                        {
                            "content": new_content.strip(),
                            "sources": _selected_source_names(),
                            "created_at": _now_iso(),
                        },
                    )
                    storage.save_notes(st.session_state["notes"])
                    st.toast("Notiz gespeichert")
                    st.rerun()
                else:
                    st.warning("Bitte Inhalt eingeben.")

        _dialog()

    if st.button("Notiz hinzufügen", width="stretch", key="note_add_open"):
        _open_add_note_dialog()


def run_app() -> None:
    configure_page()
    render_sidebar()
    _init_state()

    col_sources, col_chat, col_studio = st.columns([0.25, 0.45, 0.3])
    with col_sources:
        render_sources_panel()
    with col_chat:
        render_chat_panel()
    with col_studio:
        render_studio_panel()


if __name__ == "__main__":
    run_app()
