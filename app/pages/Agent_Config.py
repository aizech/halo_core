from __future__ import annotations

import json
from typing import Dict, List

import streamlit as st

from app import main
from services import agents_config


def _load_configs() -> Dict[str, Dict[str, object]]:
    return agents_config.load_agent_configs()


def _save_config(agent_id: str, config: Dict[str, object]) -> None:
    agents_config.save_agent_config(agent_id, config)


def _as_text_lines(value: object) -> str:
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def _parse_lines(raw: str) -> List[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def render_agent_config_page() -> None:
    main._init_state()
    main.render_sidebar()
    st.title("Agent Config")
    st.caption("Manage per-agent configuration files.")

    try:
        configs = _load_configs()
    except ValueError as exc:
        st.error(f"Agent config validation failed: {exc}")
        return
    except Exception as exc:
        st.error(f"Failed to load agent configs: {exc}")
        return
    agent_ids = sorted(configs.keys())
    if not agent_ids:
        st.info("No agents found.")
        return

    selected_id = st.selectbox("Select agent", options=agent_ids)
    current = dict(configs[selected_id])

    st.text_input("ID", value=str(current.get("id", "")), disabled=True)
    name = st.text_input("Name", value=str(current.get("name", "")))
    role = st.text_input("Role", value=str(current.get("role", "")))
    description = st.text_area(
        "Description", value=str(current.get("description", "")), height=80
    )
    enabled = st.checkbox("Enabled", value=bool(current.get("enabled", True)))
    instructions = st.text_area(
        "Instructions", value=str(current.get("instructions", "")), height=160
    )
    st.subheader("Capabilities")
    skills_raw = st.text_area(
        "Skills (one per line)", value=_as_text_lines(current.get("skills"))
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
    configured_tools = [
        str(tool)
        for tool in current.get("tools", [])
        if isinstance(current.get("tools"), list)
        for tool in [tool]
        if isinstance(tool, str)
    ]
    selected_tools = st.multiselect(
        "Tools",
        options=list(available_tools.keys()),
        default=[tool for tool in configured_tools if tool in available_tools],
        format_func=lambda tool_id: available_tools.get(tool_id, tool_id),
    )
    extra_tools_raw = st.text_area(
        "Additional tools (one per line)",
        value="\n".join(
            tool for tool in configured_tools if tool not in available_tools
        ),
        help="Optional: define custom tool ids directly.",
    )
    mcp_raw = st.text_area(
        "MCP calls (one per line)", value=_as_text_lines(current.get("mcp_calls"))
    )

    # MCP Servers UI with enable/disable toggles
    st.subheader("MCP Servers")
    st.caption("Model Context Protocol servers for extended tool capabilities.")

    mcp_servers = list(current.get("mcp_servers", []))
    if not isinstance(mcp_servers, list):
        mcp_servers = []

    # Initialize session state for MCP servers if not present
    mcp_key = f"mcp_servers_{selected_id}"
    if mcp_key not in st.session_state:
        st.session_state[mcp_key] = mcp_servers.copy()

    # Sync with current config if changed
    if st.session_state[mcp_key] != mcp_servers:
        st.session_state[mcp_key] = mcp_servers.copy()

    servers_to_edit = st.session_state[mcp_key]

    # Render each server
    servers_to_remove = []
    transport_options = ["streamable-http", "sse", "stdio"]
    for idx, server in enumerate(servers_to_edit):
        if not isinstance(server, dict):
            continue

        with st.container():
            col_name, col_enabled, col_remove = st.columns([3, 1, 1])

            server_name = str(server.get("name", f"server-{idx}"))
            with col_name:
                st.text_input(
                    "Name",
                    value=server_name,
                    key=f"mcp_name_{idx}_{selected_id}",
                    disabled=True,
                )

            with col_enabled:
                enabled = st.checkbox(
                    "Enabled",
                    value=bool(server.get("enabled", False)),
                    key=f"mcp_enabled_{idx}_{selected_id}",
                )
                servers_to_edit[idx]["enabled"] = enabled

            with col_remove:
                if st.button(
                    "🗑️", key=f"mcp_remove_{idx}_{selected_id}", help="Remove server"
                ):
                    servers_to_remove.append(idx)

            # Transport selector
            current_transport = str(server.get("transport", "streamable-http")).strip()
            if current_transport not in transport_options:
                current_transport = "streamable-http"

            new_transport = st.selectbox(
                "Transport",
                options=transport_options,
                index=transport_options.index(current_transport),
                key=f"mcp_transport_{idx}_{selected_id}",
                help="Choose communication protocol for the MCP server.",
            )
            servers_to_edit[idx]["transport"] = new_transport

            if new_transport in {"streamable-http", "sse"}:
                # URL field
                url_val = str(server.get("url", ""))
                new_url = st.text_input(
                    f"URL ({new_transport})",
                    value=url_val,
                    key=f"mcp_url_{idx}_{selected_id}",
                    placeholder="https://...",
                    help="HTTP endpoint for the MCP server",
                )
                servers_to_edit[idx]["url"] = new_url
                if "command" in servers_to_edit[idx]:
                    servers_to_edit[idx]["command"] = ""
            else:
                # Command field
                cmd_val = str(server.get("command", ""))
                new_cmd = st.text_input(
                    "Command (stdio)",
                    value=cmd_val,
                    key=f"mcp_cmd_{idx}_{selected_id}",
                    placeholder="npx -y @openbnb/mcp-server-airbnb",
                    help="Command to run the stdio MCP server process locally",
                )
                servers_to_edit[idx]["command"] = new_cmd
                if "url" in servers_to_edit[idx]:
                    servers_to_edit[idx]["url"] = ""

            st.divider()

    # Remove marked servers
    for idx in sorted(servers_to_remove, reverse=True):
        if 0 <= idx < len(servers_to_edit):
            servers_to_edit.pop(idx)

    # Add server button
    col_add, col_example = st.columns([1, 2])
    with col_add:
        if st.button("➕ Add MCP Server", key=f"mcp_add_{selected_id}"):
            servers_to_edit.append(
                {
                    "name": f"server-{len(servers_to_edit) + 1}",
                    "enabled": False,
                    "transport": "streamable-http",
                    "url": "",
                    "command": "",
                }
            )

    with col_example:
        if st.button(
            "➕ Add Agno Docs MCP",
            key=f"mcp_add_agno_{selected_id}",
            help="Add public Agno documentation MCP server",
        ):
            servers_to_edit.append(
                {
                    "name": "agno-docs",
                    "enabled": False,
                    "transport": "streamable-http",
                    "url": "https://docs.agno.com/mcp",
                    "command": "",
                }
            )

    # Update session state
    st.session_state[mcp_key] = servers_to_edit

    tool_settings = (
        current.get("tool_settings", {})
        if isinstance(current.get("tool_settings"), dict)
        else {}
    )
    st.subheader("Tool Settings")
    if "pubmed" in selected_tools:
        pubmed_settings = (
            tool_settings.get("pubmed", {})
            if isinstance(tool_settings.get("pubmed"), dict)
            else {}
        )
        pubmed_email = st.text_input(
            "PubMed E-Mail", value=str(pubmed_settings.get("email", ""))
        )
        pubmed_max_results = int(
            st.number_input(
                "PubMed Max Results",
                min_value=1,
                value=int(pubmed_settings.get("max_results") or 5),
            )
        )
        pubmed_enable = st.checkbox(
            "PubMed Suche aktiv",
            value=bool(pubmed_settings.get("enable_search_pubmed", True)),
        )
        pubmed_all = st.checkbox(
            "PubMed Alle Quellen",
            value=bool(pubmed_settings.get("all", False)),
        )
    if "websearch" in selected_tools:
        websearch_settings = (
            tool_settings.get("websearch", {})
            if isinstance(tool_settings.get("websearch"), dict)
            else {}
        )
        websearch_backend_options = [
            "",
            "duckduckgo",
            "google",
            "bing",
            "brave",
            "yandex",
        ]
        websearch_backend_default = str(websearch_settings.get("backend", ""))
        if websearch_backend_default not in websearch_backend_options:
            websearch_backend_default = ""
        websearch_backend = st.selectbox(
            "WebSearch Backend",
            options=websearch_backend_options,
            index=websearch_backend_options.index(websearch_backend_default),
        )
        websearch_num_results = int(
            st.number_input(
                "WebSearch Max Results",
                min_value=1,
                value=int(websearch_settings.get("num_results") or 5),
            )
        )
    if "youtube" in selected_tools:
        youtube_settings = (
            tool_settings.get("youtube", {})
            if isinstance(tool_settings.get("youtube"), dict)
            else {}
        )
        youtube_fetch_captions = st.checkbox(
            "YouTube Captions aktiv",
            value=bool(youtube_settings.get("fetch_captions", True)),
        )
        youtube_fetch_video_info = st.checkbox(
            "YouTube Video-Infos aktiv",
            value=bool(youtube_settings.get("fetch_video_info", True)),
        )
        youtube_fetch_timestamps = st.checkbox(
            "YouTube Timestamps aktiv",
            value=bool(youtube_settings.get("fetch_timestamps", False)),
        )
    if "duckduckgo" in selected_tools:
        duckduckgo_settings = (
            tool_settings.get("duckduckgo", {})
            if isinstance(tool_settings.get("duckduckgo"), dict)
            else {}
        )
        duckduckgo_enable_search = st.checkbox(
            "DuckDuckGo Suche aktiv",
            value=bool(duckduckgo_settings.get("enable_search", True)),
        )
        duckduckgo_enable_news = st.checkbox(
            "DuckDuckGo News aktiv",
            value=bool(duckduckgo_settings.get("enable_news", True)),
        )
        duckduckgo_fixed_max_results = int(
            st.number_input(
                "DuckDuckGo Max Results",
                min_value=1,
                value=int(duckduckgo_settings.get("fixed_max_results") or 5),
            )
        )
        duckduckgo_timeout = int(
            st.number_input(
                "DuckDuckGo Timeout (Sek)",
                min_value=1,
                value=int(duckduckgo_settings.get("timeout") or 10),
            )
        )
        duckduckgo_verify_ssl = st.checkbox(
            "DuckDuckGo SSL verifizieren",
            value=bool(duckduckgo_settings.get("verify_ssl", True)),
        )
    if "arxiv" in selected_tools:
        arxiv_settings = (
            tool_settings.get("arxiv", {})
            if isinstance(tool_settings.get("arxiv"), dict)
            else {}
        )
        arxiv_max_results = int(
            st.number_input(
                "arXiv Max Results",
                min_value=1,
                max_value=50,
                value=int(arxiv_settings.get("max_results") or 5),
            )
        )
        arxiv_sort_options = ["", "submittedDate", "lastUpdatedDate", "relevance"]
        arxiv_sort_default = str(arxiv_settings.get("sort_by", ""))
        if arxiv_sort_default not in arxiv_sort_options:
            arxiv_sort_default = ""
        arxiv_sort_by = st.selectbox(
            "arXiv Sortierung",
            options=arxiv_sort_options,
            index=arxiv_sort_options.index(arxiv_sort_default),
        )
    if "website" in selected_tools:
        website_settings = (
            tool_settings.get("website", {})
            if isinstance(tool_settings.get("website"), dict)
            else {}
        )
        website_max_pages = int(
            st.number_input(
                "Website Max Pages",
                min_value=1,
                max_value=20,
                value=max(1, min(20, int(website_settings.get("max_pages") or 5))),
            )
        )
        website_timeout = int(
            st.number_input(
                "Website Timeout (Sek)",
                min_value=1,
                max_value=120,
                value=max(1, min(120, int(website_settings.get("timeout") or 10))),
            )
        )
        website_allowed_domains_raw = st.text_area(
            "Website erlaubte Domains (eine pro Zeile)",
            value="\n".join(
                str(domain).strip()
                for domain in website_settings.get("allowed_domains", [])
                if str(domain).strip()
            ),
        )
    if "hackernews" in selected_tools:
        hackernews_settings = (
            tool_settings.get("hackernews", {})
            if isinstance(tool_settings.get("hackernews"), dict)
            else {}
        )
        hackernews_enable_top_stories = st.checkbox(
            "HackerNews Top Stories aktiv",
            value=bool(hackernews_settings.get("enable_get_top_stories", True)),
        )
        hackernews_enable_user_details = st.checkbox(
            "HackerNews User-Details aktiv",
            value=bool(hackernews_settings.get("enable_get_user_details", True)),
        )
        hackernews_all = st.checkbox(
            "HackerNews Alle Funktionen",
            value=bool(hackernews_settings.get("all", False)),
        )
    if "yfinance" in selected_tools:
        yfinance_settings = (
            tool_settings.get("yfinance", {})
            if isinstance(tool_settings.get("yfinance"), dict)
            else {}
        )
        yfinance_stock_price = st.checkbox(
            "YFinance Aktienkurs aktiv",
            value=bool(yfinance_settings.get("stock_price", True)),
        )
        yfinance_analyst_recommendations = st.checkbox(
            "YFinance Analystenempfehlungen aktiv",
            value=bool(yfinance_settings.get("analyst_recommendations", True)),
        )

    st.subheader("Routing & Runtime")
    model = st.text_input("Model override", value=str(current.get("model", "")))
    memory_scope = st.text_input(
        "Memory scope", value=str(current.get("memory_scope", ""))
    )
    coordination_options = [
        "",
        "direct_only",
        "delegate_on_complexity",
        "always_delegate",
        "coordinated_rag",
    ]
    current_mode = str(current.get("coordination_mode", ""))
    if current_mode not in coordination_options:
        coordination_options.append(current_mode)
    coordination_mode = st.selectbox(
        "Coordination mode",
        options=coordination_options,
        index=coordination_options.index(current_mode),
        help="Controls how the master agent delegates to team members.",
    )
    stream_events = st.checkbox(
        "Stream events", value=bool(current.get("stream_events", True))
    )

    if st.button("Save configuration", type="primary"):
        # Get MCP servers from session state
        mcp_servers_to_save = st.session_state.get(mcp_key, [])
        if not isinstance(mcp_servers_to_save, list):
            mcp_servers_to_save = []

        combined_tools = selected_tools + _parse_lines(extra_tools_raw)
        updated_tool_settings: Dict[str, object] = {}
        if "pubmed" in selected_tools:
            updated_tool_settings["pubmed"] = {
                "email": pubmed_email.strip() or None,
                "max_results": pubmed_max_results,
                "enable_search_pubmed": pubmed_enable,
                "all": pubmed_all,
            }
        if "websearch" in selected_tools:
            updated_tool_settings["websearch"] = {
                "backend": websearch_backend.strip() or None,
                "num_results": websearch_num_results,
            }
        if "youtube" in selected_tools:
            updated_tool_settings["youtube"] = {
                "fetch_captions": youtube_fetch_captions,
                "fetch_video_info": youtube_fetch_video_info,
                "fetch_timestamps": youtube_fetch_timestamps,
            }
        if "duckduckgo" in selected_tools:
            updated_tool_settings["duckduckgo"] = {
                "enable_search": duckduckgo_enable_search,
                "enable_news": duckduckgo_enable_news,
                "fixed_max_results": duckduckgo_fixed_max_results,
                "timeout": duckduckgo_timeout,
                "verify_ssl": duckduckgo_verify_ssl,
            }
        if "arxiv" in selected_tools:
            updated_tool_settings["arxiv"] = {
                "max_results": arxiv_max_results,
                "sort_by": arxiv_sort_by.strip() or None,
            }
        if "website" in selected_tools:
            updated_tool_settings["website"] = {
                "max_pages": website_max_pages,
                "timeout": website_timeout,
                "allowed_domains": _parse_lines(website_allowed_domains_raw),
            }
        if "hackernews" in selected_tools:
            updated_tool_settings["hackernews"] = {
                "enable_get_top_stories": hackernews_enable_top_stories,
                "enable_get_user_details": hackernews_enable_user_details,
                "all": hackernews_all,
            }
        if "yfinance" in selected_tools:
            updated_tool_settings["yfinance"] = {
                "stock_price": yfinance_stock_price,
                "analyst_recommendations": yfinance_analyst_recommendations,
            }
        updated = {
            **current,
            "name": name.strip(),
            "description": description.strip(),
            "role": role.strip(),
            "instructions": instructions.strip(),
            "skills": _parse_lines(skills_raw),
            "tools": combined_tools,
            "tool_settings": updated_tool_settings,
            "mcp_calls": _parse_lines(mcp_raw),
            "mcp_servers": mcp_servers_to_save,
            "model": model.strip() or None,
            "memory_scope": memory_scope.strip() or None,
            "coordination_mode": coordination_mode.strip() or None,
            "stream_events": stream_events,
            "enabled": enabled,
        }
        updated = {k: v for k, v in updated.items() if v is not None}
        try:
            json.dumps(updated)
        except TypeError as exc:
            st.error(f"Config is not JSON-serializable: {exc}")
            return
        try:
            _save_config(selected_id, updated)
        except Exception as exc:
            st.error(f"Failed to save config: {exc}")
        else:
            st.success("Saved.")


if __name__ == "__main__":
    render_agent_config_page()
