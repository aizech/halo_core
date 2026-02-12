# HALO Core — Multi‑Agent Chat Integration PRD (Concise)

## 1) Goal
Deliver a configurable, multi‑agent chat system in HALO Core that is **modular**, **data‑driven**, and **fully reusable** across UI pages and services. Every agent has its own config (instructions, skills, tools, MCP bindings), and the chat UI remains a thin shell over services.

## 2) Non‑Goals
- Rewriting the existing RAG pipeline.
- Migrating to a DB backend (unless explicitly chosen).
- Building a new frontend framework (stay in Streamlit).

## 3) Success Criteria
- Agents are fully configurable via per‑agent files with schema validation.
- Multi‑agent team coordination works with streaming and tool‑call visibility.
- Chat UI does not contain agent construction logic.
- Presets can switch team members, models, tools without code changes.
- All changes are covered by tests.

## 4) Current State (baseline)
- Chat streaming, tool call rendering, image upload, and JSON persistence already exist. @app/main.py
- Agent configs load/merge via `services/agents_config.py` (data_dir). @services/agents_config.py
- Presets loaded from `presets.json`. @services/presets.py

## 5) Functional Requirements
### FR‑1 Per‑Agent Config Files
**Requirement**: Each agent has its own config file in `HALO_DATA_DIR/agents/<id>.json`.

**Fields (required unless noted)**
- `id`, `name`, `description`, `role`, `instructions`
- `skills` (list[str]) — routing tags
- `tools` (list[str]) — tool IDs
- `mcp_calls` (list[str]) — MCP tool bindings
- `model` (optional), `enabled` (bool), `memory_scope` (optional)

**Implementation steps**
1. Extend `services/agents_config.py` schema validation to include `skills`, `mcp_calls`, `memory_scope`.
2. Add defaults for existing agents if missing.
3. Update merge logic to prefer: defaults → on‑disk agent configs → preset overrides.
4. Add unit tests for validation and merge precedence.

### FR‑2 Team Coordination Policy
**Requirement**: Team coordination must be configurable and deterministic.

**Policies**
- `direct_only`: respond directly, no delegation.
- `delegate_on_complexity`: delegate based on skills/routing.
- `always_delegate`: always dispatch to specific member(s).

**Implementation steps**
1. Add `coordination_mode` to chat config or preset.
2. Implement a routing function in `services/halo_team.py` that selects member(s) based on skills + mode.
3. Persist selected member(s) in trace for auditability.
4. Add tests for routing decisions.

### FR‑3 Streaming + Tool Calls
**Requirement**: Streaming must support content + tool call events without duplicates.

**Implementation steps**
1. Use `stream_events=True` on Team streams when tool events are desired.
2. Ensure team/member duplication handling remains (TeamRunContent vs RunContent).
3. Persist tool calls with serialization and render in UI.
4. Add tests to cover team‑only, member‑only, and mixed events.

### FR‑4 Multi‑page Configuration UI
**Requirement**: Agent configuration lives in a separate Streamlit page.

**Implementation steps**
1. Create `pages/Agent_Config.py` with:
   - Agent list, enable/disable toggle
   - Editable instructions/skills/tools/MCP bindings
   - Save action to `services/agents_config.save_agent_config`
2. Keep chat page minimal; no direct agent creation logic.

### FR‑5 Reusable Module Architecture
**Requirement**: All modules are reusable components and UI is thin.

**Implementation steps**
1. Ensure all logic lives in services:
   - `agents_config.py`, `halo_team.py`, `chat_state.py`, `presets.py`, `storage.py`
2. UI calls only these services.
3. Add docstrings and type hints for reuse.

## 6) Non‑Functional Requirements
- Backwards compatible with existing presets.
- Fast startup with cached configs.
- Clear error surfaces (agent config validation errors show in config page).

## 7) Testing
- Unit tests for agent config validation + merge precedence.
- Team routing tests for each coordination mode.
- Streaming event tests for duplicates + tool calls.
- UI smoke test: agent config page loads without modifying chat state.

## 8) Deliverables
- Updated `services/agents_config.py`
- New/updated `services/halo_team.py`, `services/chat_state.py`
- New `pages/Agent_Config.py`
- Updated tests in `tests/`
- Updated `presets.json` schema (coordination_mode)

## 9) Rollout Plan
1. Phase 1: Per‑agent configs + validation + tests.
2. Phase 2: Team coordination policy.
3. Phase 3: Stream events + tool call rendering.
4. Phase 4: Agent Config page.

## 10) Open Questions
- Should `mcp_calls` be free‑form or limited to a curated list?
- Default `coordination_mode`?
- Should `stream_events=True` be always on or preset‑controlled?
