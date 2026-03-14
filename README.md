# HALO Core - Holistic Agent Logical Orchestrator

HALO Core is an intelligence workspace for teams that need to turn raw information into clear, usable outputs.

Instead of juggling separate tools for files, chat, notes, and deliverables, HALO keeps the full workflow in one place:

1. Ingest sources
2. Ask grounded questions
3. Save high-value insights
4. Generate shareable artifacts

---

## Why teams choose HALO

- **Workflow-first**: built for end-to-end work, not one-off prompts.
- **Team-agent capable**: run specialized AI roles with delegation strategies.
- **Source-grounded**: answers are driven by selected evidence.
- **Transparent execution**: inspect tool calls, agent actions, and traces when needed.
- **Output-ready**: generate reports, infographics, podcasts, presentations, and data tables.

---

## Streamlit demo

Hosted demo: [halocore.streamlit.app](https://halocore.streamlit.app/)

Demo limitations:
- No persistent storage between sessions
- Download generated files immediately
- Session timeout after inactivity (~15-20 min)
- Shared resources can slow generation
- Cold starts may take a few seconds
- No access to your local files/env vars
- User memory backend is disabled on Streamlit Cloud

---

## Quickstart

### Prerequisites

- Python 3.11+
- FFmpeg (for audio/video transcription)
- OpenAI API key (and any MCP/provider credentials you use)
- Optional: Node/npm for frontend tooling

### Install

```bash
# Unix/Linux/macOS
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Windows PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "sk-..."
```

### Run

```bash
streamlit run app/main.py
```

Default UI includes a sidebar plus three work areas: **Sources**, **Chat**, and **Studio**.

---

## First win in 90 seconds

1. Upload 1-3 files in **Sources** (`+ Quellen hinzufuegen`).
2. Select those sources.
3. In **Chat**, ask for findings, risks, and actions.
4. Save the best answer as a note.
5. Generate a **Bericht** in **Studio**.

You now have a full source-to-output workflow running end to end.

### Agent teams quickstart

1. Open **Configuration** → **Agent Config**.
2. Select a pre-configured team (e.g., "Medical AI Team").
3. In **Chat**, enable team mode and ask a complex question.
4. Watch as different agents contribute specialized expertise.
5. Review the coordinated response with tool call traces.

---

## Core product areas

### Sources
- Upload and manage documents, data files, images, audio, video, and medical DICOM files
- Import connector results from Notion, Google Drive, and Microsoft 365
- Control exactly what context HALO may use
- Optional auto-anonymization for DICOM medical imaging

### Chat
- Source-grounded responses with citations
- Multimodal input support (text, images, audio, video)
- Team-agent orchestration with specialized roles
- Multiple coordination modes: direct, skill-based delegation, or team-wide
- Save responses directly into notes

### Summary of all sources
- Fast global briefing in Chat (`Zusammenfassung aller Quellen`)
- Detect stale summaries after source updates
- Pin summaries into notes

### Studio
- Template-driven output generation from current context
- Templates include: Bericht, Infografik, Podcast, Videouebersicht, Praesentation, Datentabelle
- Outputs are stored and exportable

### Notes
- Preserve approved reasoning and decisions
- Reuse notes as future sources

### DICOM Tools
- Medical imaging anonymization with HIPAA Safe Harbor compliance
- Configurable anonymization (patient, institution, study data)
- Batch processing of multiple DICOM files
- Export anonymization mapping as CSV
- PACS server integration for hospital systems

### Configuration and Agent Config
- Tune app behavior, presets, models, tools, and runtime options
- Configure advanced team coordination and MCP usage
- 15 pre-configured agents and 4 ready-to-use teams
- MCP connectors for Notion, Google Drive, and Microsoft 365
- DICOM medical imaging settings and PACS integration

---

## Data, persistence, and paths

- Sources, chat history, notes, and studio outputs are stored in `data/` by default.
- Set `HALO_DATA_DIR` to override storage location per environment.
- Studio templates are data-driven via `templates/studio_templates.json`.
- Chat presets are loaded from `presets.json`.

---

## Runtime controls

### Coordination modes (`coordination_mode`)
- `direct_only`: master answers directly
- `delegate_on_complexity`: delegates to matching members by skills
- `always_delegate`: delegates to all configured members
- `coordinated_rag`: delegates broadly with source-first RAG guidance

### Knowledge mode
- Agno `Knowledge` is wired to LanceDB in `data/lancedb` via `services/knowledge.py`
- `search_knowledge=True` is enabled when knowledge is available
- Team mode also enables knowledge search for `coordinated_rag`
- On Windows, vector search is used to avoid hybrid/FTS index lock issues

### Streaming
- Chat streams by default
- Per-agent `stream_events` enables event-rich streaming
- App-level `log_stream_events` enables verbose stream event logs

### Memory backend
- Default: JSON-only local persistence in `data/`
- Optional: set `HALO_AGENT_DB` to enable Agno SQLite-backed memory
- With DB enabled, agents/teams use bounded history (`num_history_runs=3`) and user memories

### DICOM Settings
- `DICOM_ANONYMIZE_ON_UPLOAD`: Auto-anonymize DICOM files on upload
- `DICOM_PACS_*`: PACS server configuration for hospital integration

### MCP Connector Credentials
- `NOTION_API_KEY`: Notion workspace integration
- `GOOGLE_OAUTH_CREDENTIALS`: Google Drive access (JSON credentials file)
- `MSAL_*`: Microsoft 365 / OneDrive authentication

### Structured trace telemetry
Each chat turn stores telemetry fields, including:
- `model`
- `selected_members`
- `tools`
- `stream_mode`, `stream_events`, `stream_result`
- `latency_ms`
- `knowledge_hits`, `knowledge_sources`
- `used_fallback`

---

## Troubleshooting runbook

### Weak or ungrounded answers
1. Verify `OPENAI_API_KEY` is configured.
2. Confirm sources are ingested and selected.
3. Check logs for retrieval/knowledge failures.

### Windows LanceDB `WinError 5` (`_indices/fts`)
1. Restart Streamlit.
2. Move `HALO_DATA_DIR` outside heavily locked sync folders if possible.
3. Confirm Windows vector-search fallback path is active.

### Streaming issues
1. Enable `stream_events` for the relevant chat agent.
2. Turn on `log_stream_events` for deeper diagnostics.
3. Run: `python -m pytest tests/test_streaming.py -q`

### MCP connector issues
1. Verify credentials in `.env` or `.streamlit/secrets.toml`.
2. Test connections via Configuration page.
3. Run: `python -m pytest tests/test_terminal_mcp_smoke.py -q`

### DICOM file handling issues
1. Check `DICOM_ANONYMIZE_ON_UPLOAD` setting if auto-anonymization unexpected.
2. Verify PACS server configuration for connection issues.
3. Ensure DICOM files are not corrupted before upload.

### Agent config validation issues
1. Check `data/agents/*.json` typed fields (`instructions`, `skills`, `tools`, `members`).
2. Run: `python -m pytest tests/test_agents_config.py -q`

---

## Docs and local docs preview

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000`.

CI-equivalent docs validation:

```bash
mkdocs build --strict
```

---

## Repository structure

```text
app/                # Streamlit entrypoints and UI components
├── pages/          # Individual app pages (Configuration, DICOM_Tools, etc.)
services/           # Backend orchestration, retrieval, storage, connectors
├── agents/         # Agent configuration files
└── knowledge.py    # LanceDB integration for RAG
data/               # Local persisted workspace data
├── agents/         # Runtime agent data
├── chat_history/   # Conversation history
└── lancedb/         # Vector database for knowledge retrieval
templates/          # Studio template definitions
├── studio_templates.json  # Template configurations
docs/               # Comprehensive documentation
├── handbook/       # User guides
├── admin/          # Administration guides
└── reference/      # Technical reference
tests/              # Pytest suites
adr/                # Architectural Decision Records
```

---

## Development workflow

1. Review [AGENTS.md](AGENTS.md) before code changes.
2. Keep changes scoped and tested.
3. Update README/docs/ADR/PRD when behavior changes.

### Test

```bash
python -m pytest
```

### Quality gates

- `black --check .`
- `ruff check .`
- `mypy app services` (when enabled)

CI runs linting, tests, and type checks via GitHub Actions.

---

## Useful links

- [Documentation](docs/index.md) — Comprehensive docs site
- [User Handbook](docs/handbook/index.md) — End user guides
- [Admin Guide](docs/admin/index.md) — System administration
- [Technical Reference](docs/reference/index.md) — Developer documentation
- [Changelog](docs/changelog.md) — Version history and changes
- [Product Requirements Document](docs_internal/HALO_CORE_PRD.md)
- [Chat Integration PRD](docs_internal/HALO_CHAT_INTEGRATION_PRD.md)
- [Agent Config Integration Plan](docs_internal/AGENT_CONFIG_INTEGRATION_PLAN.md)
- [Architectural Decisions](adr/)
- [Streamlit App Entry](app/main.py)
- [Agno docs](https://github.com/agno-agi/agno)
- [Streamlit docs](https://docs.streamlit.io)
- [Live Demo](https://halocore.streamlit.app/)
- [Corpus Analytica](https://www.corpusanalytica.com/)

Made with ❤️ by Corpus Analytica
