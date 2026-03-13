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


def _render_mcp_servers_ui(
    selected_id: str,
    current: Dict[str, object],
    is_admin: bool,
) -> List[Dict[str, object]]:
    """Renders the MCP Servers UI and returns the updated server list."""
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
        "youtube_transcript": "YouTube Transkript",
        "duckduckgo": "DuckDuckGo Suche",
        "arxiv": "arXiv Papers",
        "website": "Website Inhalte",
        "hackernews": "Hacker News",
        "yfinance": "Yahoo Finance",
        "calculator": "Calculator",
        "wikipedia": "Wikipedia Suche",
        "mermaid": "Mermaid Diagramme",
        "image": "Bildgenerierung (GPT Image)",
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

    # Check admin role
    is_admin = bool(
        st.session_state.get("is_admin", True)
    )  # default True for testing/development

    if not is_admin:
        st.info(
            "ℹ️ MCP Server configuration requires administrative privileges. You can view the current setup below."
        )

    mcp_servers = list(current.get("mcp_servers", []))
    if not isinstance(mcp_servers, list):
        mcp_servers = []

    # Initialize session state for MCP servers if not present
    mcp_key = f"mcp_servers_{selected_id}"
    if mcp_key not in st.session_state:
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
                    disabled=not is_admin,
                )
                if is_admin:
                    servers_to_edit[idx]["enabled"] = enabled

            with col_remove:
                if st.button(
                    "🗑️",
                    key=f"mcp_remove_{idx}_{selected_id}",
                    help="Remove server",
                    disabled=not is_admin,
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
                disabled=not is_admin,
            )
            if is_admin:
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
                    disabled=not is_admin,
                )
                if is_admin:
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
                    disabled=not is_admin,
                )
                if is_admin:
                    servers_to_edit[idx]["command"] = new_cmd
                    if "url" in servers_to_edit[idx]:
                        servers_to_edit[idx]["url"] = ""

            st.divider()

    # Remove marked servers
    if is_admin:
        for idx in sorted(servers_to_remove, reverse=True):
            if 0 <= idx < len(servers_to_edit):
                servers_to_edit.pop(idx)

    # Add server button
    col_add, col_example = st.columns([1, 2])
    with col_add:
        if st.button(
            "➕ Add MCP Server", key=f"mcp_add_{selected_id}", disabled=not is_admin
        ):
            if is_admin:
                servers_to_edit.append(
                    {
                        "name": f"new-mcp-server-{len(servers_to_edit)+1}",
                        "enabled": False,
                        "url": "https://...",
                        "transport": "streamable-http",
                    }
                )

    with col_example:
        if st.button(
            "➕ Add Agno Docs MCP",
            key=f"mcp_add_agno_{selected_id}",
            help="Add public Agno documentation MCP server",
            disabled=not is_admin,
        ):
            if is_admin:
                servers_to_edit.append(
                    {
                        "name": "agno-docs",
                        "enabled": False,
                        "transport": "streamable-http",
                        "url": "https://docs.agno.com/mcp",
                        "command": "",
                    }
                )

        if st.button(
            "➕ Add SQLite MCP",
            key=f"mcp_add_sqlite_{selected_id}",
            help="Add official SQLite MCP Server via npx",
            disabled=not is_admin,
        ):
            if is_admin:
                servers_to_edit.append(
                    {
                        "name": "sqlite",
                        "enabled": False,
                        "transport": "stdio",
                        "url": "",
                        "command": 'npx -y @modelcontextprotocol/server-sqlite --db "c:\\temp\\test.db"',
                    }
                )

        if st.button(
            "➕ Add File System MCP",
            key=f"mcp_add_fs_{selected_id}",
            help="Add official File System MCP Server via npx",
            disabled=not is_admin,
        ):
            if is_admin:
                servers_to_edit.append(
                    {
                        "name": "filesystem",
                        "enabled": False,
                        "transport": "stdio",
                        "url": "",
                        "command": 'npx -y @modelcontextprotocol/server-filesystem "c:\\temp"',
                    }
                )

        if st.button(
            "➕ Add Airbnb MCP",
            key=f"mcp_add_airbnb_{selected_id}",
            help="Add Airbnb MCP Server via npx",
            disabled=not is_admin,
        ):
            if is_admin:
                servers_to_edit.append(
                    {
                        "name": "airbnb",
                        "enabled": False,
                        "transport": "stdio",
                        "url": "",
                        "command": "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
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
    if "youtube_transcript" in selected_tools:
        youtube_transcript_settings = (
            tool_settings.get("youtube_transcript", {})
            if isinstance(tool_settings.get("youtube_transcript"), dict)
            else {}
        )
        youtube_transcript_fetch_captions = st.checkbox(
            "YouTube Transkript: Captions aktiv",
            value=bool(youtube_transcript_settings.get("fetch_captions", True)),
        )
        youtube_transcript_fetch_video_info = st.checkbox(
            "YouTube Transkript: Video-Infos aktiv",
            value=bool(youtube_transcript_settings.get("fetch_video_info", False)),
        )
        youtube_transcript_fetch_timestamps = st.checkbox(
            "YouTube Transkript: Timestamps aktiv",
            value=bool(youtube_transcript_settings.get("fetch_timestamps", True)),
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
    if "image" in selected_tools:
        image_settings = (
            tool_settings.get("image", {})
            if isinstance(tool_settings.get("image"), dict)
            else {}
        )
        image_model_options = ["gpt-image-1.5"]
        current_image_model = str(image_settings.get("image_model", "gpt-image-1.5"))
        if current_image_model not in image_model_options:
            image_model_options.append(current_image_model)
        image_model = st.selectbox(
            "GPT Image Model",
            options=image_model_options,
            index=image_model_options.index(current_image_model),
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
        # Try both UI keys, prefer whichever has elements
        mcp_key = f"mcp_servers_{selected_id}"
        mcp_servers_to_save = st.session_state.get(mcp_key, [])

        adv_mcp_key = f"mcp_servers_adv_{selected_id}"
        adv_mcp_servers = st.session_state.get(adv_mcp_key, [])

        # If advanced tab has more up to date info (it usually stays in sync via current config)
        if len(adv_mcp_servers) > len(mcp_servers_to_save):
            mcp_servers_to_save = adv_mcp_servers

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
        if "youtube_transcript" in selected_tools:
            updated_tool_settings["youtube_transcript"] = {
                "fetch_captions": youtube_transcript_fetch_captions,
                "fetch_video_info": youtube_transcript_fetch_video_info,
                "fetch_timestamps": youtube_transcript_fetch_timestamps,
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
        if "image" in selected_tools:
            updated_tool_settings["image"] = {
                "image_model": image_model,
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


def _render_team_builder_tab() -> None:
    """Render the Team Builder tab for creating agent teams."""
    st.subheader("Team Builder")
    st.caption("Create and configure teams of agents for coordinated task execution.")

    try:
        configs = _load_configs()
    except Exception as exc:
        st.error(f"Failed to load agent configs: {exc}")
        return

    # Separate agents and teams
    agents = {
        aid: cfg for aid, cfg in configs.items() if cfg.get("type", "agent") == "agent"
    }
    teams = {tid: cfg for tid, cfg in configs.items() if cfg.get("type") == "team"}

    # Show existing teams
    st.markdown("### Existing Teams")
    if teams:
        team_options = ["(New Team)"] + list(teams.keys())
        selected_team = st.selectbox("Select team to edit", options=team_options)
    else:
        selected_team = st.selectbox("Select team to edit", options=["(New Team)"])
        st.info("No teams configured yet. Create a new team below.")

    # Team configuration
    if selected_team == "(New Team)":
        team_id = st.text_input("Team ID", placeholder="e.g., medical_team")
        team_name = st.text_input("Team Name", placeholder="e.g., Medical AI Team")
        team_description = st.text_area(
            "Description", placeholder="Describe the team's purpose..."
        )
        existing_config = {}
    else:
        existing_config = dict(teams[selected_team])
        team_id = st.text_input("Team ID", value=selected_team, disabled=True)
        team_name = st.text_input(
            "Team Name", value=str(existing_config.get("name", ""))
        )
        team_description = st.text_area(
            "Description", value=str(existing_config.get("description", ""))
        )

    # Member selection
    st.markdown("### Team Members")
    st.caption(
        "Select agents to include in this team. Members will be delegated tasks based on their skills."
    )

    available_agent_ids = list(agents.keys())
    current_members = existing_config.get("members", [])
    if not isinstance(current_members, list):
        current_members = []

    selected_members = st.multiselect(
        "Team Members",
        options=available_agent_ids,
        default=[m for m in current_members if m in available_agent_ids],
        format_func=lambda aid: f"{aid} ({agents.get(aid, {}).get('name', aid)})",
    )

    # Show member details
    if selected_members:
        st.markdown("#### Selected Members")
        for member_id in selected_members:
            member_cfg = agents.get(member_id, {})
            with st.expander(f"**{member_cfg.get('name', member_id)}** ({member_id})"):
                st.markdown(f"**Role:** {member_cfg.get('role', 'N/A')}")
                st.markdown(
                    f"**Skills:** {', '.join(member_cfg.get('skills', [])) or 'None'}"
                )
                st.markdown(
                    f"**Tools:** {', '.join(member_cfg.get('tools', [])) or 'None'}"
                )

    # Coordination mode
    st.markdown("### Coordination Settings")
    coordination_options = [
        "delegate_on_complexity",
        "always_delegate",
        "coordinated_rag",
        "direct_only",
    ]
    current_mode = str(
        existing_config.get("coordination_mode", "delegate_on_complexity")
    )
    if current_mode not in coordination_options:
        current_mode = "delegate_on_complexity"

    coordination_mode = st.selectbox(
        "Coordination Mode",
        options=coordination_options,
        index=coordination_options.index(current_mode),
        help=(
            "delegate_on_complexity: Route to members based on skill matching. "
            "always_delegate: Always involve all members. "
            "coordinated_rag: RAG-focused with source citations. "
            "direct_only: No delegation, master handles all."
        ),
    )

    # Team-level model
    team_model = st.text_input(
        "Team Model Override",
        value=str(existing_config.get("model", "")),
        placeholder="e.g., openai:gpt-4.1",
        help="Model used by the team coordinator. Members can have their own models.",
    )

    # Team instructions
    team_instructions = st.text_area(
        "Team Instructions",
        value=str(existing_config.get("instructions", "")),
        height=120,
        placeholder="Instructions for the team coordinator...",
    )

    # Team skills
    team_skills_raw = st.text_area(
        "Team Skills (one per line)",
        value=_as_text_lines(existing_config.get("skills")),
        help="Skills that describe the team's collective capabilities.",
    )

    # Save button
    col_save, col_delete = st.columns([1, 1])

    with col_save:
        if st.button("Save Team", type="primary"):
            if not team_id or selected_team == "(New Team)" and team_id in configs:
                st.error("Team ID is required and must be unique.")
            elif not selected_members:
                st.warning("Please select at least one team member.")
            else:
                team_config = {
                    "id": team_id,
                    "name": team_name.strip() or team_id,
                    "description": team_description.strip(),
                    "type": "team",
                    "members": selected_members,
                    "coordination_mode": coordination_mode,
                    "model": team_model.strip() or None,
                    "instructions": team_instructions.strip(),
                    "skills": _parse_lines(team_skills_raw),
                    "enabled": True,
                }
                # Remove None values
                team_config = {k: v for k, v in team_config.items() if v is not None}

                try:
                    _save_config(team_id, team_config)
                    st.success(f"Team '{team_id}' saved successfully!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to save team: {exc}")

    with col_delete:
        if selected_team != "(New Team)":
            if st.button("Delete Team", type="secondary"):
                try:
                    # Mark as disabled rather than delete to preserve references
                    disabled_config = dict(existing_config)
                    disabled_config["enabled"] = False
                    _save_config(selected_team, disabled_config)
                    st.success(f"Team '{selected_team}' disabled.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Failed to disable team: {exc}")


def _render_agent_config_tab(is_admin: bool) -> None:
    """Render the Agent Config tab (original functionality)."""
    _render_mcp_servers_ui("agent_config_page", {}, is_admin)


def render_agent_config_page() -> None:
    """Entrypoint for Streamlit multipage navigation."""
    main._init_state()
    main.render_sidebar()
    if not main.require_access("logged_in"):
        st.stop()
    st.title("Agent Configuration")
    st.caption(
        "Configure agents and teams. Agents are individual AI specialists; "
        "Teams coordinate multiple agents for complex tasks."
    )

    is_admin = bool(st.session_state.get("is_admin", True))

    tab_agent, tab_team = st.tabs(["Agent Config", "Team Builder"])

    with tab_agent:
        _render_agent_config_tab(is_admin)

    with tab_team:
        _render_team_builder_tab()


if __name__ == "__main__":
    render_agent_config_page()
