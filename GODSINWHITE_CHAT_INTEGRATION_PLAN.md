# Integration & Adoption Plan: godsinwhite → halo_core chat (updated)

## 1) Current implementation state (halo_core)
Based on the current codebase:

- **Chat UI & flow**: `render_chat_panel()` renders chat history, tool calls, images, and streaming output. Streaming runs in `_stream_agent_response()` with de-dup handling, mermaid rendering, and fallback when streaming returns empty. @app/main.py#1728-1890
- **Session persistence**: Chat history persisted to JSON in `data/chat_history/<session_id>.json` using `storage.load_chat_history/save_chat_history`. Session id is stored in `st.session_state` during initialization. @services/storage.py#18-103
- **Tool call persistence + rendering**: Tool calls are serialized and stored in `persistent_tool_calls`; rendered with `_display_tool_calls`. @app/main.py#958-1009
- **Multimodal**: `st.chat_input(accept_file=True, accept_audio=True)` handles images; uploads saved under `uploads/` and rendered in chat. @app/main.py#1830-1906
- **Presets**: `presets.json` + `services/presets.py` to apply model/tools/members in sidebar. @services/presets.py#1-64
- **Agent config storage**: Stored under `HALO_DATA_DIR/agents` to align with tests and runtime. @services/agents_config.py#20-43

## 2) Agno docs check (team coordination & streaming)
Key references from Agno docs:

- Team streaming: `Team.run(..., stream=True)`; optional `stream_events=True` to receive tool/trace events.  
  Docs: https://docs.agno.com/teams/running-teams
- Agent streaming: `agent.run(..., stream=True, stream_events=True)` yields tool events and reasoning steps.  
  Docs: https://docs.agno.com/agents/running-agents

Implication: if we require tool-call events from the team stream, we should pass `stream_events=True` (Agno default streams content only).

## 3) Gap analysis vs original godsinwhite plan
**Completed / implemented in halo_core:**
- Streaming responses with de-dup (team/member, cumulative content)
- Tool call serialization + UI
- Image upload + rendering
- Presets (model/tools/members) + sidebar integration
- Chat history persistence in JSON

**Still open / needs explicit coordination plan:**
- Multi-agent **team coordination strategy** (how to route tasks, when to show member responses, what to stream)
- Optional DB-backed session persistence (if required beyond JSON)
- Agno `stream_events=True` handling if detailed tool events are desired

## 4) Concise multi-agent coordination plan (no implementation yet)
Goal: introduce a *coordinated team* in chat that is explicit, controllable, and observable.

### 4.1 Coordination policy
- **Master team** remains the single chat interface.
- **Delegation rules** are explicit in config:
  - When prompt is simple (greeting, small talk) → respond directly, no delegation.
  - When prompt is domain-heavy → delegate to specific member(s) (e.g., `reports`, `infographic`).
- **Member selection** uses a lightweight routing rubric in config (keywords or task types) to avoid model overreach.

### 4.2 Streaming & observability
- Use `stream_events=True` to receive tool and reasoning events *if* we want to show tool calls and per-member activity live.
- Render **member events** in a collapsed expander (“Team activity”) to avoid clutter.
- Continue to render **final response** as the master team output, not the member logs.

### 4.3 UI integration plan
- Keep the existing chat UI.
- Add a **Team activity panel** (collapsed by default) showing:
  - Member selected
  - Tool calls
  - Intermediate notes (optional)

### 4.4 Configuration surface
- Use `presets.json` to define:
  - Default team members
  - Models and tools per preset
  - “Coordination mode”: `direct_only`, `delegate_on_complexity`, `always_delegate`

### 4.4b Per-agent configuration (separate coding per agent)
- Each agent lives in its own config file (JSON/YAML), with:
  - `id`, `name`, `description`, `role`, `instructions`
  - `skills` (free-form tags) for routing
  - `tools` (tool IDs) and `mcp_calls` (MCP tool bindings)
  - `model` override, `enabled`, `memory_scope`
- Loader merges defaults → local overrides → preset overrides.
- Expose agent configs in the admin UI for edit/enable/disable.

### 4.4c Reusable module architecture
- Split chat orchestration into reusable services:
  - `services/agents_config.py` (load/save/validate agent configs)
  - `services/halo_team.py` (Team builder + coordination policy)
  - `services/chat_state.py` (message normalization + persistence)
  - `services/presets.py` (preset load/apply)
  - `services/storage.py` (persistence backend)
- UI layer only calls these services; no agent logic in the UI.

### 4.4d Configuration UI as a separate Streamlit page
- Use Streamlit multi-page app structure to host an **Agent Config** page.
- The page reads/writes per-agent configs and presets without touching chat UI state.
- Keeps chat view minimal while allowing full configuration workflows.

### 4.5 Safety & fallback
- If team build fails, fall back to single-agent streaming.
- If `stream_events` is unavailable, fall back to content-only streaming and render tool calls from the final response (if present).

## 5) Next steps (decision checkpoints)
1. Confirm whether **stream_events=True** should be enabled for the team stream. (Impacts UI complexity)
2. Confirm coordination mode defaults and which members are always available.
3. Confirm whether JSON persistence is sufficient or DB-backed sessions are required.

---

If you want this plan updated to a specific file name or location, tell me and I’ll adjust.
