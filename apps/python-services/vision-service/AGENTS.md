# AGENTS.md

## Scope

This directory is responsible only for computer vision and structured behavior detection.

Focus on:
- frame/image parsing
- pose/landmark extraction
- posture detection
- hand movement analysis
- smoking-like gesture analysis
- normalized detection output schemas
- health and analysis endpoints

Do not move business orchestration logic here.
Do not move report generation here.
Do not move chatbot orchestration here.

## Rules

1. Keep routes thin.
2. Keep analysis logic in service modules.
3. Return structured JSON.
4. Do not return vague free-form text as the primary machine output.
5. Use confidence-based outputs.
6. Keep detectors modular and swappable.
7. Do not make `/health` success the only indicator of service correctness.
8. Add or fix real analysis endpoints before polishing internals.