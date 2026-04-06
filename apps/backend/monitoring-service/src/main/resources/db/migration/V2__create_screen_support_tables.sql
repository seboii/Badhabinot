CREATE TABLE monitoring_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    client_surface VARCHAR(32) NOT NULL,
    device_type VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_monitoring_sessions_user_id ON monitoring_sessions (user_id);
CREATE INDEX idx_monitoring_sessions_status ON monitoring_sessions (status);

CREATE TABLE activity_feed (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id UUID NULL REFERENCES monitoring_sessions (id) ON DELETE SET NULL,
    activity_type VARCHAR(64) NOT NULL,
    category VARCHAR(32) NOT NULL,
    title VARCHAR(160) NOT NULL,
    message VARCHAR(255) NOT NULL,
    confidence NUMERIC(6, 4) NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_activity_feed_user_occurred_at ON activity_feed (user_id, occurred_at DESC);
CREATE INDEX idx_activity_feed_category ON activity_feed (category);

CREATE TABLE hydration_logs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id UUID NULL REFERENCES monitoring_sessions (id) ON DELETE SET NULL,
    amount_ml INTEGER NOT NULL,
    source VARCHAR(32) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_hydration_logs_user_occurred_at ON hydration_logs (user_id, occurred_at DESC);

