CREATE TABLE behavior_events (
    id UUID PRIMARY KEY,
    analysis_id UUID NULL REFERENCES analysis_jobs (id) ON DELETE SET NULL,
    user_id UUID NOT NULL,
    session_id UUID NULL REFERENCES monitoring_sessions (id) ON DELETE SET NULL,
    event_type VARCHAR(64) NOT NULL,
    detector VARCHAR(64) NOT NULL,
    confidence NUMERIC(6, 4) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    interpretation VARCHAR(255) NOT NULL,
    recommendation_hint VARCHAR(255) NOT NULL,
    evidence_json TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_behavior_events_user_occurred_at ON behavior_events (user_id, occurred_at DESC);
CREATE INDEX idx_behavior_events_session_id ON behavior_events (session_id);
CREATE INDEX idx_behavior_events_type ON behavior_events (event_type);

CREATE TABLE reminder_events (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id UUID NULL REFERENCES monitoring_sessions (id) ON DELETE SET NULL,
    reminder_type VARCHAR(64) NOT NULL,
    source VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    message VARCHAR(255) NOT NULL,
    trigger_reason VARCHAR(255) NOT NULL,
    metadata_json TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_reminder_events_user_occurred_at ON reminder_events (user_id, occurred_at DESC);
CREATE INDEX idx_reminder_events_type ON reminder_events (reminder_type);

CREATE TABLE daily_reports (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    report_date DATE NOT NULL,
    analyses_completed INTEGER NOT NULL,
    posture_alert_count INTEGER NOT NULL,
    hand_movement_count INTEGER NOT NULL,
    smoking_like_count INTEGER NOT NULL,
    reminder_count INTEGER NOT NULL,
    hydration_progress_ml INTEGER NOT NULL,
    water_goal_ml INTEGER NOT NULL,
    poor_posture_ratio NUMERIC(6, 4) NOT NULL,
    summary TEXT NOT NULL,
    recommendations_json TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uk_daily_reports_user_date UNIQUE (user_id, report_date)
);

CREATE INDEX idx_daily_reports_user_date ON daily_reports (user_id, report_date DESC);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(16) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_chat_messages_conversation_created_at ON chat_messages (conversation_id, created_at ASC);
CREATE INDEX idx_chat_messages_user_created_at ON chat_messages (user_id, created_at DESC);
