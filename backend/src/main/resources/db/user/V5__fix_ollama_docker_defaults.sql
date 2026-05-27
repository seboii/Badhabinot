-- Fix Ollama base URL: host.docker.internal is unreachable from ai-service container
-- All internal traffic must use the Docker service name
UPDATE user_settings
SET ollama_base_url = 'http://ollama:11434'
WHERE ollama_base_url = 'http://host.docker.internal:11434'
   OR ollama_base_url = 'http://localhost:11434';

-- Migrate stale model names to the current custom model
UPDATE user_settings
SET local_model_name = 'badhabinot:latest'
WHERE local_model_name IN ('llama3.2:3b', 'llama3.1:8b', 'llama3:8b', 'mistral:7b');
