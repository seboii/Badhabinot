ALTER TABLE user_settings
    ADD COLUMN IF NOT EXISTS local_model_name VARCHAR(100) NOT NULL DEFAULT 'llama3.2:3b';

ALTER TABLE user_settings
    ADD COLUMN IF NOT EXISTS ollama_base_url VARCHAR(255) NOT NULL DEFAULT 'http://localhost:11434';
