-- Push token storage for FCM mobile notifications
CREATE TABLE push_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    token       TEXT NOT NULL,
    platform    VARCHAR(16) NOT NULL DEFAULT 'ANDROID',
    device_name VARCHAR(128),
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX uidx_push_tokens_token ON push_tokens (token);
CREATE INDEX idx_push_tokens_user_id ON push_tokens (user_id) WHERE active = TRUE;
