from __future__ import annotations

import json
import uuid
from typing import Dict, List

import streamlit as st

from app.pages.config_sections import shared
from services import menu_settings, storage

# ---------------------------------------------------------------------------
# Module-level constants (widget state keys)
# ---------------------------------------------------------------------------

MENU_EDITOR_ITEMS_KEY = "menu_editor_items"
MENU_EDITOR_SIGNATURE_KEY = "menu_editor_signature"


# ---------------------------------------------------------------------------
# Menu editor helpers
# ---------------------------------------------------------------------------


def normalize_agent_tools(raw_tools: object) -> List[str]:
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


def normalize_menu_editor_items(items: object) -> List[Dict[str, object]]:
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
                item_kind if item_kind in {"link", "separator", "spacer"} else "link"
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
        editor_item["label"] = str(raw_item.get("label", "")).strip()
        editor_item["icon"] = str(raw_item.get("icon", "")).strip()
        editor_item["page"] = str(raw_item.get("page", "")).strip()
        access_level = str(raw_item.get("access") or "public").strip().lower()
        if access_level not in {"public", "logged_in", "admin"}:
            access_level = "public"
        editor_item["access"] = access_level
        normalized.append(editor_item)
    return normalized


def menu_items_signature(items: object) -> str:
    if not isinstance(items, list):
        return "[]"
    serializable = [item for item in items if isinstance(item, dict)]
    return json.dumps(serializable, sort_keys=True)


def strip_editor_metadata(items: object) -> List[Dict[str, object]]:
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


# ---------------------------------------------------------------------------
# Menu editor UI (shared between app_design and themes sections)
# ---------------------------------------------------------------------------


def render_menu_editor(
    container: st.delta_generator.DeltaGenerator,
    current_menu: Dict[str, object],
    page_options: List[str],
    page_labels: Dict[str, str],
) -> None:
    """Render the drag-and-reorder menu editor widget."""
    show_menu_editor = container.checkbox(
        "Navigation & Menu Editor anzeigen (Erweitert)",
        value=bool(st.session_state.get("cfg_show_menu_editor", False)),
        key="cfg_show_menu_editor",
    )
    if not show_menu_editor:
        container.caption(
            "Der erweiterte Menü-Editor ist ausgeblendet. Aktiviere ihn bei Bedarf für Reihenfolge, Spacer/Separator und Seitenzuordnung."
        )

    editor_items = st.session_state.get(MENU_EDITOR_ITEMS_KEY, [])
    pending_action_name: str | None = None
    pending_action_index = -1

    if show_menu_editor:
        menu_caption_cols = container.columns([4, 2])
        menu_caption_cols[0].caption(
            "Menüeinträge: mit ↑ / ↓ sortieren, Spacer / Separator einfügen"
        )
        menu_caption_cols[1].markdown(
            "[Google Material Icons](https://fonts.google.com/icons)",
            help="Icon-Namen für das Feld 'Icon (Material)'",
        )

        for index, item in enumerate(editor_items):
            if not isinstance(item, dict):
                continue
            row_id = str(item.get("_editor_id") or uuid.uuid4().hex)
            item["_editor_id"] = row_id
            item_box = container.container(border=True)

            kind_options = ["link", "spacer", "separator"]
            kind_labels = {
                "link": "Link",
                "spacer": "Spacer",
                "separator": "Separator",
            }
            current_kind = str(item.get("kind", "link")).strip().lower()
            if current_kind not in kind_options:
                current_kind = "link"

            _row_icon = str(item.get("icon") or "").strip()
            _row_label = str(item.get("label") or "").strip()
            _row_page = str(item.get("page") or "").strip()
            _row_access = str(item.get("access") or "public").strip()
            if current_kind == "link" and (_row_label or _row_page):
                _summary_parts = []
                if _row_icon:
                    _summary_parts.append(f"`{_row_icon}`")
                if _row_label:
                    _summary_parts.append(f"**{_row_label}**")
                if _row_page:
                    _summary_parts.append(f"→ `{_row_page}`")
                _access_badge = {
                    "public": ":material/public:",
                    "logged_in": ":material/lock:",
                    "admin": ":material/key:",
                }.get(_row_access, ":material/public:")
                _summary_parts.append(_access_badge)
                item_box.caption(" · ".join(_summary_parts))
            elif current_kind in {"spacer", "separator"}:
                item_box.caption(kind_labels.get(current_kind, current_kind))

            header_cols = item_box.columns([2.4, 5.4, 0.6, 0.6, 0.6, 0.6, 0.6])
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
                help="Nach oben verschieben",
            ):
                pending_action_name = "up"
                pending_action_index = index
            if header_cols[3].button(
                "↓",
                key=f"menu_item_down_{row_id}",
                disabled=index >= len(editor_items) - 1,
                help="Nach unten verschieben",
            ):
                pending_action_name = "down"
                pending_action_index = index
            if header_cols[4].button(
                "⧉",
                key=f"menu_item_dup_{row_id}",
                help="Eintrag duplizieren",
            ):
                pending_action_name = "duplicate"
                pending_action_index = index
            if header_cols[5].button(
                "✕",
                key=f"menu_item_delete_{row_id}",
                help="Eintrag löschen",
            ):
                pending_action_name = "delete"
                pending_action_index = index

            if selected_kind == "link":
                link_cols = item_box.columns([2.0, 1.4, 2.9, 1.7])
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
                access_value = str(item.get("access") or "public").strip().lower()
                if access_value not in {"public", "logged_in", "admin"}:
                    access_value = "public"
                item["access"] = link_cols[3].selectbox(
                    "Access",
                    options=["public", "logged_in", "admin"],
                    index=["public", "logged_in", "admin"].index(access_value),
                    key=f"menu_item_access_{row_id}",
                )
            elif selected_kind == "spacer":
                item["spacer_px"] = item_box.slider(
                    "Spacer Höhe (px)",
                    min_value=4,
                    max_value=64,
                    value=int(item.get("spacer_px", 16)),
                    key=f"menu_item_spacer_{row_id}",
                )

        add_cols = container.columns(3)
        if add_cols[0].button("+ Link", key="menu_item_add_link"):
            pending_action_name = "add_link"
        if add_cols[1].button("+ Spacer", key="menu_item_add_spacer"):
            pending_action_name = "add_spacer"
        if add_cols[2].button("+ Separator", key="menu_item_add_separator"):
            pending_action_name = "add_separator"

    if show_menu_editor and pending_action_name:
        next_items = normalize_menu_editor_items(editor_items)
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
        elif pending_action_name == "duplicate" and 0 <= pending_action_index < len(
            next_items
        ):
            original = dict(next_items[pending_action_index])
            original["_editor_id"] = uuid.uuid4().hex
            next_items.insert(pending_action_index + 1, original)
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
                    "access": "public",
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

        st.session_state[MENU_EDITOR_ITEMS_KEY] = next_items
        st.rerun()


def _collect_save_items(
    editor_items: List[Dict[str, object]],
    page_options: List[str],
) -> List[Dict[str, object]]:
    """Read widget state and build cleaned list of menu items."""
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
        access_value = (
            str(
                st.session_state.get(
                    f"menu_item_access_{row_id}",
                    item.get("access", "public"),
                )
            )
            .strip()
            .lower()
        )
        if access_value not in {"public", "logged_in", "admin"}:
            access_value = "public"
        if not label or not page:
            continue
        updated_items.append(
            {
                "kind": "link",
                "label": label,
                "icon": icon,
                "page": page,
                "access": access_value,
            }
        )
    return updated_items


# ---------------------------------------------------------------------------
# Public render entry point
# ---------------------------------------------------------------------------


def render(
    container: st.delta_generator.DeltaGenerator | None = None,
) -> None:
    """Render App design / sidebar menu configuration."""
    if container is None:
        container = st.sidebar

    container.subheader("Sidebar Menu")
    shared.render_config_saved_caption(container, "app_menu")
    shared.render_config_saved_caption(container, "app_auth")
    current_menu = menu_settings.get_menu_settings(st.session_state["config"])
    container.caption("Menüstruktur und Reihenfolge konfigurieren.")

    menu_items = current_menu.get("items", [])
    menu_items_sig = menu_items_signature(menu_items)
    editor_sig = st.session_state.get(MENU_EDITOR_SIGNATURE_KEY)
    editor_items = st.session_state.get(MENU_EDITOR_ITEMS_KEY)
    if editor_sig != menu_items_sig or not isinstance(editor_items, list):
        st.session_state[MENU_EDITOR_ITEMS_KEY] = normalize_menu_editor_items(
            menu_items
        )
        st.session_state[MENU_EDITOR_SIGNATURE_KEY] = menu_items_sig
    editor_items = st.session_state.get(MENU_EDITOR_ITEMS_KEY, [])

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

    render_menu_editor(container, current_menu, page_options, page_labels)

    editor_items = st.session_state.get(MENU_EDITOR_ITEMS_KEY, [])
    app_menu_payload = {
        "items": strip_editor_metadata(editor_items),
    }
    shared.render_config_dirty_hint(
        container,
        "app_menu",
        app_menu_payload,
        "Ungespeicherte Menü-Änderungen.",
    )

    if container.button("Sidebar Menu speichern", key="save_sidebar_menu"):
        updated_items = _collect_save_items(editor_items, page_options)
        updated_menu = menu_settings.save_menu_settings(
            st.session_state["config"],
            {
                "items": updated_items,
                "sidebar_transition": str(
                    current_menu.get("sidebar_transition", "0.3s")
                ),
            },
        )
        storage.save_config(st.session_state["config"])
        st.session_state[MENU_EDITOR_ITEMS_KEY] = normalize_menu_editor_items(
            updated_menu.get("items", [])
        )
        st.session_state[MENU_EDITOR_SIGNATURE_KEY] = menu_items_signature(
            strip_editor_metadata(st.session_state[MENU_EDITOR_ITEMS_KEY])
        )
        shared.mark_config_saved(
            container,
            "app_menu",
            "Sidebar Menu gespeichert",
            payload=app_menu_payload,
        )

    if container.button("Sidebar Menu zurücksetzen", key="reset_sidebar_menu"):
        reset_menu = menu_settings.save_menu_settings(
            st.session_state["config"], menu_settings.DEFAULT_MENU_SETTINGS
        )
        storage.save_config(st.session_state["config"])
        st.session_state[MENU_EDITOR_ITEMS_KEY] = normalize_menu_editor_items(
            reset_menu.get("items", [])
        )
        st.session_state[MENU_EDITOR_SIGNATURE_KEY] = menu_items_signature(
            strip_editor_metadata(st.session_state[MENU_EDITOR_ITEMS_KEY])
        )
        shared.mark_config_saved(
            container,
            "app_menu",
            "Sidebar Menu auf Standard zurückgesetzt",
            payload=menu_settings.DEFAULT_MENU_SETTINGS,
        )
        st.rerun()
