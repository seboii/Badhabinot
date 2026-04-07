# AGENTS.md

## Scope

This directory is responsible for the web frontend only.

Focus on:
- camera permission and capture UI
- dashboard and analysis views
- reminders UI
- reports UI
- chatbot UI
- routing
- state management
- API integration with backend
- dark mode / light mode
- loading / error / empty states

Do not move backend orchestration logic here.
Do not implement business rules only in the frontend if they belong in backend services.

---

## Current frontend priorities

The frontend must make the behavior-analysis system usable.

Highest-priority flows:
1. camera access
2. frame/image capture
3. analysis request submission
4. live or near-real-time result rendering
5. reminder display
6. daily report display
7. chatbot interaction using backend APIs

Do not spend time on unrelated pages until these flows work.

---

## Must-have pages and areas

Prioritize these pages/routes:
- login if auth exists
- dashboard
- live camera / analysis page
- events/history page
- reminders/settings page
- daily report page
- chatbot page or chatbot panel

If some pages are missing, create them.
If some exist but are empty or broken, complete them.

---

## Frontend architecture rules

1. Frontend calls backend APIs only.
2. Do not call database, Redis, or Python services directly from frontend.
3. Keep API client logic centralized.
4. Keep route structure clear and scalable.
5. Keep camera components separated from generic UI components.
6. Keep chatbot UI separate from general dashboard logic.
7. Keep theme logic centralized.
8. Avoid giant page files.

Preferred separation:
- app shell / layout
- feature modules
- shared UI primitives
- API layer
- hooks
- route definitions
- theme provider
- typed models

---

## Camera flow rules

When debugging or implementing camera behavior, always validate:

1. browser camera permission request
2. media stream acquisition
3. video preview rendering
4. frame capture timing
5. payload format
6. backend endpoint target
7. error state handling
8. result rendering
9. retry / reconnect behavior

Do not consider the camera flow done if only video preview works.
The full analysis request/response path must work.

---

## UI requirements

The UI must be real and usable, not a placeholder.

Must include:
- clear layout
- usable navigation
- visible analysis status
- result cards / tables / timelines
- error messages that help debugging
- empty states
- loading states
- responsive behavior
- theme toggle

Do not leave fake data if real backend integration is possible.

---

## Theme rules

This app must support dark mode and light mode professionally.

Requirements:
- centralized theme provider or equivalent
- consistent theme tokens
- readable contrast
- persisted preference if appropriate
- no one-off hardcoded dark styles scattered everywhere

---

## Chatbot rules

The chatbot UI must not be generic-only.

It must:
- call backend chat endpoints
- display behavior-grounded answers
- support follow-up messages
- clearly show loading/error states
- avoid pretending to know data the system has not recorded

---

## Frontend file-reading discipline

Read these first when working here:
- camera page/component
- API client / query layer
- route definitions
- auth/session layer if present
- dashboard page
- chatbot page/component
- report page/component
- theme provider
- env config

Read unrelated marketing/admin pages only if they block the main flow.

---

## Completion checklist

A frontend task is not complete unless applicable items are verified:

- camera opens
- capture works
- payload reaches backend
- results are displayed
- reminders appear
- daily report renders
- chatbot works through backend
- dark/light mode works
- Docker-based frontend run still works