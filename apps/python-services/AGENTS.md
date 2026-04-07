# AGENTS.md

## Scope

This directory contains Python microservices only.

Focus on:
- computer vision services
- higher-level AI service adapters
- structured service APIs
- internal Python service modularity
- container readiness
- integration with backend services

Do not move frontend logic here.
Do not move backend business orchestration here.

---

## Current priorities

Highest priority:
- vision-service correctness
- ai-service correctness
- analysis contracts with backend
- structured outputs
- container/runtime stability

Do not spend time on unrelated experimental Python modules unless they block current behavior-analysis flows.

---

## Python service rules

1. Keep services separated by responsibility.
2. Keep routes thin.
3. Keep processing logic in service modules.
4. Return structured JSON.
5. Keep environment-based configuration.
6. Keep health endpoints useful but do not mistake them for full feature correctness.
7. Avoid embedding business orchestration that belongs in backend services.

---

## Required service split

### vision-service
Responsible for:
- image/frame ingestion
- preprocessing
- pose/motion/gesture analysis
- structured behavior detections

### ai-service
Responsible for:
- higher-level interpretation
- chat/reasoning support
- external AI API provider integration
- normalized structured responses

---

## Completion checklist

A Python service task is not complete unless:
- request contracts from backend are correct
- main analysis endpoints work, not just `/health`
- outputs are structured and usable by backend
- Docker runtime still works