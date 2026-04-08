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


class ChatDailySnapshot(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    report_date: date
    analyses_completed: int
    posture_alert_count: int
    hand_movement_count: int
    smoking_like_count: int
    reminder_count: int
    hydration_progress_ml: int
    water_goal_ml: int
    poor_posture_ratio: float = Field(ge=0.0, le=1.0)
    summary: str


class ChatSessionSnapshot(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: int = 0


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
    recent_daily_snapshots: list[ChatDailySnapshot] = Field(default_factory=list)
    recent_event_type_counts: dict[str, int] = Field(default_factory=dict)
    recent_reminder_type_counts: dict[str, int] = Field(default_factory=dict)
    recent_sessions: list[ChatSessionSnapshot] = Field(default_factory=list)
    total_sessions_last_7_days: int = 0
    total_session_minutes_last_7_days: int = 0
    hydration_last_7_days_ml: int = 0
    analyses_completed_last_7_days: int = 0
    comparison_to_previous_day: str = ""
    data_gaps: list[str] = Field(default_factory=list)


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
