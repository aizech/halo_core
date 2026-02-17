"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Central configuration loaded from environment or `.streamlit/secrets.toml`."""

    env: str = Field("local", description="Deployment environment name")
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    data_dir: Path = Field(default=Path("data"), validation_alias="HALO_DATA_DIR")
    templates_dir: Path = Field(
        default=Path("templates"),
        validation_alias="HALO_TEMPLATES_DIR",
    )
    agent_db_file: Optional[str] = Field(
        default=None,
        validation_alias="HALO_AGENT_DB",
        description="Path to SQLite file for Agno agent memory. None = JSON-only (no DB).",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
