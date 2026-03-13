# HALO Core UI Panels and Pages

## 1) UI architecture at a glance

The app uses Streamlit with:

- one primary 3-panel app (`app/main.py`)
- auxiliary multipage entries under `app/pages/`
- session-state driven interaction model

Primary layout in `run_app()`:

- left: Sources panel
- center: Chat panel
- right: Studio panel

## 2) Sidebar navigation and controls

`render_sidebar()` exposes:

- New Notebook button (placeholder behavior)
- page navigation buttons:
  - Dashboard (`pages/Dashboard.py`)
  - Configuration (`pages/Configuration.py`)
  - Account (`pages/Account.py`)
  - Help (`pages/Help.py`)
- support caption

If multipage routing is unavailable, error messaging is shown in sidebar.

## 3) Session-state model used by UI

Core session keys initialized in `_init_state()` include:

- `session_id`
- `sources`
- `chat_history`
- `persistent_tool_calls`
- `studio_templates`
- `studio_outputs`
- `notes`
- `config`
- `agent_configs`

Additional panel-specific keys are created lazily (e.g., template settings and confirmation dialog flags).

## 4) Sources panel (`render_sources_panel`)

Responsibilities:

- source creation from file upload
- source creation from web-search suggestions
- source creation from connector fetch results
- source selection toggles (used to scope chat/studio context)
- source rename/delete/bulk-delete operations
- source-to-retrieval indexing via ingestion path

UX patterns used:

- modal dialogs (`st.dialog`) for add/rename/delete flows
- popover action menus for per-source operations
- toasts for operation feedback
- status captions and empty-state guidance

Important behavior:

- source list is persisted in JSON
- source deletion attempts to remove indexed retrieval chunks by `source_id` and fallback by `title`
- selection state is mirrored into checkbox-style state keys (`src_<id>`)

## 5) Chat panel (`render_chat_panel`)

Core display behavior:

- renders all chat history entries by role
- assistant messages can show:
  - Agent Actions trace expander
  - Tool Calls expander
  - Agent Thinking expander (if present in content)
  - images

Input behavior:

- uses `st.chat_input` with:
  - text
  - image file upload (`jpg/jpeg/png`)
  - audio capture

When submitted:

1. normalizes prompt text
2. stores uploaded images to `uploads/`
3. transcribes audio via ingestion parser path
4. appends user message to persisted history
5. stores pending prompt/images in session state
6. invokes chat runtime in next rerun

Streaming behavior in UI:

- uses callbacks from `ChatTurnInput`:
  - `on_response` to progressively render markdown
  - `on_tools` to update tool call display
- final assistant message is persisted after runtime returns

Additional feature:

- "all sources summary" expander with refresh and "save as note" actions

## 6) Studio panel (`render_studio_panel`)

High-level sections:

1. template cards (generate + configure)
2. studio outputs list
3. chat notes section

Template card behavior:

- values are stored per-template in session state:
  - language
  - tone
  - instructions
  - user prompt
- generation path calls pipelines and inserts output at top of list
- output metadata includes output id, template id, generated timestamp, sources, and optional image path

Outputs section behavior:

- grouped/ordered by templates when possible
- per-output actions include:
  - rename
  - download markdown
  - promote to source
  - share placeholder
  - delete with confirmation

Notes section behavior:

- notes rendered as expandable blocks
- per-note actions include:
  - rename
  - download
  - promote to source
  - share placeholder
  - delete with confirmation
- includes "add note" dialog

## 7) Configuration surfaces

## 7.1 Sidebar configuration panel (`_render_configuration_panel`)
Includes controls for:

- enabled connectors
- image model selection
- logging toggles
- preset selection and apply action
- chat model/team/tools
- per-agent editor (name/role/description/instructions/tools/enabled/members)

## 7.2 Dedicated Configuration page (`pages/Configuration.py`)
- renders `_render_configuration_panel()` in page context
- includes button to navigate to Agent Config page

## 7.3 Agent Config page (`pages/Agent_Config.py`)
- standalone editor for per-agent configs loaded from service layer
- supports key fields:
  - instructions
  - skills
  - tools
  - mcp calls
  - model override
  - memory scope
  - coordination mode
  - stream events
  - enabled toggle

## 8) Auxiliary pages

Current non-core pages are lightweight placeholders:

- `pages/Dashboard.py`
- `pages/Account.py`
- `pages/Help.py`

They establish navigation structure but do not yet contain deep business logic.

## 9) Visual design and CSS model

The app relies on inline CSS injected in panel render functions, especially in Studio and notes rendering.

Notable characteristics:

- custom card-like behavior around Streamlit blocks
- compact popover controls
- visual differentiation for template header actions

Because CSS is inline and tightly coupled to Streamlit test ids, future Streamlit version upgrades should be verified carefully for selector compatibility.

## 10) UI coupling notes and maintenance guidance

Current coupling points to watch:

- some business logic still lives in `app/main.py` alongside UI rendering
- dialog flags and session keys are numerous and naming-based
- panel code includes substantial side effects (save, delete, rerun)

Recommended maintenance approach:

1. Keep UI changes local to panel/page functions.
2. Prefer moving new business logic to `services/`.
3. Preserve session key names unless migration is intentional.
4. Add/update tests when changing chat stream or config behavior.

## 11) Accessibility and localization notes

Current UI strings are mixed German/English, with German dominant in interactive labels.

Examples:

- "Quellen", "Konfigurieren", "Löschen", "Teilen", "Als Quelle nutzen"

Localization strategy is currently implicit (hard-coded strings) and could be centralized in a future i18n pass.
