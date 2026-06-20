# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS build
ARG SERVICE_PATH

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System libraries required by opencv-python-headless, mediapipe, ultralytics, and deepface.
# libgl1 provides libGL.so.1 which these packages link against even in headless mode.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Use a virtual environment so the runtime stage gets a clean, portable copy.
RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY python-services python-services

# vision-service ships heavy ML dependencies (torch via ultralytics, tensorflow via deepface).
# Pre-installing CPU-only variants here prevents pip's resolver from selecting the default
# CUDA-enabled wheels on Linux (~2 GB of torch+CUDA + nvidia_cudnn + nvidia_cusparselt, etc.).
# For ai-service this block is skipped — its requirements are lightweight.
#
# NOTE: `tensorflow-cpu` was deprecated/removed after TF 2.15. The requirements.txt asks for
# tf-keras>=2.16 which requires TF 2.16+. We install `tensorflow` (the unified package from 2.16+)
# which runs CPU-only when no CUDA driver is present — equivalent to the old tensorflow-cpu.
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "${SERVICE_PATH}" = "python-services/vision-service" ]; then \
        pip install \
            --index-url https://download.pytorch.org/whl/cpu \
            torch torchvision && \
        pip install tensorflow; \
    fi

RUN --mount=type=cache,target=/root/.cache/pip pip install \
    -r ${SERVICE_PATH}/requirements.txt

FROM python:3.11-slim AS runtime
ARG SERVICE_PATH
ARG APP_PORT=8091

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=${APP_PORT} \
    PATH="/venv/bin:$PATH" \
    HOME="/app"

# Same runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    libgl1 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /venv /venv
COPY --from=build /workspace/${SERVICE_PATH}/app ./app

# Create writable directories for face profiles and session logs (vision-service only)
# Harmless for ai-service (directories simply stay empty)
RUN mkdir -p /app/data/users /app/logs/sessions

# Pre-bake DeepFace Facenet weights into the image (vision-service only).
# Otherwise DeepFace lazy-downloads facenet_weights.h5 (~92 MB) to $HOME/.deepface
# on the first face-auth request. That path is NOT a persisted volume, so every
# container recreate re-downloads it — and concurrent requests trigger parallel
# downloads that previously corrupted memory and core-dumped the worker
# ("corrupted double-linked list" -> vision_service_unavailable). Baking the single
# weights file makes face-auth deterministic and offline-safe (incl. Azure deploy).
RUN if [ "${SERVICE_PATH}" = "python-services/vision-service" ]; then \
        mkdir -p /app/.deepface/weights && \
        python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/serengil/deepface_models/releases/download/v1.0/facenet_weights.h5', '/app/.deepface/weights/facenet_weights.h5')" && \
        cd /app && python -c "from ultralytics import YOLO; YOLO('yolov8n.pt'); YOLO('yolov8n-pose.pt')"; \
    fi

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app
EXPOSE ${APP_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT}"]
