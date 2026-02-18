from __future__ import annotations

from services import menu_settings


def test_normalize_menu_settings_keeps_custom_item_order_and_kinds() -> None:
    raw = {
        "items": [
            {"kind": "link", "label": "Help", "icon": "help", "page": "pages/Help.py"},
            {"kind": "separator"},
            {"kind": "spacer", "spacer_px": 24},
            {"kind": "link", "label": "Home", "icon": "home", "page": "main.py"},
        ]
    }

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["items"] == [
        {"kind": "link", "label": "Help", "icon": "help", "page": "pages/Help.py"},
        {"kind": "separator"},
        {"kind": "spacer", "spacer_px": 24},
        {"kind": "link", "label": "Home", "icon": "home", "page": "main.py"},
        {"kind": "theme_toggle"},
    ]


def test_normalize_menu_settings_clamps_spacer_and_gap_values() -> None:
    raw = {
        "sidebar_item_gap_px": 99,
        "items": [{"kind": "spacer", "spacer_px": -50}],
    }

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["sidebar_item_gap_px"] == 32
    assert normalized["items"] == [
        {"kind": "spacer", "spacer_px": 4},
        {"kind": "theme_toggle"},
    ]


def test_normalize_menu_settings_accepts_separator_color() -> None:
    raw = {"sidebar_separator_color": "#123ABC"}

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["sidebar_separator_color"] == "#123ABC"


def test_normalize_menu_settings_accepts_theme_and_branding_fields() -> None:
    raw = {
        "theme_mode": "light",
        "theme_preset_light": "Black & White (Light)",
        "theme_preset_dark": "Black & White (Dark)",
        "theme_preset_name": "Black & White (Light)",
        "logo_src_light": "assets/logo_light.png",
        "logo_src_dark": "assets/logo_dark.png",
        "icon_src_light": "assets/icon_light.png",
        "icon_src_dark": "assets/icon_dark.png",
        "logo_height_px": 80,
        "logo_render_height_px": 48,
        "icon_render_height_px": 28,
        "sidebar_hover_text_color": "#101010",
        "sidebar_separator_color_light": "#AAAAAA",
        "sidebar_separator_color_dark": "#222222",
    }

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["theme_mode"] == "light"
    assert normalized["theme_preset_name"] == "Black & White (Light)"
    assert normalized["logo_src_light"] == "assets/logo_light.png"
    assert normalized["icon_src_dark"] == "assets/icon_dark.png"
    assert normalized["logo_height_px"] == 80
    assert normalized["logo_render_height_px"] == 48
    assert normalized["icon_render_height_px"] == 28
    assert normalized["sidebar_hover_text_color"] == "#101010"
    assert normalized["sidebar_separator_color_light"] == "#AAAAAA"
    assert normalized["sidebar_separator_color_dark"] == "#222222"
