# HALO Core – NotebookLM-Style Streamlit App

This repository hosts a Streamlit + Agno implementation of a NotebookLM-style workspace featuring Sources ("Quellen"), Chat, and Studio panels. The accompanying [PRD](HALO_CORE_PRD.md) and [ADR](adr/0001-streamlit-agno-architecture.md) describe the target experience and architectural decisions.

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
- [Product Requirements Document](HALO_CORE_PRD.md)
- [Architectural Decisions](adr/)
- [Agent Collaboration Guide](AGENTS.md)
- [Streamlit App](app/main.py)
- [Agno documentation](https://github.com/agno-agi/agno)
- [Streamlit documentation](https://docs.streamlit.io)
