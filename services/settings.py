"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment or `.streamlit/secrets.toml`."""

    env: str = Field("local", description="Deployment environment name")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    data_dir: Path = Field(default=Path("data"), env="HALO_DATA_DIR")
    templates_dir: Path = Field(default=Path("templates"), env="HALO_TEMPLATES_DIR")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
