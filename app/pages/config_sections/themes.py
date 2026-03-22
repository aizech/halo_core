from __future__ import annotations

from typing import Dict, List

import streamlit as st

from app.pages.config_sections import app_design, shared
from services import menu_settings, storage, theme_presets


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render theme configuration (migrated from main._render_theme_configuration)."""
    shared.render_config_saved_caption(container, "themes")
    shared.render_config_saved_caption(container, "app_menu")

    current_menu = menu_settings.get_menu_settings(st.session_state["config"])
    container.caption("Configure visual appearance, colors, and branding.")

    # Theme Preset Section
    theme_box = container.container(border=True)
    theme_box.markdown("**Theme Preset**")

    preset_names = sorted(theme_presets.THEME_PRESETS.keys())
    theme_default = str(current_menu.get("theme_preset_name") or "").strip()
    if theme_default not in preset_names and preset_names:
        theme_default = preset_names[0]
    theme_preset = theme_box.selectbox(
        "Theme Preset",
        options=preset_names,
        index=preset_names.index(theme_default) if preset_names else None,
        key="menu_theme_preset",
    )

    # Get current values
    sidebar_bg = str(current_menu.get("sidebar_bg", "#343A40"))
    sidebar_text = str(current_menu.get("sidebar_text_color", "#F8F9FA"))
    sidebar_icon = str(current_menu.get("sidebar_icon_color", "#F8F9FA"))
    sidebar_hover = str(current_menu.get("sidebar_hover_bg", "#F22222"))
    sidebar_hover_text = str(
        current_menu.get(
            "sidebar_hover_text_color",
            current_menu.get("sidebar_text_color", "#F8F9FA"),
        )
    )
    sidebar_active = str(current_menu.get("sidebar_active_bg", "#CC1E1E"))
    sidebar_focus = str(current_menu.get("sidebar_focus_outline", "#F22222"))
    sidebar_separator = str(current_menu.get("sidebar_separator_color", "#6C757D"))
    sidebar_font_size = int(current_menu.get("sidebar_font_size_px", 16))
    sidebar_icon_size = int(current_menu.get("sidebar_icon_size_px", 28))
    sidebar_item_gap = int(current_menu.get("sidebar_item_gap_px", 8))
    sidebar_collapsed_width = int(current_menu.get("sidebar_collapsed_width_px", 64))
    sidebar_hover_width = int(current_menu.get("sidebar_hover_width_px", 240))
    logo_src = str(current_menu.get("logo_src", ""))
    icon_src = str(current_menu.get("icon_src", ""))
    logo_height_px = int(current_menu.get("logo_height_px", 44))
    logo_render_height_px = int(current_menu.get("logo_render_height_px", 36))
    icon_render_height_px = int(current_menu.get("icon_render_height_px", 28))

    show_advanced_design = container.checkbox(
        "Erweiterte Design-Optionen anzeigen",
        value=bool(st.session_state.get("cfg_show_advanced_design", False)),
        key="cfg_show_advanced_design",
    )
    if not show_advanced_design:
        container.caption(
            "Farben, Größen und Branding sind ausgeblendet. Aktiviere die erweiterten Optionen, um sie anzupassen."
        )
    else:
        # Color Configuration
        color_box = container.container(border=True)
        color_box.markdown("**Farben**")
        color_left, color_right = color_box.columns(2)
        with color_left:
            sidebar_bg = st.color_picker(
                "Sidebar Hintergrund",
                value=sidebar_bg,
                key="menu_sidebar_bg",
            )
            sidebar_text = st.color_picker(
                "Sidebar Textfarbe",
                value=sidebar_text,
                key="menu_sidebar_text",
            )
            sidebar_hover = st.color_picker(
                "Hover Farbe",
                value=sidebar_hover,
                key="menu_sidebar_hover",
            )
            sidebar_hover_text = st.color_picker(
                "Hover Textfarbe",
                value=sidebar_hover_text,
                key="menu_sidebar_hover_text",
            )
            sidebar_separator = st.color_picker(
                "Separator Farbe",
                value=sidebar_separator,
                key="menu_sidebar_separator",
            )
        with color_right:
            sidebar_icon = st.color_picker(
                "Icon Farbe",
                value=sidebar_icon,
                key="menu_sidebar_icon",
            )
            sidebar_active = st.color_picker(
                "Aktive Farbe",
                value=sidebar_active,
                key="menu_sidebar_active",
            )
            sidebar_focus = st.color_picker(
                "Focus Outline",
                value=sidebar_focus,
                key="menu_sidebar_focus",
            )

        # Sizing and Layout
        sizing_box = container.container(border=True)
        sizing_box.markdown("**Größen & Layout**")
        sizing_left, sizing_right = sizing_box.columns(2)
        with sizing_left:
            sidebar_font_size = st.slider(
                "Schriftgröße (px)",
                min_value=12,
                max_value=24,
                value=sidebar_font_size,
                key="menu_sidebar_font_size",
            )
            sidebar_icon_size = st.slider(
                "Icon Größe (px)",
                min_value=16,
                max_value=34,
                value=sidebar_icon_size,
                key="menu_sidebar_icon_size",
            )
            sidebar_item_gap = st.slider(
                "Abstand zwischen Menüpunkten (px)",
                min_value=0,
                max_value=34,
                value=sidebar_item_gap,
                key="menu_sidebar_item_gap",
            )
        with sizing_right:
            sidebar_collapsed_width = st.slider(
                "Breite eingeklappt (px)",
                min_value=56,
                max_value=120,
                value=sidebar_collapsed_width,
                key="menu_sidebar_collapsed_width",
            )
            sidebar_hover_width = st.slider(
                "Breite bei Hover (px)",
                min_value=180,
                max_value=360,
                value=sidebar_hover_width,
                key="menu_sidebar_hover_width",
            )

        # Branding
        branding_box = container.container(border=True)
        branding_box.markdown("**Branding (Logo & Icon)**")
        branding_col_1, branding_col_2 = branding_box.columns(2)
        with branding_col_1:
            logo_src = st.text_input(
                "Logo Quelle",
                value=logo_src,
                key="menu_logo_src",
            )
            icon_src = st.text_input(
                "Icon Quelle",
                value=icon_src,
                key="menu_icon_src",
            )
        with branding_col_2:
            logo_height_px = branding_box.slider(
                "Logo Platzhöhe (px)",
                min_value=24,
                max_value=128,
                value=logo_height_px,
                key="menu_logo_height",
            )
            logo_render_height_px = branding_box.slider(
                "Logo Renderhöhe (px)",
                min_value=20,
                max_value=96,
                value=logo_render_height_px,
                key="menu_logo_render_height",
            )
            icon_render_height_px = branding_box.slider(
                "Icon Renderhöhe (px)",
                min_value=16,
                max_value=64,
                value=icon_render_height_px,
                key="menu_icon_render_height",
            )

    # Menu Configuration — delegate to app_design module
    menu_items = current_menu.get("items", [])
    menu_items_sig = app_design.menu_items_signature(menu_items)
    editor_sig = st.session_state.get(app_design.MENU_EDITOR_SIGNATURE_KEY)
    editor_items = st.session_state.get(app_design.MENU_EDITOR_ITEMS_KEY)
    if editor_sig != menu_items_sig or not isinstance(editor_items, list):
        st.session_state[app_design.MENU_EDITOR_ITEMS_KEY] = (
            app_design.normalize_menu_editor_items(menu_items)
        )
        st.session_state[app_design.MENU_EDITOR_SIGNATURE_KEY] = menu_items_sig
    editor_items = st.session_state.get(app_design.MENU_EDITOR_ITEMS_KEY, [])

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

    app_design.render_menu_editor(container, current_menu, page_options, page_labels)
    editor_items = st.session_state.get(app_design.MENU_EDITOR_ITEMS_KEY, [])

    app_menu_payload = {
        "sidebar_bg": sidebar_bg,
        "sidebar_text_color": sidebar_text,
        "sidebar_icon_color": sidebar_icon,
        "sidebar_hover_bg": sidebar_hover,
        "sidebar_hover_text_color": sidebar_hover_text,
        "sidebar_active_bg": sidebar_active,
        "sidebar_focus_outline": sidebar_focus,
        "sidebar_separator_color": sidebar_separator,
        "sidebar_font_size_px": sidebar_font_size,
        "sidebar_icon_size_px": sidebar_icon_size,
        "sidebar_collapsed_width_px": sidebar_collapsed_width,
        "sidebar_hover_width_px": sidebar_hover_width,
        "sidebar_item_gap_px": sidebar_item_gap,
        "theme_preset_name": theme_preset,
        "logo_src": logo_src,
        "icon_src": icon_src,
        "logo_height_px": logo_height_px,
        "logo_render_height_px": logo_render_height_px,
        "icon_render_height_px": icon_render_height_px,
        "items": app_design.strip_editor_metadata(editor_items),
    }

    shared.render_config_dirty_hint(
        container,
        "themes",
        app_menu_payload,
        "Ungespeicherte Theme-Änderungen.",
    )

    if container.button("Theme Einstellungen speichern", key="save_theme_settings"):
        if theme_preset:
            from app import main as _main

            _main._apply_theme_preset_to_config(
                st.session_state["config"], preset_name=theme_preset
            )

        menu_settings.save_menu_settings(
            st.session_state["config"],
            {
                **app_menu_payload,
                "sidebar_transition": str(
                    current_menu.get("sidebar_transition", "0.3s")
                ),
            },
        )
        storage.save_config(st.session_state["config"])

        st.session_state[app_design.MENU_EDITOR_ITEMS_KEY] = (
            app_design.normalize_menu_editor_items(app_menu_payload.get("items", []))
        )
        st.session_state[app_design.MENU_EDITOR_SIGNATURE_KEY] = (
            app_design.menu_items_signature(
                app_design.strip_editor_metadata(
                    st.session_state[app_design.MENU_EDITOR_ITEMS_KEY]
                )
            )
        )

        shared.mark_config_saved(
            container,
            "themes",
            "Theme Einstellungen gespeichert",
            payload=app_menu_payload,
        )
        st.rerun()
