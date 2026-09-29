from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator


class Category(StrEnum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(StrEnum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


VALID_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS, Status.REJECTED}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED, Status.REJECTED}),
    Status.RESOLVED: frozenset(),
    Status.REJECTED: frozenset(),
}

ComplaintText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=10, max_length=2000)
]
LocationText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)
]


class TriageResult(BaseModel):
    category: Category
    priority: Priority
    summary: str = Field(min_length=1, max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)

    @field_validator("summary")
    @classmethod
    def one_line_summary(cls, value: str) -> str:
        if "\n" in value or "\r" in value:
            raise ValueError("summary must be one line")
        return value.strip()


class ComplaintCreate(BaseModel):
    text: ComplaintText
    location: LocationText
    reporter_contact: str | None = Field(default=None, max_length=200)

    @field_validator("reporter_contact")
    @classmethod
    def blank_contact_is_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class StatusUpdate(BaseModel):
    status: Status


class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: Category
    priority: Priority
    status: Status
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime
    allowed_transitions: list[Status] = Field(default_factory=list)


class ComplaintPage(BaseModel):
    items: list[ComplaintRead]
    total: int
    page: int
    page_size: int


class StatsResponse(BaseModel):
    by_category: dict[Category, int]
    by_priority: dict[Priority, int]
    total: int


class ProviderOutcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    timestamp: datetime


class ProviderMeta(BaseModel):
    active_provider: str
    outcomes: list[ProviderOutcome]
