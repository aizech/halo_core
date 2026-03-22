from __future__ import annotations

import json
from typing import Dict, List

import streamlit as st

from app.pages.config_sections import shared
from services import agents_config


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


def render(container: st.delta_generator.DeltaGenerator) -> None:
    """Render advanced per-agent configuration (migrated from main._render_advanced_configuration)."""
    shared.render_config_saved_caption(container, "advanced")
    container.info(
        "Primary place for per-agent configuration. Änderungen hier betreffen den jeweils ausgewählten Agenten direkt (inkl. Tools, MCP und Runtime)."
    )
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
    youtube_transcript_captions_key = (
        f"agent_cfg_youtube_transcript_captions_{key_suffix}"
    )
    youtube_transcript_video_info_key = (
        f"agent_cfg_youtube_transcript_video_info_{key_suffix}"
    )
    youtube_transcript_timestamps_key = (
        f"agent_cfg_youtube_transcript_timestamps_{key_suffix}"
    )
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
    mcp_calls_key = f"agent_cfg_mcp_calls_{key_suffix}"
    mcp_servers_key = f"agent_cfg_mcp_servers_{key_suffix}"
    hackernews_top_key = f"agent_cfg_hackernews_top_{key_suffix}"
    hackernews_user_key = f"agent_cfg_hackernews_user_{key_suffix}"
    hackernews_all_key = f"agent_cfg_hackernews_all_{key_suffix}"
    yfinance_price_key = f"agent_cfg_yfinance_price_{key_suffix}"
    yfinance_analyst_key = f"agent_cfg_yfinance_analyst_{key_suffix}"
    member_options = [
        agent_id for agent_id in agent_ids if agent_id != selected_agent_id
    ]

    adv_expert_mode = container.checkbox(
        "Expertenmodus anzeigen",
        value=bool(st.session_state.get("cfg_adv_expert_mode", False)),
        key="cfg_adv_expert_mode",
        help="Zeigt alle Felder inkl. Beschreibung, MCP-Server und Tool-Details.",
    )

    id_box = container.container(border=True)
    id_box.markdown("**Identität & Instruktionen**")
    id_box.checkbox(
        "Aktiviert",
        value=bool(selected_agent.get("enabled", True)),
        key=enabled_key,
    )
    id_box.text_input(
        "Name",
        value=str(selected_agent.get("name", "")),
        key=name_key,
    )
    id_box.text_input(
        "Rolle",
        value=str(selected_agent.get("role", "")),
        key=role_key,
    )
    if adv_expert_mode:
        id_box.text_area(
            "Beschreibung",
            value=str(selected_agent.get("description", "")),
            key=description_key,
            height=100,
        )
    else:
        id_box.caption(
            f"Beschreibung: {str(selected_agent.get('description', '—'))[:120] or '—'}"
        )
    id_box.text_area(
        "Anweisungen",
        value=str(selected_agent.get("instructions", "")),
        key=instructions_key,
        height=160,
    )

    rt_box = container.container(border=True)
    rt_box.markdown("**Runtime**")
    rt_box.text_input(
        "Model",
        value=str(selected_agent.get("model", "openai:gpt-5.2")),
        key=model_key,
        help="Format: provider:model (z.B. openai:gpt-5.2)",
    )
    _adv_model_val = str(st.session_state.get(model_key, "")).strip()
    if _adv_model_val and ":" not in _adv_model_val:
        rt_box.warning(
            f"⚠️ Ungültiges Modell-Format: `{_adv_model_val}`. "
            "Erwartet: `provider:model` (z.B. `openai:gpt-5.2`)."
        )

    from services.tool_registry import get_all_tool_metadata

    tool_metadata = get_all_tool_metadata()
    available_tools = {
        tool_id: meta.display_name for tool_id, meta in tool_metadata.items()
    }
    normalized_tools = _normalize_agent_tools(selected_agent.get("tools", []))
    if tools_key in st.session_state:
        stored_tools = st.session_state.get(tools_key)
        if isinstance(stored_tools, list) and any(
            not isinstance(tool, str) for tool in stored_tools
        ):
            st.session_state[tools_key] = normalized_tools
    tools_box = container.container(border=True)
    tools_box.markdown("**Tools**")
    selected_tools = tools_box.multiselect(
        "Aktive Tools",
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
    if not adv_expert_mode and selected_tools:
        tools_box.caption(
            "Tool-Details (E-Mail, Max Results, Timeouts) sind im Expertenmodus verfügbar."
        )
    if adv_expert_mode and "pubmed" in selected_tools:
        pubmed_settings = tool_settings.get("pubmed", {})
        tools_box.text_input(
            "PubMed E-Mail",
            value=str(pubmed_settings.get("email", "")),
            key=pubmed_email_key,
        )
        tools_box.number_input(
            "PubMed Max Results",
            min_value=1,
            value=int(pubmed_settings.get("max_results") or 5),
            key=pubmed_max_key,
        )
        tools_box.checkbox(
            "PubMed Suche aktiv",
            value=bool(pubmed_settings.get("enable_search_pubmed", True)),
            key=pubmed_enable_key,
        )
        tools_box.checkbox(
            "PubMed Alle Quellen",
            value=bool(pubmed_settings.get("all", False)),
            key=pubmed_all_key,
        )
    if adv_expert_mode and "websearch" in selected_tools:
        websearch_settings = tool_settings.get("websearch", {})
        tools_box.selectbox(
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
        tools_box.number_input(
            "WebSearch Max Results",
            min_value=1,
            value=int(websearch_settings.get("num_results") or 5),
            key=websearch_results_key,
        )
    if adv_expert_mode and "youtube" in selected_tools:
        youtube_settings = tool_settings.get("youtube", {})
        tools_box.checkbox(
            "YouTube Captions aktiv",
            value=bool(youtube_settings.get("fetch_captions", True)),
            key=youtube_captions_key,
        )
        tools_box.checkbox(
            "YouTube Video-Infos aktiv",
            value=bool(youtube_settings.get("fetch_video_info", True)),
            key=youtube_video_info_key,
        )
        tools_box.checkbox(
            "YouTube Timestamps aktiv",
            value=bool(youtube_settings.get("fetch_timestamps", False)),
            key=youtube_timestamps_key,
        )
    if adv_expert_mode and "youtube_transcript" in selected_tools:
        youtube_transcript_settings = tool_settings.get("youtube_transcript", {})
        tools_box.checkbox(
            "YouTube Transkript: Captions aktiv",
            value=bool(youtube_transcript_settings.get("fetch_captions", True)),
            key=youtube_transcript_captions_key,
        )
        tools_box.checkbox(
            "YouTube Transkript: Video-Infos aktiv",
            value=bool(youtube_transcript_settings.get("fetch_video_info", False)),
            key=youtube_transcript_video_info_key,
        )
        tools_box.checkbox(
            "YouTube Transkript: Timestamps aktiv",
            value=bool(youtube_transcript_settings.get("fetch_timestamps", True)),
            key=youtube_transcript_timestamps_key,
        )
    if adv_expert_mode and "duckduckgo" in selected_tools:
        duckduckgo_settings = tool_settings.get("duckduckgo", {})
        tools_box.checkbox(
            "DuckDuckGo Suche aktiv",
            value=bool(duckduckgo_settings.get("enable_search", True)),
            key=duckduckgo_search_key,
        )
        tools_box.checkbox(
            "DuckDuckGo News aktiv",
            value=bool(duckduckgo_settings.get("enable_news", True)),
            key=duckduckgo_news_key,
        )
        tools_box.number_input(
            "DuckDuckGo Max Results",
            min_value=1,
            value=int(duckduckgo_settings.get("fixed_max_results") or 5),
            key=duckduckgo_results_key,
        )
        tools_box.number_input(
            "DuckDuckGo Timeout (Sek)",
            min_value=1,
            value=int(duckduckgo_settings.get("timeout") or 10),
            key=duckduckgo_timeout_key,
        )
        tools_box.checkbox(
            "DuckDuckGo SSL verifizieren",
            value=bool(duckduckgo_settings.get("verify_ssl", True)),
            key=duckduckgo_ssl_key,
        )
    if adv_expert_mode and "arxiv" in selected_tools:
        arxiv_settings = (
            tool_settings.get("arxiv", {})
            if isinstance(tool_settings.get("arxiv"), dict)
            else {}
        )
        arxiv_sort_options = ["", "submittedDate", "lastUpdatedDate", "relevance"]
        arxiv_sort_default = str(arxiv_settings.get("sort_by", ""))
        if arxiv_sort_default not in arxiv_sort_options:
            arxiv_sort_default = ""
        tools_box.number_input(
            "arXiv Max Results",
            min_value=1,
            max_value=50,
            value=int(arxiv_settings.get("max_results") or 5),
            key=arxiv_max_results_key,
        )
        tools_box.selectbox(
            "arXiv Sortierung",
            options=arxiv_sort_options,
            index=arxiv_sort_options.index(arxiv_sort_default),
            key=arxiv_sort_by_key,
        )
    if adv_expert_mode and "website" in selected_tools:
        website_settings = (
            tool_settings.get("website", {})
            if isinstance(tool_settings.get("website"), dict)
            else {}
        )
        tools_box.number_input(
            "Website Max Pages",
            min_value=1,
            max_value=20,
            value=max(1, min(20, int(website_settings.get("max_pages") or 5))),
            key=website_max_pages_key,
        )
        tools_box.number_input(
            "Website Timeout (Sek)",
            min_value=1,
            max_value=120,
            value=max(1, min(120, int(website_settings.get("timeout") or 10))),
            key=website_timeout_key,
        )
        tools_box.text_area(
            "Website erlaubte Domains (eine pro Zeile)",
            value="\n".join(
                str(domain).strip()
                for domain in website_settings.get("allowed_domains", [])
                if str(domain).strip()
            ),
            key=website_domains_key,
        )
    if adv_expert_mode and "hackernews" in selected_tools:
        hackernews_settings = tool_settings.get("hackernews", {})
        tools_box.checkbox(
            "HackerNews Top Stories aktiv",
            value=bool(hackernews_settings.get("enable_get_top_stories", True)),
            key=hackernews_top_key,
        )
        tools_box.checkbox(
            "HackerNews User-Details aktiv",
            value=bool(hackernews_settings.get("enable_get_user_details", True)),
            key=hackernews_user_key,
        )
        tools_box.checkbox(
            "HackerNews Alle Funktionen",
            value=bool(hackernews_settings.get("all", False)),
            key=hackernews_all_key,
        )
    if adv_expert_mode and "yfinance" in selected_tools:
        yfinance_settings = tool_settings.get("yfinance", {})
        tools_box.checkbox(
            "YFinance Aktienkurs aktiv",
            value=bool(yfinance_settings.get("stock_price", True)),
            key=yfinance_price_key,
        )
        tools_box.checkbox(
            "YFinance Analystenempfehlungen aktiv",
            value=bool(yfinance_settings.get("analyst_recommendations", True)),
            key=yfinance_analyst_key,
        )

    team_box = container.container(border=True)
    team_box.markdown("**Team-Mitglieder**")
    team_box.multiselect(
        "Mitglieder (Delegation)",
        options=member_options,
        default=[
            m
            for m in (
                selected_agent.get("members", [])
                if isinstance(selected_agent.get("members"), list)
                else []
            )
            if m in member_options
        ],
        key=members_key,
    )

    mcp_box = container.container(border=True)
    mcp_box.markdown("**MCP Konfiguration**")
    if not adv_expert_mode:
        mcp_box.caption(
            "MCP-Server JSON und MCP-Calls sind im Expertenmodus verfügbar."
        )
    else:
        mcp_box.text_area(
            "MCP calls (eine pro Zeile)",
            value="\n".join(
                str(call).strip()
                for call in selected_agent.get("mcp_calls", [])
                if str(call).strip()
            ),
            key=mcp_calls_key,
            height=120,
        )
    if mcp_servers_key not in st.session_state:
        st.session_state[mcp_servers_key] = json.dumps(
            selected_agent.get("mcp_servers", []), indent=2
        )
    if adv_expert_mode:
        if mcp_box.button("➕ Add Agno Docs MCP", key=f"{mcp_servers_key}_add_agno"):
            try:
                mcp_servers_payload = json.loads(
                    str(st.session_state.get(mcp_servers_key, "[]")) or "[]"
                )
            except json.JSONDecodeError:
                mcp_servers_payload = []
            if not isinstance(mcp_servers_payload, list):
                mcp_servers_payload = []
            if not any(
                isinstance(item, dict)
                and str(item.get("name", "")).strip() == "agno-docs"
                for item in mcp_servers_payload
            ):
                mcp_servers_payload.append(
                    {
                        "name": "agno-docs",
                        "enabled": False,
                        "transport": "streamable-http",
                        "url": "https://docs.agno.com/mcp",
                        "allowed_tools": [],
                    }
                )
                st.session_state[mcp_servers_key] = json.dumps(
                    mcp_servers_payload, indent=2
                )
        mcp_box.text_area(
            "MCP servers (JSON)",
            key=mcp_servers_key,
            height=160,
        )
        _mcp_raw = str(st.session_state.get(mcp_servers_key, "[]") or "[]").strip()
        try:
            _mcp_parsed = json.loads(_mcp_raw)
            if not isinstance(_mcp_parsed, list):
                mcp_box.warning("⚠️ MCP servers muss ein JSON-Array `[...]` sein.")
            elif _mcp_parsed:
                _enabled_count = sum(
                    1
                    for s in _mcp_parsed
                    if isinstance(s, dict) and s.get("enabled", False)
                )
                mcp_box.caption(
                    f"✅ Gültiges JSON · {len(_mcp_parsed)} Server"
                    f"{f' · {_enabled_count} aktiv' if _enabled_count else ' · keiner aktiv'}"
                )
        except json.JSONDecodeError as _mcp_exc:
            mcp_box.error(f"❌ JSON-Fehler: {_mcp_exc}")

    advanced_payload = {
        "agent_id": selected_agent_id,
        "enabled": bool(
            st.session_state.get(enabled_key, selected_agent.get("enabled", True))
        ),
        "name": str(
            st.session_state.get(name_key, selected_agent.get("name", ""))
        ).strip(),
        "role": str(
            st.session_state.get(role_key, selected_agent.get("role", ""))
        ).strip(),
        "description": str(
            st.session_state.get(description_key, selected_agent.get("description", ""))
        ).strip(),
        "instructions": str(
            st.session_state.get(
                instructions_key, selected_agent.get("instructions", "")
            )
        ).strip(),
        "model": str(
            st.session_state.get(model_key, selected_agent.get("model", ""))
        ).strip(),
        "tools": st.session_state.get(tools_key, selected_agent.get("tools", [])),
        "members": st.session_state.get(members_key, selected_agent.get("members", [])),
        "mcp_calls": str(st.session_state.get(mcp_calls_key, "")),
        "mcp_servers": str(st.session_state.get(mcp_servers_key, "")),
    }
    shared.render_config_dirty_hint(
        container,
        "advanced",
        advanced_payload,
        "Ungespeicherte Agent-Änderungen.",
    )
    if container.button(
        "Agent-Konfiguration speichern",
        key="cfg_advanced_save_agent_config",
    ):
        try:
            parsed_mcp_servers = json.loads(
                str(st.session_state.get(mcp_servers_key, "[]")) or "[]"
            )
        except json.JSONDecodeError as exc:
            container.error(f"MCP servers JSON ist ungültig: {exc}")
            return
        if not isinstance(parsed_mcp_servers, list):
            container.error("MCP servers muss ein JSON-Array sein.")
            return

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
        if "youtube_transcript" in selected_tools:
            updated_tool_settings["youtube_transcript"] = {
                "fetch_captions": bool(
                    st.session_state.get(youtube_transcript_captions_key, True)
                ),
                "fetch_video_info": bool(
                    st.session_state.get(youtube_transcript_video_info_key, False)
                ),
                "fetch_timestamps": bool(
                    st.session_state.get(youtube_transcript_timestamps_key, True)
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
            "mcp_calls": [
                line.strip()
                for line in str(st.session_state.get(mcp_calls_key, "")).splitlines()
                if line.strip()
            ],
            "mcp_servers": parsed_mcp_servers,
        }
        agents_config.save_agent_config(selected_agent_id, updated)
        agent_configs[selected_agent_id] = updated
        st.session_state["agent_configs"] = agent_configs
        shared.mark_config_saved(
            container,
            "advanced",
            "Agent-Konfiguration gespeichert",
            payload=advanced_payload,
        )
