CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    locale VARCHAR(16) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES user_profiles (user_id) ON DELETE CASCADE,
    sensitivity VARCHAR(16) NOT NULL,
    water_goal_ml INTEGER NOT NULL,
    water_interval_min INTEGER NOT NULL,
    exercise_interval_min INTEGER NOT NULL,
    quiet_hours_enabled BOOLEAN NOT NULL,
    quiet_hours_start TIME NOT NULL,
    quiet_hours_end TIME NOT NULL,
    model_mode VARCHAR(16) NOT NULL,
    notifications_enabled BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE user_consents (
    user_id UUID PRIMARY KEY REFERENCES user_profiles (user_id) ON DELETE CASCADE,
    privacy_policy_accepted BOOLEAN NOT NULL,
    camera_monitoring_accepted BOOLEAN NOT NULL,
    remote_inference_accepted BOOLEAN NOT NULL,
    accepted_at TIMESTAMPTZ NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
