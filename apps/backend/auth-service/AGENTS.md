# AGENTS.md

## Scope

This directory is responsible only for authentication and authorization concerns.

Focus on:
- login/session/token flows
- user identity
- route protection support
- auth-related DTOs and persistence
- frontend auth compatibility

Do not turn this service into a general user-behavior orchestration service.

---

## Current priorities

Only work here if auth is blocking the main behavior-analysis flow.

Examples:
- frontend cannot log in
- backend analysis endpoints are unreachable due to auth mismatch
- gateway auth propagation is broken
- user identity is not available for event/report/chat grounding

If auth is not blocking current scope, do not over-refactor this service.

---

## Rules

1. Keep auth concerns isolated.
2. Avoid unrelated security redesigns.
3. Fix only what is necessary to support the current product flows.
4. Ensure user identity can be used safely by report/reminder/chat features.

---

## Completion checklist

A task here is not complete unless:
- login/auth flow still works
- protected analysis/report/chat endpoints remain usable
- user identity is available where required for grounding behavior data