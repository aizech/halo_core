# HALO Core Agent Configuration Integration Plan

## Goals
- Make each agent’s **description/role/instructions** editable via separate config files.
- Expose agent configuration in the **admin configuration UI**.
- Enable **master agent delegation** while keeping actions transparent to the user.
- Keep current HALO Core behavior stable and incrementally adopt config-driven agents.

## Plan (Checklist)
- [ ] **Inventory current agent usage**
  - [ ] Locate where agents are created/registered in HALO Core (`services/agents.py`, pipeline entrypoints, templates).
  - [ ] Identify current admin config storage and schema (session config + `data/config.json`).

- [ ] **Define per-agent config format**
  - [ ] Create `data/agents/<agent_id>.json` with fields: `id`, `name`, `description`, `role`, `instructions`, `tools`, `enabled`, `model` (optional).
  - [ ] Add a lightweight schema/validation helper in `services/agents_config.py`.
  - [ ] Provide defaults for existing agents (generate base JSON from current prompts).

- [ ] **Load agent configs at startup**
  - [ ] Add loader to read all `data/agents/*.json` and merge with defaults.
  - [ ] Cache in `st.session_state["agent_configs"]` and expose helpers to query by id.

- [ ] **Wire configs into agent construction**
  - [ ] Update agent creation in `services/agents.py` to accept `agent_config` (description/role/instructions/tools).
  - [ ] Ensure existing template agents still work if config missing.

- [ ] **Admin configuration UI**
  - [ ] Add a new “Agents” section in the admin configuration sidebar.
  - [ ] Show a list of agents (enable/disable).
  - [ ] Provide per-agent editor for name, description, role, instructions, tools.
  - [ ] Persist changes to `data/agents/<agent_id>.json`.

- [ ] **Master agent delegation (Agno Team)**
  - [ ] Introduce a master agent config entry (tools + delegation rules).
  - [ ] Add optional team/delegate wiring in pipelines using Agno’s `Team`.
  - [ ] Keep fallbacks to single-agent mode if no team members enabled.

- [ ] **Transparency for agent calls**
  - [ ] Capture and display sub-agent/tool calls in Studio or Chat output.
  - [ ] Add UI expanders for: “Agent Actions”, “Tool Calls”, and “Agent Responses”.

- [ ] **Persistence and migration**
  - [ ] If config files don’t exist, generate them from existing templates/agent prompts.
  - [ ] Add a one-time migration function in `services/storage.py` or `services/agents_config.py`.

- [ ] **Tests & validation**
  - [ ] Add unit tests for config load/save and schema validation.
  - [ ] Add smoke test to ensure agent still runs with missing config.

## Notes / Open Questions
- Should admin editing of agent tools allow only a curated list or free-form IDs?
- Should agent config changes apply immediately or require a restart?
- Do we want per-agent model overrides in phase 1 or later?
