from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime


class ChatFact(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    label: str
    value: str


class ChatEvent(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    event_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: str
    interpretation: str
    occurred_at: datetime
    evidence: dict[str, object]


class ChatReminder(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    reminder_type: str
    message: str
    trigger_reason: str
    occurred_at: datetime


class ChatContext(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    hydration_progress_ml: int
    water_goal_ml: int
    analyses_completed: int
    posture_alert_count: int
    hand_movement_count: int
    smoking_like_count: int
    reminder_count: int
    poor_posture_ratio: float = Field(ge=0.0, le=1.0)
    summary: str
    recommendations: list[str]
    facts: list[ChatFact]
    recent_events: list[ChatEvent]
    recent_reminders: list[ChatReminder]


class ChatRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    conversation_id: str
    user_id: str
    timezone: str | None = None
    report_date: date
    message: str
    history: list[ChatMessage]
    context: ChatContext


class ChatModelDescriptor(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str
    name: str
    mode: Literal["external_api", "mock"]


class ChatResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    conversation_id: str
    answer: str
    grounded_facts: list[str]
    follow_up_suggestions: list[str]
    model: ChatModelDescriptor
