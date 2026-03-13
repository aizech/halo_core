# HALO Core Repository Overview

## 1) Purpose

HALO Core is a Streamlit-based, NotebookLM-style workspace that combines:

- Source management ("Quellen")
- Grounded chat over selected sources
- Studio-style artifact generation (reports, infographic, podcast, presentation, table, etc.)

The app uses Agno for agent and team orchestration, with a service-oriented Python backend under `services/` and Streamlit UI in `app/`.

## 2) Current implementation status

The repository contains a functional MVP with active refactoring toward more modular runtime services.

Implemented capabilities include:

- Source upload and parsing for text, office docs, images, audio, and video
- LanceDB-backed retrieval and indexing
- Streaming chat with tool-call visibility and fallback behavior
- Agent/team configuration persisted in per-agent JSON files
- Preset-driven chat model/tools/member switching
- Studio template generation and artifact persistence

Planned and roadmap work is tracked in:

- `AGNO_ADOPTION_BACKLOG.md`
- `docs_internal/HALO_CORE_PRD.md`
- `docs_internal/HALO_CHAT_INTEGRATION_PRD.md`

## 3) High-level structure

```text
app/                    Streamlit app and pages
services/               Core business logic and orchestration
templates/              Studio template registry (JSON)
data/                   Local runtime storage (JSON, LanceDB, generated assets)
tests/                  Pytest suite
docs/                   Maintainer-facing implementation docs (this folder)
docs_internal/          PRDs and integration plans
adr/                    Architecture decision records
.github/workflows/      CI, docs lint, release, dependency audit
```

## 4) Key runtime entry points

### Primary app entrypoint
- `streamlit run app/main.py`
- Main function: `run_app()` in `app/main.py`

### Major service entrypoints
- Chat orchestration: `services/chat_runtime.py::run_chat_turn`
- Agent abstraction: `services/agents.py`
- Team building: `services/halo_team.py`
- Streaming normalization: `services/streaming_adapter.py::stream_agent_response`
- Storage and persistence: `services/storage.py`
- Source ingestion: `services/ingestion.py`
- Retrieval and indexing: `services/retrieval.py`

## 5) Technology stack

### Application and orchestration
- Streamlit
- Agno
- OpenAI SDK

### Data and parsing
- LanceDB + pyarrow + numpy
- pypdf, python-docx, openpyxl, python-pptx
- moviepy (video to audio extraction)

### Validation and config
- Pydantic + pydantic-settings
- dotenv support via dependencies

### Quality and CI
- pytest
- ruff
- black
- mypy (present but currently commented in CI workflow)

## 6) Configuration model

Configuration is split between:

1. Environment/settings (`services/settings.py`)
   - `OPENAI_API_KEY`
   - `HALO_DATA_DIR`
   - `HALO_TEMPLATES_DIR`
   - `HALO_AGENT_DB`

2. Runtime UI configuration (`data/config.json`)
   - connector enablement
   - logging toggles
   - image model
   - selected preset

3. Agent configuration (`HALO_DATA_DIR/agents/*.json`)
   - per-agent role/instructions/tools/model/members/coordination controls

4. Studio template registry (`templates/studio_templates.json`)
   - data-driven template definitions

5. Presets (`presets.json`)
   - quick updates for chat model/tools/members/stream/coordinator behavior

## 7) Data persistence model

The app primarily uses local JSON and local LanceDB:

- Sources: `data/sources.json`
- Chat history: `data/chat_history/<session_id>.json`
- Studio notes: `data/studio_notes.json`
- Studio outputs: `data/studio_outputs.json`
- Connector cache: `data/connector_cache.json`
- Retrieval index: `data/lancedb/`

Optional Agno SQLite memory backend is enabled via `HALO_AGENT_DB`.

## 8) UI composition model

The default app view is a 3-column layout:

1. Sources panel
2. Chat panel
3. Studio panel

Sidebar includes navigation to multipage entries:

- Dashboard
- Configuration
- Account
- Help
- Agent Config page (reachable from Configuration page)

## 9) Test coverage map

The `tests/` suite covers:

- Agent config validation/merging
- Team routing and coordination behavior
- Chat runtime orchestration and telemetry
- Streaming event handling and deduplication
- Chunking, ingestion, knowledge, presets, chat state

This supports a safe refactoring path from monolithic UI logic to service-level modules.

## 10) CI/CD overview

GitHub workflows include:

- `ci.yml`: lint + format + tests (Python 3.11 and 3.13)
- `docs.yml`: markdown lint on PR markdown changes
- `audit.yml`: scheduled dependency audit via `pip-audit`
- `release.yml`: Docker build on version tags

## 11) Internal reference documents

- Product requirements: `docs_internal/HALO_CORE_PRD.md`
- Chat integration PRD: `docs_internal/HALO_CHAT_INTEGRATION_PRD.md`
- Agent config integration plan: `docs_internal/AGENT_CONFIG_INTEGRATION_PLAN.md`
- Architecture decision: `adr/0001-streamlit-agno-architecture.md`
- Collaboration/coding rules: `AGENTS.md`

## 12) Where to start (by role)

### New maintainer
1. `README.md`
2. `docs/ARCHITECTURE_AND_RUNTIME.md`
3. `docs/DEVELOPMENT_TESTING_AND_OPERATIONS.md`

### Chat/agent contributor
1. `docs/AGENT_SYSTEM.md`
2. `services/chat_runtime.py`
3. `services/streaming_adapter.py`

### Ingestion/RAG contributor
1. `docs/DATA_STORAGE_AND_RETRIEVAL.md`
2. `services/ingestion.py`
3. `services/retrieval.py`

### UI contributor
1. `docs/UI_PANELS_AND_PAGES.md`
2. `app/main.py`
3. `app/pages/*.py`
