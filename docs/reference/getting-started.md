# Getting Started

## Requirements

- Python 3.11+
- A virtual environment (`.venv`)

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run the app

```bash
streamlit run app/main.py
```

## Run quality checks

```bash
black .
ruff check .
pytest
```

## Next reading

- [Repository Overview](repository-overview.md)
- [Architecture and Runtime](architecture-and-runtime.md)
