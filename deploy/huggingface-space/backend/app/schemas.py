"""Request bodies for account, progress, and assistant routes."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AuthIn(BaseModel):
    email: str = Field(default="", max_length=254)
    password: str = Field(default="", max_length=128)


class ProgressIn(BaseModel):
    lesion_id: str = Field(default="", max_length=60)
    note: str = Field(default="", max_length=1000)
    recorded_at: str | None = None
    analysis_id: str | None = None


class AssistantTurnIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1000)


class AssistantIn(BaseModel):
    message: str = Field(default="", max_length=1000)
    language: Literal["en", "ar"] = "en"
    history: list[AssistantTurnIn] = Field(default_factory=list, max_length=20)
    allow_generation: bool = False
