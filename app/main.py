"""Streamlit entrypoint for the NotebookLM-style MVP."""

from __future__ import annotations

import json
import logging
import sys
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional
from uuid import uuid4
from textwrap import shorten

import streamlit as st
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
import services.agents as agents  # noqa: E402
from services import agents_config  # noqa: E402
from services import exports  # noqa: E402

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
    actions: List[StudioActionConfig] = Field(default_factory=list)
    agent: Dict[str, str] = Field(default_factory=dict)
    defaults: Dict[str, str] = Field(default_factory=dict)


class StudioTemplatesConfig(BaseModel):
    templates: List[StudioTemplateConfig] = Field(default_factory=list)


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


def render_sidebar() -> None:
    st.sidebar.title("HALO Admin")
    section = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Administration", "Configuration", "Account", "Help"],
        index=0,
        key="sidebar_nav",
    )
    st.sidebar.write("Selected:", section)
    st.sidebar.button("New Notebook", width="stretch")
    if section == "Configuration":
        _render_configuration_panel()
    st.sidebar.divider()
    st.sidebar.markdown(
        "Need help? Visit [AGENTS.md](../AGENTS.md) or join the #halo-support channel."
    )


def _init_state() -> None:
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
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {
                "role": "assistant",
                "content": "Willkommen! Frag mich etwas zu deinen Quellen.",
            }
        ]
    if "studio_templates" not in st.session_state:
        st.session_state["studio_templates"] = _load_studio_templates()
    if "notes" not in st.session_state:
        st.session_state["notes"] = storage.load_notes()
    if "studio_outputs" not in st.session_state:
        stored_outputs = storage.load_studio_outputs()
        if stored_outputs:
            st.session_state["studio_outputs"] = stored_outputs
        else:
            st.session_state["studio_outputs"] = []
    elif isinstance(st.session_state.get("studio_outputs"), dict):
        st.session_state["studio_outputs"] = _get_studio_outputs_list()
        storage.save_studio_outputs(st.session_state["studio_outputs"])
    if "config" not in st.session_state:
        stored_config = storage.load_config() or {}
        default_config = {
            "enabled_connectors": list(connectors.AVAILABLE_CONNECTORS.keys()),
            "image_model": "gpt-image-1",
            "log_agent_payload": False,
            "log_agent_response": True,
            "log_agent_errors": True,
            "log_user_requests": True,
        }
        st.session_state["config"] = {**default_config, **stored_config}
    if "agent_configs" not in st.session_state:
        st.session_state["agent_configs"] = agents_config.load_agent_configs()


def _render_configuration_panel() -> None:
    st.sidebar.subheader("Quellen & Connectoren")
    enabled = st.sidebar.multiselect(
        "Aktivierte Connectoren",
        options=list(connectors.AVAILABLE_CONNECTORS.keys()),
        default=st.session_state["config"].get("enabled_connectors", []),
        format_func=lambda key: connectors.AVAILABLE_CONNECTORS[key].name,
    )
    st.sidebar.subheader("Bildgenerierung")
    image_model = st.sidebar.selectbox(
        "Bildmodell",
        options=["gpt-image-1", "dall-e-3"],
        index=["gpt-image-1", "dall-e-3"].index(
            st.session_state["config"].get("image_model", "gpt-image-1")
        ),
    )
    if st.sidebar.button("Speichern", key="save_connectors"):
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
        storage.save_config(st.session_state["config"])
        st.sidebar.success("Connector-Einstellungen aktualisiert")

    st.sidebar.subheader("Agent-Logging")
    st.sidebar.checkbox(
        "Agent payload loggen",
        value=bool(st.session_state["config"].get("log_agent_payload", True)),
        key="log_agent_payload",
    )
    st.sidebar.checkbox(
        "Agent response loggen",
        value=bool(st.session_state["config"].get("log_agent_response", True)),
        key="log_agent_response",
    )
    st.sidebar.checkbox(
        "Agent Fehler loggen",
        value=bool(st.session_state["config"].get("log_agent_errors", True)),
        key="log_agent_errors",
    )
    st.sidebar.checkbox(
        "User Requests loggen",
        value=bool(st.session_state["config"].get("log_user_requests", True)),
        key="log_user_requests",
    )
    agents.set_logging_preferences(
        log_payload=bool(st.session_state.get("log_agent_payload", True)),
        log_response=bool(st.session_state.get("log_agent_response", True)),
        log_errors=bool(st.session_state.get("log_agent_errors", True)),
    )

    st.sidebar.subheader("Agenten")
    agent_configs = st.session_state.get("agent_configs", {})
    agent_ids = sorted(agent_configs.keys())
    if agent_ids:
        name_counts: Dict[str, int] = {}
        for agent_id in agent_ids:
            label = str(agent_configs.get(agent_id, {}).get("name", agent_id))
            name_counts[label] = name_counts.get(label, 0) + 1

        def _format_agent_label(agent_id: str) -> str:
            label = str(agent_configs.get(agent_id, {}).get("name", agent_id))
            if name_counts.get(label, 0) > 1:
                return f"{label} ({agent_id})"
            return label

        selected_agent_id = st.sidebar.selectbox(
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
        member_options = [
            agent_id for agent_id in agent_ids if agent_id != selected_agent_id
        ]
        st.sidebar.checkbox(
            "Aktiviert",
            value=bool(selected_agent.get("enabled", True)),
            key=enabled_key,
        )
        st.sidebar.text_input(
            "Name",
            value=str(selected_agent.get("name", "")),
            key=name_key,
        )
        st.sidebar.text_input(
            "Rolle",
            value=str(selected_agent.get("role", "")),
            key=role_key,
        )
        st.sidebar.text_area(
            "Beschreibung",
            value=str(selected_agent.get("description", "")),
            key=description_key,
            height=100,
        )
        st.sidebar.text_area(
            "Anweisungen",
            value=str(selected_agent.get("instructions", "")),
            key=instructions_key,
            height=160,
        )
        st.sidebar.text_input(
            "Model",
            value=str(selected_agent.get("model", "openai:gpt-5.2")),
            key=model_key,
            help="Format: provider:model (z.B. openai:gpt-5.2)",
        )
        available_tools = {
            "pubmed": "PubMed Suche",
            "wikipedia": "Wikipedia Suche",
            "mermaid": "Mermaid Diagramme",
        }
        raw_tools = selected_agent.get("tools", [])
        normalized_tools: List[str] = []
        if isinstance(raw_tools, list):
            for tool in raw_tools:
                if isinstance(tool, str):
                    normalized_tools.append(tool)
                else:
                    tool_name = type(tool).__name__.lower()
                    if "pubmed" in tool_name:
                        normalized_tools.append("pubmed")
                    elif "wikipedia" in tool_name:
                        normalized_tools.append("wikipedia")
                    elif "mermaid" in tool_name:
                        normalized_tools.append("mermaid")
        if tools_key in st.session_state:
            stored_tools = st.session_state.get(tools_key)
            if isinstance(stored_tools, list) and any(
                not isinstance(tool, str) for tool in stored_tools
            ):
                st.session_state[tools_key] = normalized_tools
        selected_tools = st.sidebar.multiselect(
            "Tools",
            options=list(available_tools.keys()),
            default=normalized_tools,
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
            st.sidebar.text_input(
                "PubMed E-Mail",
                value=str(pubmed_settings.get("email", "")),
                key=pubmed_email_key,
            )
            st.sidebar.number_input(
                "PubMed Max Results",
                min_value=1,
                value=int(pubmed_settings.get("max_results") or 5),
                key=pubmed_max_key,
            )
            st.sidebar.checkbox(
                "PubMed Suche aktiv",
                value=bool(pubmed_settings.get("enable_search_pubmed", True)),
                key=pubmed_enable_key,
            )
            st.sidebar.checkbox(
                "PubMed Alle Quellen",
                value=bool(pubmed_settings.get("all", False)),
                key=pubmed_all_key,
            )
        st.sidebar.multiselect(
            "Team-Mitglieder",
            options=member_options,
            default=(
                selected_agent.get("members", [])
                if isinstance(selected_agent.get("members"), list)
                else []
            ),
            key=members_key,
        )
        if st.sidebar.button("Agent speichern", key="save_agent_config"):
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
            updated = {
                **selected_agent,
                "id": selected_agent_id,
                "enabled": st.session_state.get(enabled_key, True),
                "name": st.session_state.get(name_key, ""),
                "role": st.session_state.get(role_key, ""),
                "description": st.session_state.get(description_key, ""),
                "instructions": st.session_state.get(instructions_key, ""),
                "model": st.session_state.get(model_key, "openai:gpt-5.2"),
                "members": st.session_state.get(members_key, []),
                "tools": selected_tools,
                "tool_settings": updated_tool_settings,
            }
            agents_config.save_agent_config(selected_agent_id, updated)
            agent_configs[selected_agent_id] = updated
            st.session_state["agent_configs"] = agent_configs
            st.sidebar.success("Agent-Konfiguration gespeichert")
    else:
        st.sidebar.caption("Keine Agenten-Konfigurationen gefunden.")


def _toggle_source(source_id: str) -> None:
    current_value = st.session_state.get(f"src_{source_id}", True)
    for source in st.session_state["sources"]:
        if source.id == source_id:
            source.selected = current_value
            break
    _persist_sources()


def _add_source(name: str, type_label: str, meta: str, body: str | None = None) -> None:
    source = SourceItem(name=name, type_label=type_label, meta=meta)
    st.session_state["sources"].append(source)
    _persist_sources()
    ingestion.ingest_source_content(
        title=name,
        body=body or "",
        meta={"type": type_label, "meta": meta, "source_id": source.id},
    )


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
    source_names = _all_source_names()
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
        "Sources: [INSERT SOURCES]"
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


def _append_chat(
    role: Literal["user", "assistant"],
    content: str,
    trace: Dict[str, object] | None = None,
) -> None:
    payload = {"role": role, "content": content}
    if trace:
        payload["trace"] = trace
    st.session_state["chat_history"].append(payload)


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


def _extract_mermaid_blocks(content: str) -> tuple[str, List[str]]:
    blocks = re.findall(r"```mermaid\n(.*?)```", content, re.DOTALL)
    cleaned = re.sub(r"```mermaid\n(.*?)```", "", content, flags=re.DOTALL)
    return cleaned.strip(), [block.strip() for block in blocks]


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
        _render_mermaid_diagram(block)


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
            status_text = f"Quellen in der Bibliothek: {all_source_count}"
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
                    st.session_state["all_sources_summary_stale"] = False
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
                if message["role"] == "assistant":
                    trace = message.get("trace") if isinstance(message, dict) else None
                    if trace:
                        with st.expander("Thinking", expanded=False):
                            _render_thinking_trace(trace)
                _render_chat_markdown(message["content"])
                if message["role"] == "assistant":
                    if st.button("In Notiz speichern", key=f"save_note_{idx}"):
                        _save_note_from_message(message["content"])
    pending_prompt = st.session_state.pop("pending_chat_prompt", None)
    if pending_prompt:
        contexts = retrieval.query_similar(pending_prompt)
        try:
            response = pipelines.generate_chat_reply(
                pending_prompt,
                _selected_source_names(),
                st.session_state["notes"],
                contexts,
                _get_agent_config("chat"),
            )
        except TypeError:
            response = pipelines.generate_chat_reply(
                pending_prompt,
                _selected_source_names(),
                st.session_state["notes"],
                contexts,
            )
        trace = agents.get_last_trace()
        _append_chat("assistant", response, trace=trace)
        st.toast("Antwort generiert – siehe Chat")
        st.rerun()
    selected_count = len(_selected_source_names())
    user_submission = st.chat_input(
        f"Frage stellen oder Audio aufnehmen… ({selected_count} Quellen ausgewählt)",
        accept_audio=True,
    )
    if user_submission:
        user_prompt = (user_submission.text or "").strip()
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
        _append_chat("user", user_prompt)
        if st.session_state.get("config", {}).get("log_user_requests", True):
            _LOGGER.info("User request: %s", user_prompt)
        st.session_state["pending_chat_prompt"] = user_prompt
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
                    st.markdown(content)
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
