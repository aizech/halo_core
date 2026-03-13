# Agents and Teams

HALO Core includes pre-configured AI agents and teams for different use cases.

---

## What Are Agents?

Agents are AI roles with specific:

- **Instructions** — How to respond
- **Tools** — Capabilities like web search, PubMed, calculator
- **Skills** — Tags for delegation matching
- **Model** — AI model selection

---

## What Are Teams?

Teams coordinate multiple agents:

- **Master agent** — Receives user queries
- **Members** — Specialized agents for delegation
- **Coordination mode** — Rules for delegation

---

## Available Agents

### General Purpose

| Agent | Role | Tools | Model |
|-------|------|-------|-------|
| **General Assistant** | Everyday tasks, quick answers | DuckDuckGo, Calculator | gpt-4.1-mini |
| **Chat Agent** | Fallback for simple conversations | — | gpt-4.1-mini |
| **Note Taker** | Summarize and organize information | — | gpt-4.1-mini |
| **Summarizer** | Condense long content | — | gpt-4.1-mini |

### Medical Specialists

| Agent | Role | Tools | Model |
|-------|------|-------|-------|
| **Radiology Specialist** | Medical image analysis (X-ray, CT, MRI) | PubMed, Web Search | gpt-5.2 |
| **Cardiology Specialist** | Cardiovascular cases | PubMed, Calculator | gpt-4.1 |
| **Clinical Pharmacist** | Medication interactions, dosing | PubMed | gpt-4.1 |
| **Medical Researcher** | Evidence synthesis, literature review | PubMed | gpt-4.1 |
| **Medical Scribe** | Clinical documentation | — | gpt-4.1-mini |
| **Chief Doctor** | Clinical coordination, diagnosis | PubMed, Calculator | gpt-4.1 |

### Content & Marketing

| Agent | Role | Tools | Model |
|-------|------|-------|-------|
| **Content Writer** | Blog posts, articles, copy | Web Search | gpt-4.1 |
| **SEO Optimizer** | Search optimization | Web Search | gpt-4.1 |
| **Image Creator** | Generate images via DALL-E | — | gpt-4.1 |

### Research & Analysis

| Agent | Role | Tools | Model |
|-------|------|-------|-------|
| **Web Researcher** | Internet research, fact-checking | DuckDuckGo | gpt-4.1 |
| **Data Analyst** | Data analysis, visualization | Calculator | gpt-4.1 |

---

## Available Teams

### Medical AI Team

**Members:** Chief Doctor, Radiologist, Cardiologist, Pharmacist, Medical Researcher, Medical Scribe

**Best for:**
- Clinical case analysis
- Multi-specialty consultation
- Medical literature synthesis
- Diagnostic reasoning

**Coordination:** `delegate_on_complexity`

---

### General Team

**Members:** General Assistant, Web Researcher, Content Writer

**Best for:**
- Everyday research tasks
- Content creation
- Quick information gathering

---

### Marketing Team

**Members:** Content Writer, SEO Optimizer, Web Researcher

**Best for:**
- Blog posts and articles
- SEO-optimized content
- Marketing copy

---

### Showcase Team

**Members:** Showcase Assistant, Web Researcher

**Best for:**
- Demonstrations
- Quick research
- General assistance

---

## Selecting an Agent or Team

### In Chat

1. Open **Configuration** → **Chat**
2. Select a **preset** or choose team members
3. Or use **Agent Config** to select specific agents

### Via Presets

Presets bundle agent/team settings:

| Preset | Behavior |
|--------|----------|
| Quick Response | Single agent, fast model |
| Deep Analysis | Team with delegation |
| Team Research | Full team collaboration |

---

## Agent Skills Reference

Skills enable smart delegation in `delegate_on_complexity` mode:

| Skill | Agents |
|-------|--------|
| `imaging_interpretation` | Radiologist |
| `cardiovascular` | Cardiologist |
| `medication`, `pharmacology` | Pharmacist |
| `research`, `literature_review` | Medical Researcher, Web Researcher |
| `writing`, `content_creation` | Content Writer |
| `seo`, `optimization` | SEO Optimizer |
| `data_analysis` | Data Analyst |
| `summarization` | Summarizer, Note Taker |

---

## Customizing Agents

### Via UI

1. Open **Agent Config** page
2. Select an agent
3. Modify:
   - Instructions
   - Tools
   - Skills
   - Model
   - Coordination mode
4. Save changes

### Via JSON

Edit `data/agents/<agent_id>.json`:

```json
{
  "id": "custom_agent",
  "name": "Custom Agent",
  "role": "specialist",
  "instructions": ["Your custom instructions..."],
  "skills": ["custom_skill"],
  "tools": ["web_search", "calculator"],
  "model": "openai:gpt-4.1",
  "enabled": true
}
```

---

## Adding a New Agent

1. Create `data/agents/<agent_id>.json`
2. Set required fields: `id`, `name`, `role`, `instructions`
3. Add optional fields: `skills`, `tools`, `model`
4. Set `enabled: true`
5. Add to team `members` array if needed
6. Test in chat

---

## Next Steps

- [Chat](chat.md) — Use agents in conversations
- [Advanced Usage](advanced.md) — Agent configuration details
- [Agent System](../reference/agent-system.md) — Technical reference
