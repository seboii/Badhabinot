# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS build
ARG SERVICE_PATH

WORKDIR /workspace
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY apps/python-services apps/python-services
RUN --mount=type=cache,target=/root/.cache/pip pip install --prefix /install --no-cache-dir -r ${SERVICE_PATH}/requirements.txt

FROM python:3.11-slim AS runtime
ARG SERVICE_PATH
ARG APP_PORT=8091

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=${APP_PORT}

COPY --from=build /install /usr/local
COPY --from=build /workspace/${SERVICE_PATH}/app ./app

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app
EXPOSE ${APP_PORT}

CMD ["sh", "-c", "uvicorn app.main:app --host ${UVICORN_HOST} --port ${UVICORN_PORT}"]
