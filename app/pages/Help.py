from __future__ import annotations

import streamlit as st

from app import main


def render_help_page() -> None:
    main._init_state()
    main.render_sidebar()
    st.title("HALO Core - User Handbook")
    st.caption("Made with ❤️ by Corpus Analytica")
    st.markdown("""

## Welcome to HALO Core

**HALO** means **Holistic Agent Logical Orchestrator**.

HALO is built for one outcome: helping you move from information overload to clear, shippable decisions.

In one workspace, you can:
- collect and control your evidence,
- orchestrate specialist AI agents,
- produce decision-ready outputs,
- and keep high-value insights reusable.

If your current workflow feels like tabs, copy-paste, and uncertainty, HALO is your upgrade.

---

## Why HALO feels different

### 1) Workflow-first intelligence
HALO is designed around a full operating loop:
1. Add sources
2. Ask grounded questions
3. Save the strongest insights
4. Generate artifacts (report, infographic, podcast, presentation, and more)

### 2) AI collaboration, not just one assistant
HALO can run role-based agents with different instructions, tools, and delegation behavior.
You can work with a coordinated system that behaves like a researcher, analyst, editor, and producer.

### 3) Transparent where it matters
When needed, you can inspect tool calls, agent actions, and runtime traces.
This gives you trust and control without slowing down execution.

### 4) Source-grounded by default
You choose active sources. HALO answers against that context and can preserve citation-aware structure.

### 5) Built for usable outcomes
HALO does not stop at answers. It turns context into assets your team can review, reuse, and share.

---

## Your first win in 90 seconds

1. In **Sources**, click **+ Quellen hinzufügen** and upload 1-3 files.
2. Select those files.
3. In **Chat**, ask: "From selected sources only, list key decisions, risks, and next actions."
4. Save the strongest response as a note.
5. In **Studio**, generate a **Bericht**.

You now have an end-to-end, source-grounded pipeline running.

---

## Product tour

### A) Sources: your evidence control center

Use Sources to ingest, curate, and activate context.

You can:
- upload documents, data files, images, audio, and video,
- import connector results,
- rename/download/delete items,
- select exactly what HALO is allowed to use.

Why it matters: stronger source control means stronger answers.

---

### B) Chat: where intelligence becomes decisions

Chat supports text prompts and multimodal workflows (including image/audio-enabled interactions).

Key strengths:
- source-grounded responses,
- optional team-agent orchestration,
- expandable tool/runtime transparency,
- save-to-note flow for reusable outputs.

Prompt pattern:
"Based on selected sources only, provide: 3 findings, 3 risks, 3 actions, and open questions."

---

### C) Summary of All Sources: instant orientation

In Chat, **Zusammenfassung aller Quellen** gives you a fast strategic briefing.

Use it to:
- get aligned before deep analysis,
- detect stale summaries after source changes,
- pin high-value summaries into notes.

---

### D) Studio: from insight to deliverable

Studio templates transform context into structured assets.

Common templates:
- Bericht
- Infografik
- Podcast
- Videouebersicht
- Praesentation
- Datentabelle

Use Studio when you need outputs your team can immediately review and share.

---

### E) Notes: your reusable intelligence layer

Notes preserve your best outputs from chat and summaries.

Typical uses:
- keep approved reasoning,
- track decisions over time,
- convert notes back into sources,
- build a durable project memory trail.

---

### F) Configuration + Agent Config: tailor HALO to your mission

In **Configuration**, you tune app behavior, presets, and runtime settings.

In **Agent Config**, power users control:
- role instructions,
- tool access,
- MCP server usage,
- coordination modes like `direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`.

This is where HALO shifts from helpful to formidable.

---

## High-impact workflows

### Workflow 1: Rapid due diligence brief
1. Import source bundle.
2. Ask Chat for thesis, evidence, contradictions, and missing data.
3. Save key outputs as notes.
4. Generate **Bericht**.

Outcome: executive-ready draft in a single session.

### Workflow 2: Research to presentation
1. Build source set.
2. Generate all-sources summary.
3. Ask Chat for slide storyline.
4. Generate **Praesentation** output.

Outcome: clear narrative structure you can polish fast.

### Workflow 3: Multimodal analysis sprint
1. Upload document + image + optional audio notes.
2. Ask for integrated interpretation.
3. Save final synthesis as note.
4. Generate **Infografik** or **Bericht**.

Outcome: richer analysis from mixed inputs without tool hopping.

---

## Tips for premium results

1. **Set explicit scope**
   - Example: "Use only selected Q4 sources."

2. **Ask for structure**
   - Example: "Return findings, risks, actions, and assumptions."

3. **Run iterative passes**
   - Pass 1: broad summary
   - Pass 2: critical challenge
   - Pass 3: decision-ready output

4. **Save strong outputs as notes**
   - Convert one great answer into reusable project intelligence.

5. **Tune agents/tools for your domain**
   - Targeted setup can dramatically improve quality and consistency.

---

## Troubleshooting quick fixes

### "Answers are generic"
- Confirm sources are selected.
- Refresh source summary.
- Add explicit structure and constraints to your prompt.

### "Import failed"
- Check supported file type.
- For audio/video workflows, ensure local dependencies are installed.

### "Memory not visible in Account"
- Memory backend may be disabled in the current environment.

### "Studio output feels weak"
- Improve source selection first.
- Save stronger notes from chat, then regenerate.

---

## FAQ

### Do I need a user account?
Not in the default local setup.

### Where is my data stored?
By default in local project data files.

### Can I control tools and models?
Yes, via Configuration and Agent Config.

### Can HALO handle multimodal input?
Yes. Text workflows can be extended with image/audio-enabled flows.

### What if streaming fails?
HALO includes fallback behavior to preserve response continuity where possible.

---

## Final note

HALO is strongest when you use it as a **collaborative intelligence system**, not a one-prompt chatbot.

Curate evidence. Ask sharper questions. Capture winning outputs. Then ship.

Made with ❤️ by Corpus Analytica
        """)


if __name__ == "__main__":
    render_help_page()
