# HALO Core – NotebookLM-Style Streamlit App

This repository hosts a Streamlit + Agno implementation of a NotebookLM-style workspace featuring Sources ("Quellen"), Chat, and Studio panels. The accompanying [PRD](docs_internal/HALO_CORE_PRD.md) and [ADR](adr/0001-streamlit-agno-architecture.md) describe the target experience and architectural decisions.

## Prerequisites
- Python 3.10+
- Node/npm optional (only for frontend assets or tooling)
- FFmpeg (for audio/video transcription)
- OpenAI API key and any other MCP/system API credentials (store in `.streamlit/secrets.toml`)

## Getting Started
```bash
python -m venv .venv
. .venv/Scripts/activate        # Windows Powershell: .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with entries like:
```toml
OPENAI_API_KEY = "sk-..."
AGNO_TELEMETRY_URL = ""
```

## Running the App
```bash
streamlit run app/main.py
```
The default layout renders the sidebar (Administration, Configuration, Account, Help) and the three primary panels with Studio templates driven by `/templates/studio_templates.json`. Studio cards use clickable header strips for generation with inline ⋯ menus for configuration and standardized download filenames for exports.

Uploaded sources, studio notes, and chat history are saved as JSON under the `data/` folder. Override the location with `HALO_DATA_DIR` if you want per-environment persistence.
Chat presets (model/tools/team members) are loaded from `presets.json` and can be applied from the sidebar.
Mermaid diagrams are rendered from fenced ` ```mermaid ` blocks; multiline labels are sanitized for browser rendering.

## Runtime configuration knobs

### Coordination modes (`coordination_mode`)
- `direct_only`: master answers directly, no delegation.
- `delegate_on_complexity`: delegates only to members whose `skills` match the prompt.
- `always_delegate`: delegates to all configured members.
- `coordinated_rag`: delegates to all members and adds source-first RAG guidance.

### Knowledge mode
- Agno `Knowledge` is wired to LanceDB (`data/lancedb`) via `services/knowledge.py`.
- `search_knowledge=True` is enabled when knowledge is available.
- Team mode also enables knowledge search for `coordinated_rag`.
- Windows runs use vector search (instead of hybrid/FTS) to avoid index lock failures.

### Streaming options
- Chat uses streaming by default.
- Per-agent `stream_events` controls whether event-rich streaming is requested.
- App config `log_stream_events` controls verbose stream event logging.

### Memory backend options
- Default: JSON-only state/history in `data/` (safe local fallback).
- Optional: set `HALO_AGENT_DB` to enable Agno SQLite-backed memory.
- When DB is enabled, agents/teams use bounded history (`num_history_runs=3`) and user memories.

### Structured trace telemetry
Each chat turn trace includes `telemetry` metadata:
- `model`
- `selected_members`
- `tools`
- `stream_mode`, `stream_events`, `stream_result`
- `latency_ms`
- `knowledge_hits`, `knowledge_sources`
- `used_fallback`

## Operator runbook (troubleshooting)

### 1) "No documents found" or ungrounded answers
1. Ensure `OPENAI_API_KEY` is configured.
2. Confirm sources are ingested and selected in the UI.
3. Check logs for retrieval/knowledge errors.

### 2) Windows LanceDB index error (`WinError 5` under `_indices/fts`)
1. Restart Streamlit (re-initializes knowledge mode).
2. Keep `HALO_DATA_DIR` outside heavily locked sync folders where possible.
3. Verify current code path uses vector search on Windows.

### 3) Streaming output issues
1. Verify `stream_events` is enabled for the chat agent when tool/team visibility is needed.
2. Turn on `log_stream_events` to inspect normalized stream events.
3. Run streaming tests: `python -m pytest tests/test_streaming.py -q`.

### 4) Agent config validation errors
1. Open `data/agents/*.json` and ensure typed fields are valid (`instructions`, `skills`, `tools`, `members`).
2. Re-run: `python -m pytest tests/test_agents_config.py -q`.

## Repository Structure
```
app/                # Streamlit entrypoints and UI components
services/           # Backend service wrappers (MCP, storage, orchestration)
data/               # Local storage (gitignored in production)
templates/          # Studio template definitions (studio_templates.json)
tests/              # Pytest suites
adr/                # Architectural Decision Records
```

## Development Workflow
1. Review `AGENTS.md` for coding conventions, CI expectations, and collaboration norms.
2. Use feature branches (`feature/<issue>-<slug>`), keep commits small, and ensure tests pass locally.
3. Update PRD/ADR/README whenever requirements shift.

## Testing
```bash
python -m pytest
```
Add or update tests alongside code changes. Use fixtures/mocks for external APIs and MCP servers.

## CI/CD
GitHub Actions run linting (`ruff`, `black --check`), tests (`pytest`), and type checks (`mypy`). Releases build Docker images and deploy via environment-protected workflows. See `AGENTS.md` for details.

## Useful Links
- [Documentation Content Overview](docs/CONTENT_OVERVIEW.md)
- [Product Requirements Document](docs_internal/HALO_CORE_PRD.md)
- [Chat Integration PRD](docs_internal/HALO_CHAT_INTEGRATION_PRD.md)
- [Agent Config Integration Plan](docs_internal/AGENT_CONFIG_INTEGRATION_PLAN.md)
- [Architectural Decisions](adr/)
- [Agent Collaboration Guide](AGENTS.md)
- [Streamlit App](app/main.py)
- [Agno documentation](https://github.com/agno-agi/agno)
- [Streamlit documentation](https://docs.streamlit.io)

Made with ❤️ by Corpus Analytica