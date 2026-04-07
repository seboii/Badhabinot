# AGENTS.md

## Mission

This repository is under active development as a behavior-analysis platform.

Your current mission is **not** to redesign the whole project.
Your mission is to **work on top of the existing codebase** and focus only on the current product-critical scope:

1. camera capture flow
2. behavior / image / video analysis
3. posture detection
4. hand-movement analysis
5. smoking-related behavior detection with confidence-based output
6. reminder engine (especially hydration / posture reminders)
7. daily / end-of-day reporting
8. user-facing AI chatbot grounded in tracked behavior data
9. fixing the current runtime, Docker, API, and integration errors blocking these features

Do not spend time on unrelated product areas unless they directly block this scope.

---

## Strict scope control

### Prioritize these areas first

Read and work in these areas before anything else:

- `apps/web/`
- `apps/backend/`
- `apps/python-services/`
- `infra/docker/`
- `.env*`
- `docker-compose*.yml`
- `README.md`
- database migration and initialization files
- API contracts related to camera, analysis, reminders, reports, and chat

### Avoid unrelated exploration unless required

Do **not** spend time deeply analyzing unrelated modules unless they directly block the current feature scope, for example:

- billing
- payments
- marketing pages
- generic admin pages
- experimental old modules
- unrelated authentication refactors
- unrelated notification channels
- unused legacy code not involved in the current behavior-analysis flow

If you must inspect an unrelated module, explain briefly why it is required for the current task.

---

## Current product objective

The current system must become a working behavior-analysis application.

### Required capabilities

The system must support:

- camera access from the web app
- image / frame / stream ingestion
- posture analysis
- hand motion analysis
- smoking-like behavior detection using confidence-based logic
- hydration reminders
- posture reminders
- end-of-day report generation
- chatbot answers based on the user's own tracked data
- working frontend-backend-python integration
- working Docker-based local runtime

### Current truth

The most important current problem is that the system does not correctly:
- capture camera input,
- analyze it end-to-end,
- generate behavior events reliably,
- expose results cleanly in the UI.

Fix these before adding cosmetic improvements.

---

## Architecture constraints

Preserve this architecture:

### Web frontend
Responsible for:
- camera permission and capture UI
- dashboard
- live analysis UI
- reminders UI
- reports UI
- chatbot UI
- theme toggle (light/dark)
- API calls to backend only

### Spring Boot backend
Responsible for:
- auth/session/user logic
- orchestration
- persistence
- reminder logic
- report aggregation
- chatbot context preparation
- calling Python services
- exposing stable APIs to the frontend

### Python services
Responsible for:
- computer vision
- posture analysis
- hand movement analysis
- smoking-related behavior heuristics/detection
- structured detection outputs

### AI service
Responsible for:
- higher-level interpretation and chat assistance
- using external AI APIs
- normalizing model/provider responses

### Data layer
- PostgreSQL for persistence
- Redis only for short-lived state, caching, or job coordination where useful

---

## Non-negotiable implementation rules

1. Build on top of the existing repository.
2. Do not replace the whole project without necessity.
3. Do not create disconnected demo code.
4. Do not leave placeholder routes or fake UI flows.
5. Do not fake detections.
6. If a behavior cannot be detected reliably, return confidence-based output and state limitations honestly.
7. Keep detectors modular.
8. Keep request/response schemas explicit.
9. Keep environment variables centralized and consistent.
10. Keep Docker runtime working.
11. Prefer root-cause fixes over surface-level patches.

---

## AI policy for this repository

### Required
Higher-level AI analysis and chatbot behavior must be **API-based**.

### Forbidden as default path
- do not make local LLM inference the main production path
- do not hardwire the app to a local AI runtime
- do not require local heavyweight model setup for normal usage

### Expected design
- provider adapter pattern
- environment-configured API keys
- environment-configured base URL / model name
- timeout and retry handling
- normalized structured responses

---

## Behavior-analysis design rules

Implement the behavior pipeline in modular stages:

1. input ingestion
2. preprocessing
3. landmark / pose / motion extraction
4. detector modules
5. normalized behavior events
6. event aggregation
7. reminder generation
8. report generation
9. chatbot/report query layer

### Required detector modules
At minimum support and improve:
- posture detector
- hand-movement detector
- smoking-related behavior detector

### Output expectations
Every detection event should aim to include:
- event type
- timestamp
- confidence
- severity if applicable
- evidence metadata
- user-facing interpretation or recommendation hint

---

## Reminder rules

Reminder logic must be backend-driven, not just frontend-only.

Support:
- hydration reminders
- posture reminders
- inactivity or unhealthy-pattern reminders if available
- cooldown logic
- configurable thresholds/preferences
- event-based and scheduled reminder generation where appropriate

---

## Reporting rules

Support:
- daily summary
- end-of-day report
- counts of detected behaviors
- posture trend summary
- reminder history
- event timeline
- practical recommendations

Do not leave reports as static placeholders.

---

## Chatbot rules

The chatbot must be grounded in application data.

### Must do
- answer questions about the user's own tracked behavior
- use report/event/reminder/session data
- support follow-up questions
- provide helpful summaries and improvement suggestions

### Must not do
- respond as a generic assistant without using user data
- invent untracked behavior history
- ignore actual stored events and reports

---

## Camera and analysis debugging procedure

When working on camera/analysis issues, always trace the full path:

1. browser camera permission
2. frontend capture logic
3. frontend payload format
4. backend endpoint
5. backend validation
6. backend orchestration
7. Python service request contract
8. vision processing
9. event persistence / caching
10. reminder/report generation
11. frontend rendering of results

Do not mark the issue as solved just because `/health` returns 200.

---

## File-reading discipline

Before reading many files, first inspect only the files most likely to matter for the current task.

### Read first
- frontend camera page/component
- frontend API client
- backend controller/service handling analysis
- backend integration client for Python services
- Python vision service routes
- Python analysis logic modules
- Docker compose files
- env/config files
- database config and migrations

### Read later only if needed
- unrelated UI pages
- unrelated services
- old archived files
- non-blocking documentation

If you find yourself reading many unrelated files, stop and return to the current feature path.

---

## Change strategy

Prefer this order:

1. identify root cause
2. fix contracts/config/runtime
3. fix end-to-end feature path
4. improve detector modularity
5. improve reminders/reports/chat integration
6. improve UX and cleanup

Do not start with cosmetic refactors.

---

## Required deliverables for each substantial task

When making meaningful changes, provide:

1. audit summary
2. root-cause summary
3. exact files changed
4. implementation details
5. env/config changes
6. Docker/runtime notes
7. validation steps
8. remaining limitations if any

---

## Validation checklist

A task in this repository is not complete unless applicable items below are verified:

- camera capture works
- payload reaches backend
- backend successfully calls Python services
- behavior events are produced
- reminders can be triggered/generated
- end-of-day reporting works
- chatbot can answer from real tracked data
- Docker runtime still works
- frontend still loads and displays results correctly

---

## Safety and honesty rules

- Do not claim medical certainty.
- Do not overstate smoking detection confidence.
- Prefer confidence-based outputs and transparent limitations.
- Do not fabricate missing integrations or data.

---

## If uncertain

If requirements are ambiguous, choose the most practical implementation that:
- preserves current architecture,
- improves the end-to-end behavior-analysis flow,
- stays within the current project scope,
- and avoids unnecessary repo-wide refactors.