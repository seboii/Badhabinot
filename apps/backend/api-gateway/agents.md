# AGENTS.md

## Scope

This directory is responsible only for API gateway concerns.

Focus on:
- routing
- path forwarding
- auth propagation if required
- CORS
- gateway-level resilience only where needed
- correct routing from frontend-facing URLs to backend services

Do not implement domain business logic here.

---

## Current priorities

Ensure the gateway does not block the behavior-analysis product flow.

Critical routes to verify:
- auth routes
- analysis routes
- reminder routes
- report routes
- chatbot routes

If the frontend depends on the gateway, these routes must be correct before other gateway refinements.

---

## Rules

1. Keep gateway thin.
2. Do not duplicate backend orchestration here.
3. Keep route configuration explicit.
4. Verify service discovery / internal URLs match Docker service names.
5. Verify CORS and forwarded headers if browser access depends on them.
6. Prioritize working end-to-end routing over advanced gateway features.

---

## Completion checklist

A gateway task is not complete unless:
- frontend can reach required backend APIs through the gateway
- analysis-related routes are correct
- report/reminder/chat routes are correct
- no incorrect localhost assumptions exist inside containers