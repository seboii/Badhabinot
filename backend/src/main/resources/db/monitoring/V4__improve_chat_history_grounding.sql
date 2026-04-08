ALTER TABLE chat_messages
    ADD COLUMN IF NOT EXISTS metadata_json TEXT NULL;

CREATE INDEX IF NOT EXISTS idx_chat_messages_user_conversation_created_at
    ON chat_messages (user_id, conversation_id, created_at DESC);
