# HALO Core User Handbook

## HALO Signature Features (Extraordinary)

This section highlights the standout capabilities that make HALO different from a basic chat app.

### 1) HALO concept and identity
- **HALO** = **Holistic Agent Logical Orchestrator**.
- The product is designed as an orchestrated intelligence workspace, not only as a single assistant chat.

### 2) Team-based AI collaboration
- HALO can run with a **team of specialized agents**.
- Each agent can have its own role, instructions, tools, and settings.
- This allows different expert perspectives (for example research-focused, report-focused, or tool-focused behavior).

### 3) Smart delegation strategies
- HALO supports multiple delegation modes such as:
  - `direct_only`
  - `delegate_on_complexity`
  - `always_delegate`
  - `coordinated_rag`
- In practical terms: HALO can decide when to answer directly and when to involve specialist agents.

### 4) "Complexity behind glass" transparency
- Users can inspect what happened during generation via expandable sections like:
  - **Agent Actions**
  - **Tool Calls**
  - **Agent Thinking**
- This gives visibility into reasoning flow and orchestration behavior without exposing raw system internals.

### 5) Memory Management layer tied to chat identity
- HALO supports a memory layer linked to the active `user_id`.
- When memory backend is enabled, user memory can persist across interactions and be managed in the **Account** page.
- This enables more personalized continuity across chat sessions.

### 6) Multimodal understanding in one chat flow
- Users can combine:
  - text prompts
  - image uploads
  - audio input (with transcription)
- This supports richer real-world workflows (for example "analyze this image and include my spoken notes").

### 7) Source-grounded citations with fallback resilience
- HALO is built to answer using selected sources.
- It applies citation-aware response handling and can fall back to alternate generation paths when streaming output is empty.

### 8) Live source-awareness and quick synthesis
- The chat area includes a dynamic **summary of all sources**.
- HALO tracks whether this summary is stale when source inventory changes, so users can refresh at the right moment.

### 9) Studio pipeline from insight to artifact
- HALO turns research context directly into production-style outputs (report, infographic, podcast, presentation, etc.).
- Outputs are persisted, revisitable, and exportable from the same workspace.

---

## 1. Overview

### What this application is
HALO Core is a workspace app for research and content creation. It helps you:
- collect sources (files, web findings, connector results)
- ask questions in a source-grounded AI chat
- generate ready-to-use outputs (for example reports, infographics, podcast scripts, and presentations)
- save important chat results as reusable notes

In short: HALO Core combines a document library, an AI assistant, and a content studio in one interface.

### Who it is for
HALO Core is designed for people who need to turn information into useful outputs quickly, such as:
- analysts and consultants
- medical or scientific researchers
- content teams and editors
- product and strategy teams
- anyone preparing summaries, presentations, or evidence-based answers

### Core problem it solves
Without HALO Core, users often jump between many tools (storage, search, AI chat, notes, export tools). This creates friction and lost context.

HALO Core solves this by keeping the full workflow in one place:
1. add sources
2. chat with context
3. convert answers into structured outputs
4. save/share/export results

### Key benefits
- **Faster research cycles**: fewer app switches
- **More reliable answers**: chat is grounded in selected sources
- **Reusable knowledge**: notes and outputs persist locally
- **Flexible setup**: configurable models, tools, presets, and sidebar layout
- **Practical output formats**: markdown, PDF-like export, and slide-style CSV export

### High-level architecture (non-technical)
At a high level, HALO Core has three visible work areas and several support pages:
- **Sources**: your library and ingestion area
- **Chat**: your AI conversation and source summary area
- **Studio**: output generation and artifact management
- **Sidebar pages**: Configuration, Account, Help, Agent Config, Dashboard

Data is saved in local files by default, so your session can continue later.

---

## 2. Getting Started

### Prerequisites
Before running HALO Core, make sure you have:
- Python 3.10+
- required Python packages from `requirements.txt`
- (recommended) an OpenAI API key for full AI features
- FFmpeg if you plan to transcribe audio/video

### Installation and setup
1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create `.streamlit/secrets.toml` and add keys (for example `OPENAI_API_KEY`).
4. Start the app:
   - `streamlit run app/main.py`

### Account creation/login
There is no mandatory account sign-up in the UI.
- By default, the app uses a local user identity (`local-user`).
- Advanced users can set a custom `user_id` in configuration.

### Basic first-use flow
1. Open HALO Core.
2. Add at least one source in **Sources**.
3. Select your source(s).
4. Ask a question in **Chat**.
5. Save valuable responses as notes.
6. Generate a structured output in **Studio**.

Expected result: you can move from raw files to a publishable draft in one session.

---

## 3. Core Features

## A. Sources Library

### What it does
Lets you import, manage, select, and remove sources used by chat and studio generation.

### Why it matters
Source selection controls what the AI can use for grounded responses.

### How to use it
1. In **Sources**, click **+ Quellen hinzufügen**.
2. Upload one or more files (PDF, DOCX, TXT, MD, CSV, XLSX, PPTX, images, audio, video).
3. Optionally run web search suggestions and import results.
4. Mark sources via checkboxes (or use “select all”).
5. Use per-source menu actions to rename, download, or delete.

### Expected results
- Imported items appear in the source list with type and timestamp.
- Selected sources are used by chat/studio.
- Deleted items are removed from local project state.

---

## B. Connector-Based Source Collection

### What it does
Allows fetching source suggestions from connected systems (for example Drive/Notion connectors in current build).

### Why it matters
Helps collect source candidates faster than manual uploads.

### How to use it
1. In Sources, choose one or more connectors.
2. Click **Quellen abrufen**.
3. Review listed results.
4. Click **Importieren** for the items you want.

### Expected results
Imported connector items appear in your source list and can be selected for chat/studio.

> Assumption: Connector behavior is partly MVP/mock-backed in this repository version. Treat it as a guided ingestion layer that can be extended in production.

---

## C. Chat with Source Grounding

### What it does
Lets you ask text questions, attach images, and capture audio-to-text prompts. Answers are generated using selected sources.

### Why it matters
Improves trustworthiness by grounding responses in your source set.

### How to use it
1. Select sources in **Sources** panel.
2. In **Chat**, enter a prompt (optional: add image/audio input).
3. Send your prompt.
4. Review answer, tool calls, and optional agent trace sections.
5. Save useful responses as notes.

### Expected results
- You receive a response with source-aware behavior.
- If multiple sources are selected, responses can include a source section.
- Agent actions/tool call details can appear in expandable sections.

---

## D. “Summary of All Sources” in Chat

### What it does
Creates and stores a unified summary of all sources in the library.

### Why it matters
Gives fast orientation before deep questioning.

### How to use it
1. In the chat panel, open **Zusammenfassung aller Quellen**.
2. Click refresh icon to generate/update summary.
3. Optionally pin the summary to notes.

### Expected results
- Summary content is displayed.
- Stale indicator appears when source set changed.
- You can save summary as a note for later reuse.

---

## E. Studio Templates (Content Generation)

### What it does
Generates structured deliverables from your current context via template cards.

Current template set includes:
- Bericht (Report)
- Infografik
- Podcast
- Videoübersicht
- Präsentation
- Datentabelle

### Why it matters
Transforms chat/research context into actionable artifacts quickly.

### How to use it
1. Open **Studio**.
2. Pick a template card.
3. (Optional) open card menu to set language, tone, and extra prompt.
4. Click template generate button.
5. Review saved output in **Studio-Ergebnisse**.

### Expected results
- A new output artifact appears in Studio results.
- Output includes generation timestamp and linked source context.
- You can expand, review, and export/delete outputs.

---

## F. Notes Management

### What it does
Stores reusable notes captured from chat, summaries, or manual entry.

### Why it matters
Preserves key findings and allows reusing them as sources.

### How to use it
1. Save a chat response or source summary as note.
2. In notes section, expand a note to read content and source info.
3. Use menu actions to rename, download, delete, or convert note into a source.
4. Add manual notes with **Notiz hinzufügen**.

### Expected results
- Notes persist across sessions.
- Converted notes appear as selectable sources.

---

## G. Configuration Hub

### What it does
Central place for app setup, split into tabs:
- **App** (design/menu/theme/sidebar behavior)
- **Sources** (connectors, image model)
- **Chat** (logging, presets, model/tools/team)
- **Studio** (template settings)
- **Advanced** (agent-level controls)

### Why it matters
Lets you tailor workflow and appearance to your team’s needs.

### How to use it
1. Open **Configuration** from sidebar.
2. Navigate to relevant tab.
3. Change values.
4. Save in-section settings.

### Expected results
Updated configuration persists and affects runtime behavior.

---

## H. Account Memory Management

### What it does
Displays and manages user memory entries when memory DB backend is enabled.

### Why it matters
Lets users clean up or reset saved memory traces.

### How to use it
1. Open **Account** page.
2. If enabled, review memory rows.
3. Select entries and delete selected, or clear all.

### Expected results
- Selected memory entries are removed.
- If backend is disabled, page informs you clearly.

---

## I. Agent Configuration (Power Feature)

### What it does
Provides deep control of per-agent settings, including tools, MCP servers, role instructions, and coordination mode.

### Why it matters
Enables advanced workflow specialization by role/use case.

### How to use it
1. Open **Configuration** → **Open Agent Config**.
2. Select an agent.
3. Edit fields (name, role, instructions, tool list, runtime settings).
4. Save configuration.

### Expected results
Selected agent behavior updates for subsequent runs.

---

## 4. Workflows / Common Tasks

### Workflow 1: Ask grounded questions on uploaded documents
1. Upload PDFs/DOCX files in Sources.
2. Select them with checkboxes.
3. Ask a focused question in Chat.
4. Save the best answer as note.

Result: you get a traceable answer tied to selected material.

### Workflow 2: Build a report draft from collected evidence
1. Import sources (uploads + connectors).
2. Generate/update all-sources summary.
3. Open Studio and choose **Bericht**.
4. Set language/tone and add optional prompt.
5. Generate and export.

Result: report-style draft you can refine externally.

### Workflow 3: Convert insights into presentation-ready structure
1. Prepare source set and chat findings.
2. Save key findings as notes.
3. Use **Präsentation** template.
4. Export output as needed.

Result: rapid first draft of slide flow.

### Workflow 4: Manage long-running project memory
1. Use Account page to review memory items.
2. Delete outdated entries.
3. Keep only useful context.

Result: cleaner assistant behavior and reduced noise.

---

## 5. Interface Explanation

### Main layout
The default Home view has three columns:
1. **Sources** (left)
2. **Chat** (center)
3. **Studio** (right)

### Sidebar
The sidebar is fully configurable and can include:
- navigation links
- separators/spacers
- theme toggle
- branding logo/icon

Default destinations include Home, Dashboard, Configuration, Account, Help.

### Key controls you will use often
- **+ Quellen hinzufügen**: import sources
- **Quellen abrufen**: fetch connector data
- **Chat input**: question/audio/image submission
- **In Notiz speichern**: keep chat output
- **Template Generate button**: create studio artifact
- **Download buttons**: export source/note/output content
- **Configuration save buttons**: persist setting changes

### Important page summaries
- **Dashboard**: placeholder status page in current build
- **Configuration**: operational control center
- **Account**: memory management
- **Help**: support pointers
- **Agent Config**: advanced AI behavior setup

---

## 6. Advanced Usage

### A. Theme and navigation customization
In Configuration → App, you can customize:
- colors (background/text/hover/separator)
- icon and font sizes
- collapsed/expanded sidebar widths
- menu entry order and item types (link/spacer/separator/theme toggle)
- branding assets (light/dark logo and icon)

### B. Chat presets
In Configuration → Chat:
- select preset
- apply model/tools/member bundle in one step

This is useful for switching between workflows (for example quick response vs deeper multi-agent mode).

### C. Tool and coordination tuning
In Agent Config you can tune:
- enabled tools per agent
- MCP server list and enabled state
- coordination mode (`direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`)
- stream-events behavior

### D. Storage and runtime environment
By environment settings, advanced users can change:
- data directory location (`HALO_DATA_DIR`)
- optional memory DB backend (`HALO_AGENT_DB`)

---

## 7. Troubleshooting

## Problem: “I get weak or generic answers”
Possible causes:
- no sources selected
- source summary outdated
- missing API key

Try this:
1. Confirm selected sources in Sources panel.
2. Refresh all-sources summary.
3. Verify `OPENAI_API_KEY` is configured.

---

## Problem: “My uploaded file fails to import”
Possible causes:
- unsupported extension
- parsing/transcription dependency missing

Try this:
1. Check supported file type list.
2. For audio/video, ensure required dependencies (for example FFmpeg stack).
3. Retry with a smaller or simpler file.

---

## Problem: “Account page says memory backend disabled”
Cause:
- optional memory DB is not configured.

Try this:
1. Set `HALO_AGENT_DB` in environment.
2. Restart app.

---

## Problem: “Preset list is empty”
Cause:
- `presets.json` missing or invalid.

Try this:
1. Add a valid `presets.json` in project root.
2. Reopen Configuration → Chat.

---

## Problem: “Share action does nothing”
Cause:
- share controls are placeholder UX in this build.

Try this instead:
- use download/export and external sharing channels.

---

## Problem: “No studio outputs generated”
Possible causes:
- no relevant selected source context
- model/tool configuration issue

Try this:
1. Confirm source selection.
2. Test with Bericht template first.
3. Check chat and agent configuration.

---

## 8. FAQ

### Q1: Do I need an account to use HALO Core?
No mandatory signup is required in the default local setup.

### Q2: Where is my data stored?
By default in local JSON files under the `data/` directory.

### Q3: Can I use only one source?
Yes. You can select one or many sources per task.

### Q4: Can I change the AI model?
Yes. Use Configuration (Chat tab) or Agent Config.

### Q5: Can I control which tools an agent uses?
Yes. Use Agent Config tool selection and settings.

### Q6: Can I export generated outputs?
Yes. Outputs and notes can be downloaded.

### Q7: Is every connector production-ready?
Not necessarily in this repository snapshot. Some connector flows are MVP/mock-oriented.

### Q8: Can I use images and audio in chat?
Yes. Chat input supports images and audio capture/import.

### Q9: What if chat streaming fails?
The runtime has fallback behavior to still generate responses when possible.

### Q10: How do I reset menu/sidebar customization?
Use Configuration → App and reset sidebar menu settings.

---

## 9. Glossary

- **Source**: Any imported content item used as knowledge input.
- **Grounded answer**: Response tied to selected sources rather than pure free-form output.
- **Connector**: Integration path to external systems for source discovery.
- **Template**: Predefined studio output type (report, infographic, etc.).
- **Studio output**: Generated artifact saved in Studio-Ergebnisse.
- **Note**: Saved text snippet from chat/summary/manual input.
- **Preset**: Saved chat setup bundle (model/tools/members).
- **Agent**: AI role with its own instructions and tools.
- **Coordination mode**: Rule for how master and team agents collaborate.
- **MCP server**: External capability endpoint used by agents for additional tool access.
- **Stream events**: Real-time internal events shown during response generation.
- **Memory backend**: Optional database layer for persistent user/agent memory.

---

## Assumptions and Scope Notes
- This handbook reflects the behavior of the repository state analyzed in `halo_core` at the provided path.
- Some UI labels are in German; this handbook keeps English structure with practical terminology.
- Connector and sharing flows include MVP/placeholder behavior in this version.
- This guide focuses on end users and operators, not internal developers.
