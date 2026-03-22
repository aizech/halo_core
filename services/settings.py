"""Application configuration helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
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
    # DICOM settings
    dicom_anonymize_on_upload: bool = Field(
        default=False,
        validation_alias="DICOM_ANONYMIZE_ON_UPLOAD",
        description="Auto-anonymize DICOM files on upload to Sources.",
    )
    dicom_anonymization_tags: List[str] = Field(
        default_factory=lambda: [
            "PatientName",
            "PatientID",
            "PatientBirthDate",
            "PatientSex",
            "PatientAddress",
            "InstitutionName",
            "ReferringPhysicianName",
        ],
        validation_alias="DICOM_ANONYMIZATION_TAGS",
        description="List of DICOM tags to anonymize.",
    )
    dicom_pacs_host: Optional[str] = Field(
        default=None,
        validation_alias="DICOM_PACS_HOST",
        description="DICOM PACS server hostname for MCP connector.",
    )
    dicom_pacs_port: Optional[int] = Field(
        default=None,
        validation_alias="DICOM_PACS_PORT",
        description="DICOM PACS server port.",
    )
    dicom_pacs_ae_title: Optional[str] = Field(
        default=None,
        validation_alias="DICOM_PACS_AE_TITLE",
        description="DICOM PACS AE Title.",
    )
    default_model: str = Field(
        default="openai:gpt-4o",
        validation_alias="HALO_DEFAULT_MODEL",
        description="Default model ID used when no agent-specific model is configured.",
    )
    default_chat_instructions: str = Field(
        default=(
            "Du bist ein Assistent, der Fragen nur mit den bereitgestellten Quellen beantwortet. "
            "Zitiere Quellen inline im Format [Quelle]."
        ),
        validation_alias="HALO_DEFAULT_CHAT_INSTRUCTIONS",
        description="Default system instructions for the chat agent.",
    )

    @field_validator("dicom_pacs_port", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v: object) -> Optional[object]:
        """Convert empty string to None for optional int fields."""
        return None if v == "" else v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[arg-type]
