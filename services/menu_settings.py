"""Sidebar menu settings helpers."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List

MENU_SETTINGS_KEY = "menu_settings"

_HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

_ALLOWED_ACCESS_LEVELS = {"public", "logged_in", "admin"}

DEFAULT_MENU_SETTINGS: Dict[str, Any] = {
    "sidebar_bg": "#313841",
    "sidebar_text_color": "#EEEEEE",
    "sidebar_icon_color": "#EEEEEE",
    "sidebar_hover_bg": "#3A4750",
    "sidebar_hover_text_color": "#EEEEEE",
    "sidebar_active_bg": "#EA9216",
    "sidebar_focus_outline": "#EA9216",
    "sidebar_separator_color": "#3A4750",
    "sidebar_separator_color_light": "#3A4750",
    "sidebar_separator_color_dark": "#3A4750",
    "theme_mode": "dark",
    "theme_preset_light": "HALO Core Palette",
    "theme_preset_dark": "HALO Core Palette",
    "theme_preset_name": "HALO Core Palette",
    "logo_src": "assets/logo_dark.png",
    "logo_src_light": "assets/logo_light.png",
    "logo_src_dark": "assets/logo_dark.png",
    "icon_src_light": "assets/icon_light.png",
    "icon_src_dark": "assets/icon_dark.png",
    "logo_height_px": 44,
    "logo_render_height_px": 36,
    "icon_render_height_px": 36,
    "sidebar_font_size_px": 14,
    "sidebar_icon_size_px": 20,
    "sidebar_collapsed_width_px": 68,
    "sidebar_hover_width_px": 260,
    "sidebar_item_gap_px": 4,
    "sidebar_transition": "0.2s",
    "input_bg": "#313841",
    "input_text_color": "#EEEEEE",
    "input_border_color": "#3A4750",
    "input_border_hover": "#EA9216",
    "input_hover_bg": "#3A4750",
    "input_focus_outline": "#EA9216",
    "items": [
        {
            "kind": "link",
            "label": "Home",
            "icon": "home",
            "page": "main.py",
        },
        {
            "kind": "link",
            "label": "Dashboard",
            "icon": "grid_view",
            "page": "pages/Dashboard.py",
        },
        {
            "kind": "link",
            "label": "DICOM Tools",
            "icon": "medical_services",
            "page": "pages/DICOM_Tools.py",
        },
        {
            "kind": "link",
            "label": "DICOM Analysis",
            "icon": "analytics",
            "page": "pages/DICOM_Analysis.py",
        },
        {
            "kind": "link",
            "label": "DICOM Analysis (Opt)",
            "icon": "bolt",
            "page": "pages/DICOM_Analysis_Optimized.py",
        },
        {
            "kind": "link",
            "label": "DICOM Benchmark",
            "icon": "speed",
            "page": "pages/DICOM_Benchmark.py",
        },
        {
            "kind": "link",
            "label": "Agent Config",
            "icon": "smart_toy",
            "page": "pages/Agent_Config.py",
        },
        {
            "kind": "link",
            "label": "Configuration",
            "icon": "settings",
            "page": "pages/Configuration.py",
        },
        {
            "kind": "link",
            "label": "Preferences",
            "icon": "settings_input_component",
            "page": "pages/Preferences.py",
        },
        {
            "kind": "link",
            "label": "Themes",
            "icon": "palette",
            "page": "pages/Themes.py",
        },
        {
            "kind": "link",
            "label": "Account",
            "icon": "account_circle",
            "page": "pages/Account.py",
        },
        {
            "kind": "link",
            "label": "Agent Cards",
            "icon": "style",
            "page": "pages/Agent_Cards.py",
        },
        {
            "kind": "link",
            "label": "Help",
            "icon": "help_outline",
            "page": "pages/Help.py",
        },
        {"kind": "user_profile"},
    ],
}


def _valid_hex(value: Any) -> bool:
    return isinstance(value, str) and bool(_HEX_COLOR_RE.match(value.strip()))


def _as_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, parsed))


def _normalize_item_kind(value: Any) -> str:
    item_kind = str(value or "link").strip().lower()
    if item_kind in {
        "link",
        "separator",
        "spacer",
        "theme_toggle",
        "search",
        "badge_link",
        "header",
        "upgrade_card",
        "user_profile",
    }:
        return item_kind
    return "link"


def _normalize_access_level(value: Any) -> str:
    access_level = str(value or "public").strip().lower()
    if access_level in _ALLOWED_ACCESS_LEVELS:
        return access_level
    return "public"


def _normalize_items(value: Any) -> List[Dict[str, Any]]:
    defaults = deepcopy(DEFAULT_MENU_SETTINGS["items"])
    if not isinstance(value, list):
        return defaults
    cleaned: List[Dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        item_kind = _normalize_item_kind(raw.get("kind"))
        if item_kind == "separator":
            cleaned.append({"kind": "separator"})
            continue
        if item_kind == "spacer":
            cleaned.append(
                {
                    "kind": "spacer",
                    "spacer_px": _as_int(
                        raw.get("spacer_px"),
                        default=16,
                        minimum=4,
                        maximum=250,
                    ),
                }
            )
            continue
        if item_kind == "theme_toggle":
            cleaned.append(
                {
                    "kind": "theme_toggle",
                    "label": str(raw.get("label") or "Dark mode").strip(),
                    "icon": str(raw.get("icon") or "dark_mode").strip(),
                }
            )
            continue
        if item_kind == "search":
            cleaned.append(
                {
                    "kind": "search",
                    "label": str(raw.get("label") or "Quick search").strip(),
                    "icon": str(raw.get("icon") or "search").strip(),
                }
            )
            continue
        if item_kind == "header":
            cleaned.append(
                {
                    "kind": "header",
                    "label": str(raw.get("label") or "").strip(),
                }
            )
            continue
        if item_kind == "upgrade_card":
            cleaned.append({"kind": "upgrade_card"})
            continue
        if item_kind == "user_profile":
            cleaned.append({"kind": "user_profile"})
            continue

        label = str(raw.get("label") or "").strip()
        icon = str(raw.get("icon") or "").strip()
        page = str(raw.get("page") or "").strip()
        if not label or not page:
            continue

        item = {
            "kind": item_kind,
            "label": label,
            "icon": icon,
            "page": page,
            "access": _normalize_access_level(raw.get("access")),
        }
        if item_kind == "badge_link":
            item["badge"] = str(raw.get("badge") or "").strip()

        cleaned.append(item)

    if not any(
        str(item.get("kind") or "").strip().lower() == "theme_toggle"
        for item in cleaned
    ):
        cleaned.append(
            {"kind": "theme_toggle", "label": "Dark mode", "icon": "dark_mode"}
        )

    return cleaned or defaults


def normalize_menu_settings(raw: Any) -> Dict[str, Any]:
    defaults = deepcopy(DEFAULT_MENU_SETTINGS)
    if not isinstance(raw, dict):
        return defaults

    preset_name = raw.get("theme_preset_name")
    if isinstance(preset_name, str):
        defaults["theme_preset_name"] = preset_name.strip()

    theme_mode = str(raw.get("theme_mode") or "").strip().lower()
    if theme_mode in {"light", "dark"}:
        defaults["theme_mode"] = theme_mode

    for key in (
        "theme_preset_light",
        "theme_preset_dark",
        "logo_src",
        "logo_src_light",
        "logo_src_dark",
        "icon_src_light",
        "icon_src_dark",
    ):
        value = raw.get(key)
        if isinstance(value, str):
            defaults[key] = value.strip()

    for key in (
        "sidebar_bg",
        "sidebar_text_color",
        "sidebar_icon_color",
        "sidebar_hover_bg",
        "sidebar_hover_text_color",
        "sidebar_active_bg",
        "sidebar_focus_outline",
        "sidebar_separator_color",
        "sidebar_separator_color_light",
        "sidebar_separator_color_dark",
        "input_bg",
        "input_text_color",
        "input_border_color",
        "input_border_hover",
        "input_hover_bg",
        "input_focus_outline",
    ):
        value = raw.get(key)
        if _valid_hex(value):
            defaults[key] = str(value).strip()

    if not defaults.get("sidebar_separator_color_light"):
        defaults["sidebar_separator_color_light"] = defaults["sidebar_separator_color"]
    if not defaults.get("sidebar_separator_color_dark"):
        defaults["sidebar_separator_color_dark"] = defaults["sidebar_separator_color"]

    defaults["sidebar_font_size_px"] = _as_int(
        raw.get("sidebar_font_size_px"),
        default=int(DEFAULT_MENU_SETTINGS["sidebar_font_size_px"]),
        minimum=12,
        maximum=24,
    )
    defaults["sidebar_icon_size_px"] = _as_int(
        raw.get("sidebar_icon_size_px"),
        default=int(DEFAULT_MENU_SETTINGS["sidebar_icon_size_px"]),
        minimum=16,
        maximum=32,
    )
    defaults["sidebar_collapsed_width_px"] = _as_int(
        raw.get("sidebar_collapsed_width_px"),
        default=int(DEFAULT_MENU_SETTINGS["sidebar_collapsed_width_px"]),
        minimum=56,
        maximum=120,
    )
    defaults["sidebar_hover_width_px"] = _as_int(
        raw.get("sidebar_hover_width_px"),
        default=int(DEFAULT_MENU_SETTINGS["sidebar_hover_width_px"]),
        minimum=180,
        maximum=360,
    )
    defaults["sidebar_item_gap_px"] = _as_int(
        raw.get("sidebar_item_gap_px"),
        default=int(DEFAULT_MENU_SETTINGS["sidebar_item_gap_px"]),
        minimum=0,
        maximum=32,
    )
    defaults["logo_height_px"] = _as_int(
        raw.get("logo_height_px"),
        default=int(DEFAULT_MENU_SETTINGS["logo_height_px"]),
        minimum=24,
        maximum=128,
    )
    defaults["logo_render_height_px"] = _as_int(
        raw.get("logo_render_height_px"),
        default=int(DEFAULT_MENU_SETTINGS["logo_render_height_px"]),
        minimum=20,
        maximum=96,
    )
    defaults["icon_render_height_px"] = _as_int(
        raw.get("icon_render_height_px"),
        default=int(DEFAULT_MENU_SETTINGS["icon_render_height_px"]),
        minimum=16,
        maximum=64,
    )

    transition = str(raw.get("sidebar_transition") or "").strip()
    if transition:
        defaults["sidebar_transition"] = transition

    defaults["items"] = _normalize_items(raw.get("items"))
    return defaults


def get_menu_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    return normalize_menu_settings(config.get(MENU_SETTINGS_KEY))


def save_menu_settings(config: Dict[str, Any], raw: Dict[str, Any]) -> Dict[str, Any]:
    normalized = normalize_menu_settings(raw)
    config[MENU_SETTINGS_KEY] = normalized
    return normalized
