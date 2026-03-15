from __future__ import annotations

import streamlit as st

from app import main


def render_help_page() -> None:
    main._init_state()
    main.render_sidebar()
    st.title("HALO Core - User Handbook")
    st.caption("Made with :material/favorite: by Corpus Analytica")

    with st.expander("Quick Start", expanded=False):
        st.code(
            """# Clone and setup
git clone https://github.com/aizech/halo_core.git
cd halo_core
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt

# Configure API key
echo 'OPENAI_API_KEY = "sk-..."' > .streamlit/secrets.toml

# Run
streamlit run app/main.py""",
            language="bash",
        )

    st.markdown("""

## Welcome to HALO Core

**HALO** means **Holistic Agent Logical Orchestrator**. It turns information overload into clear, shippable decisions — collect sources, run grounded AI chat, generate outputs, and save reusable insights, all in one workspace.

---

## Key Features

### Team-Based AI Collaboration
Run specialized AI agents with different roles, instructions, and tools in a single session.

### Smart Delegation
Multiple coordination modes: `direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`.

### Source-Grounded Responses
Answers are grounded in your selected documents with citation-aware structure.

### Transparent Execution
Inspect tool calls, agent actions, and runtime traces on demand.

### Studio Pipeline
Generate reports, presentations, podcasts, and more directly from your research context.

---

## Your first win in 90 seconds

1. In **Sources**, click **+ Quellen hinzufügen** and upload 1–3 files.
2. Select those files.
3. In **Chat**, ask: "From selected sources only, list key decisions, risks, and next actions."
4. Save the strongest response as a note.
5. In **Studio**, generate a **Bericht**.

You now have an end-to-end, source-grounded pipeline running.

---

## Product Tour

### Sources: your content library

Use Sources to ingest, curate, and activate context.

- Upload documents, data files, images, audio, and video.
- Import connector results.
- Rename, download, or delete items.
- Select exactly what HALO is allowed to use.

Use **Zusammenfassung aller Quellen** in Chat to get a fast strategic briefing before deep analysis, or after changing your source set.

---

### Chat: AI conversations and multimodal input

Chat supports text prompts and multimodal workflows (image/audio-enabled interactions).

Key strengths:
- source-grounded responses,
- optional team-agent orchestration,
- expandable tool/runtime transparency,
- save-to-note flow for reusable outputs.

Prompt pattern:
"Based on selected sources only, provide: 3 findings, 3 risks, 3 actions, and open questions."

---

### Studio: generating outputs from templates

Studio templates transform your context into structured assets.

Available templates include: Bericht, Infografik, Podcast, Videoübersicht, Präsentation, Datentabelle, Mindmap, Karteikarten, Quiz.

Use Studio when you need outputs your team can immediately review and share.

---

### Notes: reusable intelligence layer

Notes preserve your best outputs from chat and summaries.

Typical uses:
- keep approved reasoning,
- track decisions over time,
- convert notes back into sources,
- build a durable project memory trail.

---

### Configuration and Agent Config

In **Configuration**, tune app behavior, presets, and runtime settings.

In **Agent Config**, power users control:
- role instructions,
- tool access,
- MCP server usage,
- coordination mode (`direct_only`, `delegate_on_complexity`, `always_delegate`, `coordinated_rag`).

---

## Workflows

### Rapid Due Diligence Brief
1. Import source bundle.
2. Ask Chat for thesis, evidence, contradictions, and missing data.
3. Save key outputs as notes.
4. Generate **Bericht**.

Outcome: executive-ready draft in a single session.

### Research to Presentation
1. Build source set.
2. Generate all-sources summary.
3. Ask Chat for slide storyline.
4. Generate **Präsentation** output.

Outcome: clear narrative structure you can polish fast.

### Multimodal Analysis Sprint
1. Upload document + image + optional audio notes.
2. Ask for integrated interpretation.
3. Save final synthesis as note.
4. Generate **Infografik** or **Bericht**.

Outcome: richer analysis from mixed inputs without tool hopping.

---

## Tips for Premium Results

1. **Set explicit scope** — "Use only selected Q4 sources."
2. **Ask for structure** — "Return findings, risks, actions, and assumptions."
3. **Run iterative passes** — broad summary → critical challenge → decision-ready output.
4. **Save strong outputs as notes** — convert one great answer into reusable project intelligence.
5. **Tune agents and tools for your domain** — targeted setup improves quality and consistency.

---

## Troubleshooting

### "Answers are generic"
- Confirm sources are selected.
- Refresh the source summary.
- Add explicit structure and constraints to your prompt.

### "Import failed"
- Check the supported file type.
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

### What coordination modes are available?
`direct_only`, `delegate_on_complexity`, `always_delegate`, and `coordinated_rag` — configurable per agent in Agent Config.

### Can HALO handle multimodal input?
Yes. Text workflows can be extended with image/audio-enabled flows.

### What if streaming fails?
HALO includes fallback behavior to preserve response continuity where possible.

---

## Resources

- [Full Documentation](https://docs.corpusanalytica.com)
- [User Handbook](https://docs.corpusanalytica.com/handbook/)
- [Admin Guide](https://docs.corpusanalytica.com/admin/)
- [Technical Reference](https://docs.corpusanalytica.com/reference/)
- [Changelog](https://docs.corpusanalytica.com/changelog/)
- [GitHub Repository](https://github.com/aizech/halo_core)
- [Live Demo](https://halocore.streamlit.app/)
- [Corpus Analytica](https://www.corpusanalytica.com/)

---

Made with :material/favorite: by Corpus Analytica
        """)


if __name__ == "__main__":
    render_help_page()
