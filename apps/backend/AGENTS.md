# AGENTS.md

## Scope

This directory is responsible for Spring Boot backend services and orchestration.

Focus on:
- API exposure
- auth/session/user logic
- orchestration of analysis flows
- persistence
- reminder logic
- report aggregation
- chatbot context preparation
- integration with Python services
- integration with PostgreSQL and Redis

Do not move computer vision logic into backend services.
Do not move browser/UI logic here.

---

## Current backend priorities

Highest priority:
1. receive analysis requests correctly
2. validate and normalize payloads
3. orchestrate calls to vision-service and ai-service
4. persist behavior events/results correctly
5. generate reminders correctly
6. generate daily reports correctly
7. provide chatbot context endpoints or chat orchestration correctly

Fix runtime/config/integration issues before refactoring style.

---

## Backend responsibilities

Backend services are the source of truth for:
- API contracts
- user/session linkage
- business orchestration
- event persistence
- reminder scheduling and evaluation
- report building
- preparing grounded context for chatbot flows

Backend services must not:
- perform heavy vision processing locally
- depend on a local LLM as primary production path
- duplicate frontend behavior logic unnecessarily

---

## Integration rules

All inter-service calls must be explicit, typed, and resilient.

When calling Python services or AI providers:
- centralize integration clients
- define clear request/response DTOs
- handle timeout and retry intentionally
- return useful error details
- log enough context for debugging without leaking secrets

Do not hide core integration logic inside controllers.

---

## Data and state rules

Persistent data belongs in PostgreSQL.
Short-lived or coordination state may use Redis when justified.

Use backend data models for:
- users
- sessions
- analysis requests
- behavior events
- reminders
- reports
- chatbot context records if needed
- preferences/settings

Do not use Redis as primary persistent storage.

---

## Reminder rules

Reminder logic belongs here, not only in frontend.

Support:
- hydration reminders
- posture reminders
- inactivity reminders if implemented
- cooldowns
- user preferences
- event-based triggers
- scheduled daily reporting if needed

---

## Report rules

Reports must be generated from stored behavior data.

Support:
- daily summaries
- end-of-day reports
- trend summaries
- event counts/timelines
- recommendation summaries

Do not leave report endpoints as static placeholders.

---

## Chatbot rules

Backend must ground chatbot responses in user data.

Responsibilities include:
- gathering recent events
- gathering reports
- gathering reminder history where relevant
- building a structured context package for AI/chat service
- exposing stable chat APIs to frontend

Do not make chatbot responses generic-only.

---

## File-reading discipline

Read these first:
- analysis controllers
- orchestration services
- integration clients
- DTOs for analysis/report/chat
- persistence models for events/reminders/reports
- configuration classes
- datasource/Redis config
- security config only if it blocks main feature flow

Avoid unrelated service modules unless they directly block the current scope.

---

## Completion checklist

A backend task is not complete unless applicable items are verified:

- analysis endpoint receives requests correctly
- backend calls vision-service correctly
- backend calls ai-service correctly where needed
- behavior events are stored correctly
- reminder logic runs correctly
- daily report endpoint returns real data
- chatbot endpoint is grounded in stored data
- DB and Redis configs still work
- Docker runtime still works