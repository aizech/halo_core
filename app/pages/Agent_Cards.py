"""Agent Cards page - Cinematic set cards for HALO Core agents."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st
from app import main
from services.agents_config import load_agent_configs

# Assets directory (relative to this file's location)
_ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Medical agent ID -> SVG filename mapping
_MEDICAL_AGENT_IMAGES: dict[str, str] = {
    "chief_doctor": "agent_chief_doctor.svg",
    "cardiologist": "agent_cardiologist.svg",
    "radiologist": "agent_radiologist.svg",
    "pharmacist": "agent_pharmacist.svg",
    "medical_researcher": "agent_medical_researcher.svg",
    "medical_scribe": "agent_medical_scribe.svg",
}


def _svg_data_uri(filename: str) -> str | None:
    """Return a data URI for an SVG asset, or None if missing."""
    path = _ASSETS_DIR / filename
    if not path.exists():
        return None
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/svg+xml;base64,{data}"


# Material icon names per category/agent type
_MATERIAL_ICONS: dict[str, str] = {
    "Medical": "stethoscope",
    "Marketing / Content": "campaign",
    "Teams": "groups",
    "General / Research": "psychology",
    "team": "groups",
    "agent": "smart_toy",
    # Per-agent overrides
    "chat": "chat",
    "data_analyst": "bar_chart",
    "note_taker": "edit_note",
    "summarizer": "summarize",
    "web_researcher": "travel_explore",
    "image_creator": "image",
    "content_writer": "edit",
    "seo_optimizer": "search",
    "general_assistant": "support_agent",
}


def _get_material_icon(agent_id: str, category: str, agent_type: str) -> str:
    """Return a Material icon name for an agent."""
    if agent_id in _MATERIAL_ICONS:
        return _MATERIAL_ICONS[agent_id]
    if agent_type == "team":
        return "groups"
    return _MATERIAL_ICONS.get(category, "smart_toy")


def get_agent_category_and_emoji(agent_id: str, agent_config: dict) -> tuple[str, str]:
    """Return category and material icon for an agent based on its ID and configuration."""
    agent_id_lower = agent_id.lower()
    name_lower = str(agent_config.get("name", "")).lower()
    role_lower = str(agent_config.get("role", "")).lower()

    # Medical agents
    medical_keywords = [
        "medical",
        "doctor",
        "chief",
        "radiology",
        "cardiology",
        "pharmacy",
        "pharmacist",
        "research",
        "documentation",
    ]
    if any(
        keyword in agent_id_lower or keyword in name_lower or keyword in role_lower
        for keyword in medical_keywords
    ):
        return "Medical", "stethoscope"

    # Content/Marketing agents
    content_keywords = [
        "content",
        "writer",
        "seo",
        "optimizer",
        "image",
        "creator",
        "marketing",
    ]
    if any(
        keyword in agent_id_lower or keyword in name_lower or keyword in role_lower
        for keyword in content_keywords
    ):
        return "Marketing / Content", "campaign"

    # Teams
    if agent_config.get("type") == "team" or "team" in agent_id_lower:
        return "Teams", "groups"

    # Data/Research agents
    research_keywords = [
        "research",
        "data",
        "analyst",
        "pubmed",
        "web",
        "note",
        "summarizer",
    ]
    if any(
        keyword in agent_id_lower or keyword in name_lower or keyword in role_lower
        for keyword in research_keywords
    ):
        return "General / Research", "psychology"

    return "General / Research", "smart_toy"


def render_agent_card(agent_id: str, agent_config: dict) -> None:
    """Render a single agent card in profile card style."""
    category, icon_name = get_agent_category_and_emoji(agent_id, agent_config)

    name = agent_config.get("name", agent_id)
    role = agent_config.get("role", "Agent")
    agent_type = agent_config.get("type", "agent")
    model = agent_config.get("model", "Default") or "Default"
    description = agent_config.get("description", "No description available.")
    skills = agent_config.get("skills", [])
    tools = agent_config.get("tools", [])
    members = agent_config.get("members", [])

    # Truncate description for "About" section
    desc_short = description[:160] + "…" if len(description) > 160 else description

    # Avatar: SVG image for known medical agents, Material icon otherwise
    svg_uri = (
        _svg_data_uri(_MEDICAL_AGENT_IMAGES[agent_id])
        if agent_id in _MEDICAL_AGENT_IMAGES
        else None
    )
    if svg_uri:
        avatar_html = f'<img src="{svg_uri}" class="pc-avatar-img" alt="{name}"/>'
    else:
        mat_icon = _get_material_icon(agent_id, category, agent_type)
        avatar_html = (
            f'<span class="pc-avatar-icon material-symbols-outlined">{mat_icon}</span>'
        )

    # Build skill + tool chips HTML
    skill_chips_html = "".join(
        f'<span class="pc-chip pc-chip-skill">{s}</span>'
        for s in (skills[:5] if skills else ["General"])
    )
    tool_chips_html = "".join(
        f'<span class="pc-chip pc-chip-tool">{t}</span>'
        for t in (tools[:5] if tools else ["—"])
    )

    type_class = "pc-badge-team" if agent_type == "team" else "pc-badge-agent"
    type_label = agent_type.upper()

    members_html = ""
    if agent_type == "team" and members:
        member_chips = "".join(
            f'<span class="pc-chip pc-chip-member">{m}</span>' for m in members[:4]
        )
        if len(members) > 4:
            member_chips += (
                f'<span class="pc-chip pc-chip-member">+{len(members) - 4}</span>'
            )
        members_html = (
            '<div class="pc-section-label">Members</div>'
            f'<div class="pc-chips">{member_chips}</div>'
        )

    stat3_value = str(len(members)) if agent_type == "team" else "—"
    stat3_label = "Members" if agent_type == "team" else "Type"

    card_html = (
        '<div class="pc-card">'
        '<div class="pc-avatar-wrap">'
        + avatar_html
        + f'<div class="pc-type-dot {type_class}">{type_label}</div>'
        "</div>"
        f'<div class="pc-name">{name}</div>'
        f'<div class="pc-role">{role}</div>'
        f'<div class="pc-model-tag">{model}</div>'
        '<div class="pc-stats">'
        f'<div class="pc-stat"><div class="pc-stat-value">{len(skills) or 1}</div><div class="pc-stat-label">Skills</div></div>'
        '<div class="pc-stat-divider"></div>'
        f'<div class="pc-stat"><div class="pc-stat-value">{len(tools) or 0}</div><div class="pc-stat-label">Tools</div></div>'
        '<div class="pc-stat-divider"></div>'
        f'<div class="pc-stat"><div class="pc-stat-value">{stat3_value}</div><div class="pc-stat-label">{stat3_label}</div></div>'
        "</div>"
        '<div class="pc-about-label">About</div>'
        f'<div class="pc-about-text">{desc_short}</div>'
        '<div class="pc-section-label">Skills</div>'
        f'<div class="pc-chips">{skill_chips_html}</div>'
        '<div class="pc-section-label">Tools</div>'
        f'<div class="pc-chips">{tool_chips_html}</div>' + members_html + "</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander(f"Full Details: {name}", expanded=False):
        st.markdown(f"**ID:** `{agent_id}`")
        st.markdown(f"**Role:** {role}")
        st.markdown(f"**Type:** {type_label}")
        st.markdown(f"**Model:** {model}")
        st.markdown(f"**Description:** {description}")
        if skills:
            st.markdown(f"**Skills:** {', '.join(skills)}")
        if tools:
            st.markdown(f"**Tools:** {', '.join(tools)}")
        if agent_type == "team" and members:
            st.markdown(f"**Members:** {', '.join(members)}")
        instructions = agent_config.get("instructions", "")
        if instructions:
            st.markdown("**Instructions:**")
            if isinstance(instructions, list):
                instructions = "\n".join(instructions)
            st.text_area(
                "",
                instructions,
                height=100,
                disabled=True,
                key=f"instructions_{agent_id}",
            )


def render_agent_cards_page() -> None:
    """Render the main Agent Cards page."""
    # Initialize main app state and sidebar
    main._init_state()
    main.render_sidebar()

    st.set_page_config(
        page_title="Agent Cards",
        page_icon=":material/smart_toy:",
        layout="wide",
    )

    # Page title and introduction
    st.markdown("# Agent Cards")
    st.markdown("Cinematic set cards for all HALO Core agents and teams.")

    # Load agent configurations
    try:
        agent_configs = load_agent_configs()
    except Exception as e:
        st.error(f"Failed to load agent configurations: {e}")
        return

    if not agent_configs:
        st.info("No agent configurations found. Please configure some agents first.")
        return

    # Extract teams for filtering
    teams = []
    individual_agents = []

    for agent_id, config in agent_configs.items():
        if config.get("type") == "team":
            teams.append((agent_id, config.get("name", agent_id), config))
        else:
            individual_agents.append((agent_id, config))

    # Team selector at the top
    st.markdown("### Filter by Team")
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        team_options = ["All Teams"] + [team[1] for team in teams]
        selected_team = st.selectbox(
            "Select Team:",
            options=team_options,
            key="team_selector",
            help="Choose a team to see its members, or select 'All Teams' to see all agents",
        )

    with col2:
        st.markdown(f"**Teams Available:** {len(teams)}")

    with col3:
        st.markdown(f"**Individual Agents:** {len(individual_agents)}")

    # Group agents by category
    categories = {
        "Medical": [],
        "Marketing / Content": [],
        "General / Research": [],
        "Teams": [],
    }

    # Filter agents based on team selection
    filtered_agents = {}

    if selected_team == "All Teams":
        # Show all agents
        filtered_agents = agent_configs
    else:
        # Find the selected team and get its members
        selected_team_config = None
        for team_id, team_name, team_config in teams:
            if team_name == selected_team:
                selected_team_config = team_config
                break

        if selected_team_config:
            # Add the team itself
            filtered_agents[selected_team_config.get("id")] = selected_team_config

            # Add team members
            team_members = selected_team_config.get("members", [])
            for member_id in team_members:
                if member_id in agent_configs:
                    filtered_agents[member_id] = agent_configs[member_id]
        else:
            filtered_agents = agent_configs  # Fallback to all if team not found

    # Categorize filtered agents
    for agent_id, config in filtered_agents.items():
        category, _ = get_agent_category_and_emoji(agent_id, config)
        if category in categories:
            categories[category].append((agent_id, config))

    # Show selected team info if a specific team is selected
    if selected_team != "All Teams" and selected_team_config:
        st.markdown("---")
        st.markdown(f"### 📋 Team: {selected_team}")

        team_description = selected_team_config.get(
            "description", "No description available."
        )
        st.markdown(f"**Description:** {team_description}")

        team_skills = selected_team_config.get("skills", [])
        if team_skills:
            st.markdown(f"**Team Skills:** {', '.join(team_skills)}")

        team_tools = selected_team_config.get("tools", [])
        if team_tools:
            st.markdown(f"**Team Tools:** {', '.join(team_tools)}")

        st.markdown("---")

    # Load Material Symbols font
    st.markdown(
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0"/>',
        unsafe_allow_html=True,
    )

    # Inject CSS styling — profile card style
    st.markdown(
        """
    <style>
    /* ── Material Symbols ───────────────────────────────────── */
    .material-symbols-outlined {
        font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 48;
        font-size: 44px;
        line-height: 1;
    }

    /* ── Profile Card ───────────────────────────────────────── */
    .pc-card {
        background: #1e2329;
        border: 1px solid #2d333b;
        border-radius: 20px;
        padding: 24px 20px 20px;
        margin-bottom: 20px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 2px 12px rgba(0,0,0,0.35);
    }
    .pc-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 28px rgba(234,146,22,0.18);
        border-color: rgba(234,146,22,0.45);
    }

    /* Avatar */
    .pc-avatar-wrap {
        position: relative;
        display: inline-block;
        margin-bottom: 14px;
    }
    .pc-avatar {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: rgba(234,146,22,0.12);
        border: 3px solid rgba(234,146,22,0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 0 auto;
    }
    /* SVG image avatar */
    .pc-avatar-img {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        border: 3px solid rgba(234,146,22,0.5);
        object-fit: cover;
        display: block;
        margin: 0 auto;
        background: rgba(234,146,22,0.08);
    }
    /* Material icon avatar */
    .pc-avatar-icon {
        width: 80px;
        height: 80px;
        border-radius: 50%;
        background: rgba(234,146,22,0.10);
        border: 3px solid rgba(234,146,22,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        color: #EA9216;
    }
    .pc-type-dot {
        position: absolute;
        bottom: 2px;
        right: -4px;
        font-size: 9px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 10px;
        border: 2px solid #1e2329;
    }
    .pc-badge-agent { background: #EA9216; color: #1a1a1a; }
    .pc-badge-team  { background: #16C5B8; color: #1a1a1a; }

    /* Name / Role / Model */
    .pc-name {
        font-size: 17px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 4px;
        line-height: 1.2;
    }
    .pc-role {
        font-size: 12px;
        color: #EA9216;
        margin-bottom: 6px;
        font-weight: 500;
    }
    .pc-model-tag {
        display: inline-block;
        font-size: 10px;
        font-family: monospace;
        background: rgba(255,255,255,0.07);
        color: #888;
        padding: 2px 8px;
        border-radius: 6px;
        margin-bottom: 16px;
    }

    /* Stats row */
    .pc-stats {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 0;
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        padding: 10px 0;
        margin-bottom: 18px;
    }
    .pc-stat {
        flex: 1;
        text-align: center;
    }
    .pc-stat-value {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
        line-height: 1;
    }
    .pc-stat-label {
        font-size: 10px;
        color: #888;
        margin-top: 3px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .pc-stat-divider {
        width: 1px;
        height: 32px;
        background: rgba(255,255,255,0.1);
    }

    /* About section */
    .pc-about-label {
        text-align: left;
        font-size: 13px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 6px;
    }
    .pc-about-text {
        text-align: left;
        font-size: 12px;
        color: #9aa5b4;
        line-height: 1.55;
        margin-bottom: 16px;
    }

    /* Section labels + chips */
    .pc-section-label {
        text-align: left;
        font-size: 12px;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 7px;
        margin-top: 4px;
    }
    .pc-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 14px;
        justify-content: flex-start;
    }
    .pc-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 500;
        cursor: default;
    }
    .pc-chip-skill {
        background: rgba(106,137,204,0.15);
        color: #8BA4D8;
        border: 1px solid rgba(106,137,204,0.25);
    }
    .pc-chip-tool {
        background: rgba(139,195,74,0.13);
        color: #8BC34A;
        border: 1px solid rgba(139,195,74,0.22);
    }
    .pc-chip-member {
        background: rgba(234,146,22,0.12);
        color: #EA9216;
        border: 1px solid rgba(234,146,22,0.22);
    }

    /* Category headers */
    .category-header {
        color: #EA9216;
        font-size: 22px;
        font-weight: 700;
        margin: 32px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid rgba(234,146,22,0.25);
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Render each category
    for category_name, agents in categories.items():
        if agents:  # Only show categories with agents
            st.markdown(
                f'<div class="category-header">{category_name}</div>',
                unsafe_allow_html=True,
            )

            # Create columns for card grid
            cols = st.columns(3)
            for i, (agent_id, config) in enumerate(agents):
                with cols[i % 3]:
                    render_agent_card(agent_id, config)


# Main entry point
if __name__ == "__main__":
    render_agent_cards_page()
