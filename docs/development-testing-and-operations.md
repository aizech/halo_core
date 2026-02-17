# HALO Core Development, Testing, and Operations

## 1) Prerequisites

Minimum local requirements:

- Python 3.10+
- Git
- FFmpeg (required for audio/video parsing paths)
- API credentials for model/tool providers (at least OpenAI for full functionality)

Repository dependencies are defined in `requirements.txt`.

## 2) Local setup

## 2.1 Environment setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 2.2 Secrets and configuration

Use `.streamlit/secrets.toml` and/or environment variables.

Important settings consumed by `services/settings.py`:

- `OPENAI_API_KEY`
- `HALO_DATA_DIR`
- `HALO_TEMPLATES_DIR`
- `HALO_AGENT_DB`

Do not hardcode secrets in source files.

## 2.3 Running the app

```bash
streamlit run app/main.py
```

## 3) Daily development workflow

Recommended loop:

1. Pull latest changes and inspect current docs/PRDs if feature scope changed.
2. Implement focused changes in relevant module.
3. Run targeted tests for touched services first.
4. Run lint/format checks.
5. Run full test suite before finalizing.

## 4) Testing strategy

The repository uses pytest with module-focused tests under `tests/`.

High-value test areas include:

- `test_chat_runtime.py`: chat orchestration + telemetry + fallback behavior
- `test_streaming.py`: stream event dedup/final-response correctness
- `test_agents_config.py`: schema and config merge logic
- `test_halo_team.py`: team routing/coordination behavior
- `test_chat_state.py`: message/state helper behavior
- `test_chunking.py`, `test_ingestion.py`, `test_knowledge.py`: ingestion/retrieval support paths

Run all tests:

```bash
pytest
```

Run targeted tests:

```bash
pytest tests/test_chat_runtime.py -v
pytest tests/test_streaming.py -v
```

## 5) Linting and formatting

Standard tools in repository workflows:

- `ruff check .`
- `black --check .`
- `mypy app services` (configured in docs, currently commented in CI)

Typical local sequence:

```bash
ruff check .
black --check .
```

If formatting fixes are needed:

```bash
black .
```

## 6) CI/CD workflows

Defined under `.github/workflows/`.

## 6.1 CI (`ci.yml`)

- triggers on push to main and pull requests
- runs on Python 3.11 and 3.13
- installs dependencies and quality tooling
- runs:
  - ruff
  - black check
  - pytest

## 6.2 Docs lint (`docs.yml`)

- triggers on PRs touching markdown files
- runs markdown lint over `**/*.md`

## 6.3 Dependency audit (`audit.yml`)

- scheduled weekly + manual dispatch
- runs `pip-audit -r requirements.txt`

## 6.4 Release build (`release.yml`)

- triggers on version tag pushes (`v*`)
- builds Docker image and emits summary

## 7) Runtime observability and debugging

## 7.1 Logging controls

App configuration supports toggles for:

- agent payload logs
- agent response logs
- agent error logs
- user request logs
- stream event logs

These are configured in UI and persisted in `config.json`.

## 7.2 Chat run traces

Assistant messages can include structured traces with telemetry fields:

- model
- selected members
- tools
- stream outcome
- latency
- knowledge hits/sources
- fallback usage

This enables rapid diagnosis of routing, stream, and grounding behavior.

## 8) Common troubleshooting

### 8.1 App starts but chat responses are poor/placeholder

Likely cause:
- missing OpenAI key

Actions:
1. confirm `OPENAI_API_KEY` exists in secrets/env
2. restart streamlit session
3. verify model id in chat config/preset

### 8.2 Team members not active

Likely causes:
- members disabled in agent config
- coordination mode set to `direct_only`
- prompt did not match `skills` for `delegate_on_complexity`

Actions:
1. open Agent Config page
2. verify member `enabled`, `skills`, `coordination_mode`
3. inspect assistant trace in "Agent Actions"

### 8.3 Tool calls not displayed

Likely causes:
- `stream_events` disabled in agent/preset
- tools not configured for active agent/member

Actions:
1. verify `stream_events: true`
2. verify tool IDs in config
3. enable stream debug logging

### 8.4 Media parsing issues

Likely causes:
- missing FFmpeg or API keys

Actions:
1. verify FFmpeg in PATH
2. verify OpenAI key for transcription/caption paths
3. check parser error output in UI/logs

## 9) Data and environment operations

## 9.1 Data directory control

Use `HALO_DATA_DIR` to separate datasets by environment.

Suggested structure:

- `data-dev/`
- `data-staging/`
- `data-prod/` (if applicable)

## 9.2 Optional agent DB memory

Set `HALO_AGENT_DB` to enable persistent Agno memory backend.

If unset, app runs in JSON-only memory mode without failure.

## 9.3 Backup recommendations

Back up together:

- JSON files in data dir
- `chat_history/`
- `lancedb/`
- `agents/` config folder

## 10) Contribution and quality expectations

Project documentation and standards emphasize:

- focused, minimal diffs
- behavior-preserving refactors unless explicitly changing behavior
- tests updated with behavior changes
- docs updated when architecture/runtime changes

Primary references:

- `AGENTS.md`
- `CONTRIBUTING.md`
- `README.md`

## 11) Suggested change playbooks

### 11.1 Chat/runtime change

1. update service logic (`chat_runtime`, `streaming_adapter`, `agents`, or `halo_team`)
2. add/update focused tests
3. run chat/runtime + streaming tests
4. run full test suite
5. update docs in `docs/` if behavior changed

### 11.2 Ingestion/retrieval change

1. update `parsers`/`ingestion`/`chunking`/`retrieval`
2. add/update ingestion/chunking/retrieval tests
3. verify source add/index/query path manually
4. document any schema/data migration implications

### 11.3 UI panel change

1. keep rendering concerns in `app/`
2. avoid embedding new business logic in panel functions when service abstraction exists
3. validate all panel actions still persist state correctly
4. include screenshots/notes in PR when UX behavior changes

## 12) Release readiness checklist

Before tagging a release candidate:

1. All CI checks passing (lint/format/tests)
2. No known blocking regressions in chat/source/studio flows
3. Docs reflect current runtime behavior
4. Agent config defaults and templates are valid
5. Dependency audit findings reviewed

This checklist should be treated as minimum quality gate for stable delivery.
