UPDATE user_settings
SET ollama_base_url = 'http://host.docker.internal:11434'
WHERE ollama_base_url = 'http://localhost:11434';
