CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    session_id VARCHAR(128) NOT NULL,
    frame_id VARCHAR(128) NOT NULL,
    status VARCHAR(32) NOT NULL,
    subject_present BOOLEAN NULL,
    posture_state VARCHAR(32) NULL,
    behavior_type VARCHAR(64) NULL,
    confidence NUMERIC(6, 4) NULL,
    failure_code VARCHAR(64) NULL,
    failure_message VARCHAR(512) NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_analysis_jobs_user_id ON analysis_jobs (user_id);
CREATE INDEX idx_analysis_jobs_session_id ON analysis_jobs (session_id);
