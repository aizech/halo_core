"""Shared dataclasses and Pydantic models for the HALO Core Streamlit app."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceItem:
    name: str
    type_label: str
    meta: str
    selected: bool = True
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: str = field(default_factory=_now_iso)
    file_path: str | None = None  # Path to binary file for DICOM sources


@dataclass
class StudioAction:
    action_id: str
    label: str


@dataclass
class StudioTeam:
    team_id: str
    name: str
    description: str


@dataclass
class StudioTemplate:
    template_id: str
    title: str
    description: str
    status: str = ""
    icon: str = ":material/extension:"
    color: str = "#f5f5f5"
    badge: Optional[str] = None
    team_id: Optional[str] = None
    agent_id: Optional[str] = None
    actions: List[StudioAction] = field(default_factory=list)
    agent: Dict[str, str] = field(default_factory=dict)
    defaults: Dict[str, str] = field(default_factory=dict)


class StudioActionConfig(BaseModel):
    id: str = Field("generate", alias="id")
    label: str = "Generieren"


class StudioTeamConfig(BaseModel):
    id: str
    name: str
    description: str = ""


class StudioTemplateConfig(BaseModel):
    id: str
    title: str
    description: str
    status: str = ""
    icon: str = ":material/extension:"
    color: str = "#f5f5f5"
    badge: Optional[str] = None
    team_id: Optional[str] = None
    agent_id: Optional[str] = None
    actions: list[StudioActionConfig] = Field(default_factory=list)
    agent: dict[str, str] = Field(default_factory=dict)
    defaults: dict[str, str] = Field(default_factory=dict)


class StudioTemplatesConfig(BaseModel):
    teams: list[StudioTeamConfig] = Field(default_factory=list)
    templates: list[StudioTemplateConfig] = Field(default_factory=list)


StudioTemplateConfig.model_rebuild()
StudioTemplatesConfig.model_rebuild()
