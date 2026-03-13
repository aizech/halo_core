# Glossary

Definitions of terms used throughout HALO Core documentation.

---

## A

### Agent

An AI role with its own instructions, tools, and settings. Agents can work independently or as part of a team.

### Agent Config

The configuration page for advanced agent-level settings including tools, MCP servers, and coordination mode.

---

## C

### Chat History

Stored conversation records, persisted in `data/chat_history/`.

### Connector

An integration path to external systems for source discovery. Examples include Drive and Notion connectors.

### Coordination Mode

A rule for how master and team agents collaborate. Options: `direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`.

---

## D

### Data Directory

The folder where HALO stores all persistent data. Default: `data/`. Configurable via `HALO_DATA_DIR`.

---

## F

### Fallback

Alternative generation path when primary streaming fails. HALO has built-in fallback behavior.

---

## G

### Grounded Answer

A response tied to selected sources rather than pure free-form output. Grounded answers cite actual source content.

---

## H

### HALO

**Holistic Agent Logical Orchestrator** — the full name of the HALO Core system.

---

## K

### Knowledge

The indexed content from sources, stored in LanceDB for retrieval. Enables RAG (Retrieval-Augmented Generation).

---

## L

### LanceDB

A vector database used by HALO for knowledge storage and similarity search.

---

## M

### Master Agent

The primary agent that receives user queries and optionally delegates to team members.

### MCP Server

Model Context Protocol server — an external capability endpoint that provides additional tools to agents.

### Memory Backend

An optional database layer for persistent user/agent memory. Enabled via `HALO_AGENT_DB`.

### Multimodal

Input that combines multiple types: text, images, and audio.

---

## N

### Note

A saved text snippet from chat, summary, or manual input. Notes can be converted to sources.

---

## P

### Preset

A saved chat setup bundle containing model, tools, and team member configuration.

---

## R

### RAG

Retrieval-Augmented Generation — using retrieved knowledge to ground AI responses in source content.

---

## S

### Session

A single continuous interaction with HALO. Sessions maintain context and history.

### Source

Any imported content item used as knowledge input for chat and studio.

### Source Summary

A generated overview of all sources in the library, available in the Chat panel.

### Stream Events

Real-time internal events shown during response generation. Controlled by `stream_events` setting.

### Studio

The panel for template-driven output generation (reports, presentations, etc.).

### Studio Output

A generated artifact saved in Studio-Ergebnisse.

---

## T

### Team Agent

A specialized agent that works alongside the master agent. Team members have specific roles and skills.

### Template

A predefined studio output type (report, infographic, podcast, presentation, data table).

### Tool

A capability available to agents, such as web search, calculator, or file operations.

### Trace

Structured information about agent actions, tool calls, and reasoning during generation.

---

## V

### Vector Search

Similarity-based search using vector embeddings. Used for knowledge retrieval.

---

## W

### Workflow

A structured sequence of steps to accomplish a specific task in HALO.

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API authentication |
| `HALO_DATA_DIR` | Custom data directory path |
| `HALO_TEMPLATES_DIR` | Custom templates directory |
| `HALO_AGENT_DB` | Memory backend database path |

---

## File Types

| Extension | Category |
|-----------|----------|
| `.pdf`, `.docx`, `.txt`, `.md` | Documents |
| `.csv`, `.xlsx`, `.xls` | Spreadsheets |
| `.pptx` | Presentations |
| `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | Images |
| `.mp3`, `.wav`, `.m4a`, `.ogg` | Audio |
| `.mp4`, `.mov`, `.avi`, `.mkv` | Video |

---

## Configuration Files

| File | Content |
|------|---------|
| `config.json` | App settings |
| `presets.json` | Chat presets |
| `data/agents/*.json` | Agent configurations |
| `templates/studio_templates.json` | Studio templates |
| `.streamlit/secrets.toml` | API keys and secrets |
