#!/bin/sh
# Builds the custom badhabinot model inside the Ollama container.
# Waits for the base model to be available first.

set -e

MODEL_NAME="${BADHABINOT_MODEL_NAME:-badhabinot:latest}"
BASE_MODEL="${OLLAMA_MODEL_NAME:-llama3.2:3b}"
OLLAMA_HOST="${OLLAMA_HOST:-http://ollama:11434}"
MODELFILE_PATH="/modelfiles/Modelfile"

echo "[build-model] Waiting for Ollama to be ready..."
until ollama list > /dev/null 2>&1; do
  sleep 2
done

echo "[build-model] Checking if base model '${BASE_MODEL}' is available..."
until ollama list | grep -q "${BASE_MODEL}"; do
  echo "[build-model] Base model not ready yet, waiting..."
  sleep 5
done

echo "[build-model] Base model ready. Building '${MODEL_NAME}'..."
ollama create "${MODEL_NAME}" -f "${MODELFILE_PATH}"

echo "[build-model] Model '${MODEL_NAME}' built successfully."
ollama list
