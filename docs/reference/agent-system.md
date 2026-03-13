# HALO Core Agent System and Configuration

## 1) Overview

HALO Core uses Agno agents and teams with a configuration-first approach:

- Per-agent JSON config files under `HALO_DATA_DIR/agents/`
- A master chat agent/team config (`chat`)
- Deterministic routing modes for delegation
- Preset overlays to quickly switch model/tools/members at runtime

The UI edits configs, but core behavior is implemented in `services/`.

## 2) Agent configuration schema

The canonical schema lives in `services/agents_config.py` (`AgentConfig` model).

Supported fields:

- identity and metadata:
  - `id`, `name`, `description`, `role`
- behavior:
  - `instructions`
  - `skills`
  - `tools`
  - `mcp_calls`
- runtime:
  - `model`
  - `coordination_mode`
  - `stream_events`
  - `memory_scope`
  - `enabled`
  - `members`
  - `tool_settings`

Validation behavior:

- `instructions` accepts `str` or `list[str]`, normalized to a single string
- list fields (`skills`, `tools`, `mcp_calls`, `members`) must contain only strings
- invalid payloads fail with descriptive, per-field error messages

## 3) Config file location and bootstrap

Agent configs are stored in:

- `Path(HALO_DATA_DIR) / "agents"`

Bootstrap/migration behavior:

1. On first load, `migrate_agent_configs()` ensures default configs exist.
2. A marker file `.migrated_v1` prevents repeated bootstrap.
3. Defaults are generated from:
   - built-in chat and pubmed defaults
   - studio template definitions from `templates/studio_templates.json`

## 4) Effective config precedence

When loading agent configs:

1. defaults are generated in memory (`_default_configs()`)
2. on-disk JSON payload is loaded
3. default + on-disk are merged (`defaults` then `payload`)
4. merged config is revalidated and persisted if normalization changed values

When applying a preset to chat:

- selected preset updates fields in `chat` config and writes back to `HALO_DATA_DIR/agents/chat.json`

## 5) Agent instruction composition

`build_agent_instructions(config)` composes final instructions from:

- `role`
- `description`
- normalized `instructions`
- optional tool-use notice when tools are configured

For Wikipedia-enabled agents, instruction text adds an explicit requirement to include clickable Wikipedia links.

## 6) Model and tool factory layer

`services/agent_factory.py` centralizes:

### 6.1 Model provider resolution

`normalize_model_id()`
- normalizes plain IDs to `openai:<id>` unless provider already specified

`build_model()` supports:
- OpenAI (`openai:<model>`)
- optional providers when installed:
  - Google Gemini
  - Anthropic Claude
  - Groq

If provider dependencies or keys are missing, model creation returns `None` with warning logs.

### 6.2 Tool registry

`build_tools()` currently supports:

- `pubmed` (optionally with `tool_settings.pubmed`)
- `wikipedia`
- `mermaid` (if optional dependency is available)

This keeps tool construction consistent across single-agent and team paths.

## 7) Team assembly and coordination

`services/halo_team.py::build_master_team_from_config()` constructs the master chat team.

### 7.1 Member loading

- member IDs come from `master_config.members`
- member configs are loaded from `load_agent_configs()`
- disabled members are skipped
- each member is built via `build_agent_from_config()`

### 7.2 Coordination modes

Selection logic is delegated to `services/routing_policy.py::select_member_ids()`.

Supported modes:

- `direct_only`: no member delegation
- `always_delegate`: all configured members
- `delegate_on_complexity`: keyword/skills match against prompt
- `coordinated_rag`: all configured members + additional source-grounding guidance
- empty mode (`""`): behaves like `always_delegate`

### 7.3 Team runtime settings

Team is instantiated with:

- `respond_directly=True`
- `show_members_responses=True`
- `delegate_to_all_members=False`
- `determine_input_for_members=True`

Selected member IDs are attached to the team object (`team.selected_member_ids`) for traceability.

## 8) Single-agent and team fallback behavior

Chat agent creation flow (`services/agents.py::build_chat_agent`):

1. if config indicates members (or id is `chat`), attempt team creation
2. if team build fails, warn and fall back to single-agent build
3. if no config provided, use module-level default `_AGENT`

This preserves continuity even when optional providers/tools are unavailable.

## 9) Streaming and tool-event handling

Streaming is handled in `services/streaming_adapter.py` and invoked by chat runtime.

Key behaviors:

- normalizes event names for robust matching
- deduplicates overlapping team/member content
- treats final completed events as authoritative response
- ignores post-final chunks to prevent response corruption
- captures unique tool calls and exposes them via callback

Chat runtime passes `stream_events` from agent config so preset/config choices directly affect stream event verbosity.

## 10) Chat turn orchestration and telemetry

`services/chat_runtime.py::run_chat_turn()` composes an execution trace containing:

- agent identity/type
- selected team members
- runtime tools
- model label
- stream mode/events/result
- latency (ms)
- knowledge hits and source names
- fallback usage flag

Trace is attached to persisted assistant messages and rendered in UI under "Agent Actions".

## 11) Memory and knowledge integration

Agents and teams may use:

### 11.1 Optional DB-backed memory

From `services/storage.py::get_agent_db()`:

- enabled only when `HALO_AGENT_DB` is configured
- if unavailable or import fails, returns `None` and system remains functional

### 11.2 Optional Agno Knowledge wrapper

From `services/knowledge.py::get_agent_knowledge()`:

- initialized only when OpenAI key is available
- wraps the same LanceDB table used by retrieval
- uses vector search on Windows for stability; hybrid where feasible elsewhere
- if initialization fails, runtime falls back to manual retrieval path

## 12) Presets and runtime overrides

`presets.json` defines named chat presets.

Preset fields currently supported:

- `model`
- `tools`
- `members`
- `stream_events`
- `coordination_mode`

Applying a preset updates and persists `chat` config. This allows runtime behavior changes without code edits.

## 13) UI surfaces for agent management

Two configuration surfaces exist:

1. Sidebar panel in `app/main.py` (`_render_configuration_panel`)
2. Dedicated page `app/pages/Agent_Config.py`

Capabilities include:

- selecting/editing agents
- enabling/disabling agents
- changing instructions/skills/tools/MCP calls
- adjusting model and coordination mode
- toggling stream events

## 14) Adding a new agent (recommended path)

1. Create `HALO_DATA_DIR/agents/<agent_id>.json` with schema-compliant payload.
2. Set `enabled: true`.
3. Optionally add `skills` for routing in `delegate_on_complexity` mode.
4. Add agent ID to chat `members` in config page or preset.
5. If needed, add supported tool ID and tool settings.
6. Validate behavior in chat with relevant coordination mode.

## 15) Common troubleshooting

### Team not delegating as expected

- Verify `coordination_mode` value
- In `delegate_on_complexity`, ensure prompt contains skill tags expected by member configs
- Confirm member agents are enabled

### Model does not run

- confirm provider prefix in model ID (e.g. `openai:gpt-5.2`)
- confirm required API key/dependency is available for that provider

### Tool call events missing

- ensure config/preset sets `stream_events: true`
- inspect "Tool Calls" and "Agent Actions" in chat UI

### Agent memory not persistent

- set `HALO_AGENT_DB` to a valid sqlite path
- check logs for DB initialization warnings

## 16) Governance notes

The current architecture intentionally keeps:

- behavior/config in service modules and JSON
- UI layer thin on orchestration logic
- deterministic, test-covered routing/stream handling

This supports incremental hardening while preserving existing app behavior.
