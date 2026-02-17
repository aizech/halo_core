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
    ]


def test_normalize_menu_settings_clamps_spacer_and_gap_values() -> None:
    raw = {
        "sidebar_item_gap_px": 99,
        "items": [{"kind": "spacer", "spacer_px": -50}],
    }

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["sidebar_item_gap_px"] == 32
    assert normalized["items"] == [{"kind": "spacer", "spacer_px": 4}]


def test_normalize_menu_settings_accepts_separator_color() -> None:
    raw = {"sidebar_separator_color": "#123ABC"}

    normalized = menu_settings.normalize_menu_settings(raw)

    assert normalized["sidebar_separator_color"] == "#123ABC"
