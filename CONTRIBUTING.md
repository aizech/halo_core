# Contributing to HALO Core

Thanks for helping improve HALO Core. This project focuses on a NotebookLM-style Streamlit experience with Agno-backed orchestration for sources, chat, and Studio templates.

## Quick Start

### Prerequisites
- Python 3.10+
- Git
- FFmpeg (for audio/video transcription)
- OpenAI API key or other provider credentials (store in `.streamlit/secrets.toml`)

### Development Setup
1. **Clone the repository**

   ```bash
   git clone https://github.com/aizech/halo_core.git
   cd halo_core
   ```

2. **Create a virtual environment**
   
```bash
   python -m venv .venv
   . .venv/Scripts/activate        # Windows Powershell: .venv\Scripts\Activate.ps1
   ```
   
3. **Install dependencies**

   ```bash
pip install -r requirements.txt
   ```
   
4. **Configure secrets**
   
```toml
   # .streamlit/secrets.toml
OPENAI_API_KEY = "sk-..."
   ANTHROPIC_API_KEY = "sk-..."
   ```

## Contribution Workflow
1. **Create a feature branch**

   ```bash
   git checkout -b feature/<issue>-<short-description>
   ```

2. **Make your changes**
   - Keep edits focused.
   - Update documentation (PRD/ADR/README) when requirements change.
   - Add or update tests for new behavior.
3. **Run checks**
   
   ```bash
pytest
   ruff check .
   black --check .
   mypy app services
   ```
   
4. **Run the app**
   
```bash
   streamlit run app/main.py
```

5. **Submit a PR**
   - Describe the change, include screenshots for UI updates.
   - Call out any backward-compatibility concerns.

## Coding Standards
- Python formatting: **black**
- Linting: **ruff**
- Prefer type hints for public interfaces
- Keep Streamlit UI changes minimal and consistent with the existing design

## Documentation
- Update `HALO_CORE_PRD.md` for requirements changes.
- Add/extend ADRs in `adr/` for architectural decisions.
- Ensure README references stay current.

## Security
- Never commit secrets or API keys.
- Avoid logging sensitive data.

## Getting Help
- Open an issue for questions or clarifications.
