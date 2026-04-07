import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.schemas.analysis import AllowedBehavior, AnalysisRequest
from app.schemas.chat import ChatRequest


class ProviderConfigurationError(RuntimeError):
    pass


class ProviderInvocationError(RuntimeError):
    def __init__(self, message: str, *, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ProviderConfig:
    provider_name: str
    api_base_url: str
    api_key: str
    model_name: str
    timeout_seconds: float
    readiness_timeout_seconds: float
    max_retries: int
    temperature: float


@dataclass(frozen=True)
class ProviderReadiness:
    ready: bool
    details: dict[str, Any]


@dataclass(frozen=True)
class ProviderResult:
    behavior_type: AllowedBehavior
    confidence: float
    scores: dict[str, float]
    summary: str
    recommendation: str
    grounded_facts: list[str]
    provider: str
    model_name: str
    model_mode: str


@dataclass(frozen=True)
class ChatProviderResult:
    answer: str
    grounded_facts: list[str]
    follow_up_suggestions: list[str]
    provider: str
    model_name: str
    model_mode: str


class AnalysisProvider(Protocol):
    async def analyze(self, request: AnalysisRequest) -> ProviderResult:
        ...

    async def respond_chat(self, request: ChatRequest) -> ChatProviderResult:
        ...

    async def readiness(self) -> ProviderReadiness:
        ...


class OpenAiCompatibleProvider:
    def __init__(self, config: ProviderConfig, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.config = config
        self.transport = transport

    async def analyze(self, request: AnalysisRequest) -> ProviderResult:
        self._validate_configuration()
        payload = self._build_analysis_payload(request)
        response_json = await self._post_with_retry("/chat/completions", payload)
        return self._normalize_analysis_response(request, response_json)

    async def respond_chat(self, request: ChatRequest) -> ChatProviderResult:
        self._validate_configuration()
        payload = self._build_chat_payload(request)
        response_json = await self._post_with_retry("/chat/completions", payload)
        return self._normalize_chat_response(request, response_json)

    async def readiness(self) -> ProviderReadiness:
        try:
            self._validate_configuration()
        except ProviderConfigurationError as exc:
            return ProviderReadiness(False, {"provider": self.config.provider_name, "reason": str(exc)})

        try:
            async with self._client(timeout_seconds=self.config.readiness_timeout_seconds) as client:
                response = await client.get("/models", headers=self._headers())
                response.raise_for_status()
            return ProviderReadiness(True, {"provider": self.config.provider_name, "model": self.config.model_name})
        except httpx.TimeoutException:
            return ProviderReadiness(False, {"provider": self.config.provider_name, "reason": "provider readiness timed out"})
        except httpx.HTTPStatusError as exc:
            return ProviderReadiness(
                False,
                {
                    "provider": self.config.provider_name,
                    "reason": f"provider readiness returned HTTP {exc.response.status_code}",
                },
            )
        except httpx.HTTPError as exc:
            return ProviderReadiness(False, {"provider": self.config.provider_name, "reason": str(exc)})

    async def _post_with_retry(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self._client(timeout_seconds=self.config.timeout_seconds) as client:
                    response = await client.post(path, json=payload, headers=self._headers())
                    response.raise_for_status()
                    return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    raise ProviderInvocationError("external AI provider timed out", status_code=504) from exc
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if not self._is_retryable_status(exc.response.status_code) or attempt >= self.config.max_retries:
                    raise ProviderInvocationError(
                        f"external AI provider returned HTTP {exc.response.status_code}",
                        status_code=502,
                    ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt >= self.config.max_retries:
                    raise ProviderInvocationError("external AI provider is unavailable", status_code=502) from exc

            await asyncio.sleep(0.35 * (2**attempt))

        raise ProviderInvocationError("external AI provider request failed", status_code=502) from last_error

    def _client(self, *, timeout_seconds: float) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.config.api_base_url,
            timeout=httpx.Timeout(timeout_seconds),
            transport=self.transport,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        }

    def _validate_configuration(self) -> None:
        if not self.config.api_base_url:
            raise ProviderConfigurationError("AI_API_BASE_URL is required for the external provider")
        if not self.config.api_key:
            raise ProviderConfigurationError("AI_API_KEY is required for the external provider")
        if not self.config.model_name:
            raise ProviderConfigurationError("AI_MODEL_NAME is required for the external provider")

    def _build_analysis_payload(self, request: AnalysisRequest) -> dict[str, Any]:
        context = {
            "request_id": request.request_id,
            "captured_at": request.captured_at.isoformat(),
            "timezone": request.timezone or "UTC",
            "sensitivity": request.settings.sensitivity,
            "vision": request.vision.model_dump(mode="json"),
        }

        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "Analyze the structured vision data for behavior monitoring. "
                    "Return JSON only with keys behavior_type, confidence, scores, summary, recommendation, grounded_facts. "
                    "behavior_type must be one of none, hand_movement_pattern, smoking_like_gesture. "
                    "scores must contain hand_movement_pattern and smoking_like_gesture values between 0 and 1. "
                    "grounded_facts must be a short array of statements directly supported by the vision signals. "
                    "Do not claim certainty for smoking; describe it as smoking-like when applicable.\n"
                    f"Context:\n{json.dumps(context, ensure_ascii=True)}"
                ),
            }
        ]

        if request.image_base64 and request.image_content_type:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{request.image_content_type};base64,{request.image_base64}",
                    },
                }
            )

        return {
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a production monitoring assistant. "
                        "You classify only the requested behavior categories and stay conservative."
                    ),
                },
                {
                    "role": "user",
                    "content": content,
                },
            ],
        }

    def _build_chat_payload(self, request: ChatRequest) -> dict[str, Any]:
        context = request.context.model_dump(mode="json")
        history_lines = [
            {
                "role": item.role,
                "content": item.content,
            }
            for item in request.history[-10:]
        ]

        return {
            "model": self.config.model_name,
            "temperature": min(self.config.temperature + 0.05, 0.3),
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You answer only from the provided user behavior context. "
                        "Return JSON only with keys answer, grounded_facts, follow_up_suggestions. "
                        "If the context does not support a claim, say that explicitly."
                    ),
                },
                *history_lines,
                {
                    "role": "user",
                    "content": (
                        f"User timezone: {request.timezone or 'UTC'}\n"
                        f"Report date: {request.report_date.isoformat()}\n"
                        f"Grounding context:\n{json.dumps(context, ensure_ascii=True)}\n"
                        f"Question: {request.message}"
                    ),
                },
            ],
        }

    def _normalize_analysis_response(self, request: AnalysisRequest, payload: dict[str, Any]) -> ProviderResult:
        raw_content = self._extract_content(payload)
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ProviderInvocationError("external AI provider returned invalid JSON", status_code=502) from exc

        scores = {
            "hand_movement_pattern": self._clamp(parsed.get("scores", {}).get("hand_movement_pattern", 0.0)),
            "smoking_like_gesture": self._clamp(parsed.get("scores", {}).get("smoking_like_gesture", 0.0)),
        }

        behavior_type = str(parsed.get("behavior_type", "none")).strip().lower()
        if behavior_type not in {"none", "hand_movement_pattern", "smoking_like_gesture"}:
            behavior_type = max(scores, key=scores.get) if max(scores.values()) >= 0.5 else "none"

        confidence = self._clamp(parsed.get("confidence", scores.get(behavior_type, max(scores.values()))))
        summary = str(parsed.get("summary") or self._default_summary(behavior_type, request)).strip()
        recommendation = str(parsed.get("recommendation") or self._default_recommendation(behavior_type, request)).strip()
        grounded_facts = [str(item).strip() for item in parsed.get("grounded_facts", []) if str(item).strip()][:4]

        return ProviderResult(
            behavior_type=behavior_type,
            confidence=confidence,
            scores=scores,
            summary=summary,
            recommendation=recommendation,
            grounded_facts=grounded_facts,
            provider=self.config.provider_name,
            model_name=self.config.model_name,
            model_mode="external_api",
        )

    def _normalize_chat_response(self, request: ChatRequest, payload: dict[str, Any]) -> ChatProviderResult:
        raw_content = self._extract_content(payload)
        try:
            parsed = json.loads(raw_content)
        except json.JSONDecodeError as exc:
            raise ProviderInvocationError("external AI provider returned invalid chat JSON", status_code=502) from exc

        answer = str(parsed.get("answer") or "").strip()
        if not answer:
            answer = (
                "The available tracked data was not sufficient for a stronger answer. "
                "Try asking about posture, hydration, reminders, or smoking-like cues for the report date."
            )
        grounded_facts = [str(item).strip() for item in parsed.get("grounded_facts", []) if str(item).strip()][:5]
        follow_up_suggestions = [
            str(item).strip()
            for item in parsed.get("follow_up_suggestions", [])
            if str(item).strip()
        ][:3]

        return ChatProviderResult(
            answer=answer,
            grounded_facts=grounded_facts,
            follow_up_suggestions=follow_up_suggestions,
            provider=self.config.provider_name,
            model_name=self.config.model_name,
            model_mode="external_api",
        )

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderInvocationError("external AI provider returned no choices", status_code=502)

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            combined = "".join(parts).strip()
            if combined:
                return combined
        raise ProviderInvocationError("external AI provider returned an empty message", status_code=502)

    def _default_summary(self, behavior_type: AllowedBehavior, request: AnalysisRequest) -> str:
        if behavior_type == "hand_movement_pattern":
            return "The current frame and temporal context suggest a repeated hand movement pattern."
        if behavior_type == "smoking_like_gesture":
            return "The current frame suggests a smoking-like hand-to-mouth gesture, but it should be treated as a cue rather than certainty."
        if request.vision.posture_state == "poor":
            return "No smoking-like or repetitive hand event dominated the frame, but posture still needs correction."
        return "No high-confidence risky behavior dominated this frame."

    def _default_recommendation(self, behavior_type: AllowedBehavior, request: AnalysisRequest) -> str:
        if behavior_type == "hand_movement_pattern":
            return "Suggest a short reset and move the hands away from the face or work trigger."
        if behavior_type == "smoking_like_gesture":
            return "Suggest a brief pause and confirm the trigger behind the smoking-like gesture."
        if request.vision.posture_state == "poor":
            return "Prompt the user to reset posture before continuing."
        return "Continue monitoring and compare with another frame if behavior changes."

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code == 429 or status_code >= 500

    def _clamp(self, value: Any) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = 0.0
        return max(0.0, min(1.0, round(numeric, 4)))


class MockProvider:
    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    async def analyze(self, request: AnalysisRequest) -> ProviderResult:
        threshold_map = {
            "LOW": 0.64,
            "MEDIUM": 0.54,
            "HIGH": 0.46,
        }
        threshold = threshold_map[request.settings.sensitivity]
        signals = request.vision.signals
        detections = {item.event_type: item for item in request.vision.detections}

        hand_score = max(
            float(detections.get("hand_movement_pattern").confidence) if "hand_movement_pattern" in detections else 0.0,
            min(
                1.0,
                signals.hand_motion_score * 0.45
                + signals.repetitive_motion_score * 0.35
                + signals.hand_face_proximity_score * 0.20,
            ),
        )
        smoking_score = max(
            float(detections.get("smoking_like_gesture").confidence) if "smoking_like_gesture" in detections else 0.0,
            min(
                1.0,
                signals.smoking_gesture_score * 0.55
                + signals.elongated_object_score * 0.25
                + signals.hand_face_proximity_score * 0.20,
            ),
        )

        behavior_type: AllowedBehavior = "none"
        confidence = max(hand_score, smoking_score)
        if smoking_score >= threshold and smoking_score >= hand_score:
            behavior_type = "smoking_like_gesture"
            confidence = smoking_score
        elif hand_score >= threshold:
            behavior_type = "hand_movement_pattern"
            confidence = hand_score

        grounded_facts = []
        if request.vision.posture_state == "poor":
            grounded_facts.append(
                f"Poor posture state was reported with posture risk score {signals.posture_risk_score:.2f}."
            )
        if signals.hand_motion_score > 0:
            grounded_facts.append(f"Hand motion score reached {signals.hand_motion_score:.2f}.")
        if signals.smoking_gesture_score > 0:
            grounded_facts.append(f"Smoking-like gesture score reached {signals.smoking_gesture_score:.2f}.")

        return ProviderResult(
            behavior_type=behavior_type,
            confidence=round(confidence, 4),
            scores={
                "hand_movement_pattern": round(hand_score, 4),
                "smoking_like_gesture": round(smoking_score, 4),
            },
            summary=self._analysis_summary(behavior_type, request),
            recommendation=self._analysis_recommendation(behavior_type, request),
            grounded_facts=grounded_facts[:4],
            provider="mock",
            model_name=self.config.model_name,
            model_mode="mock",
        )

    async def respond_chat(self, request: ChatRequest) -> ChatProviderResult:
        question = request.message.lower()
        context = request.context
        facts = [
            f"Hydration reached {context.hydration_progress_ml} of {context.water_goal_ml} ml.",
            f"Posture alerts recorded: {context.posture_alert_count}.",
            f"Smoking-like cues recorded: {context.smoking_like_count}.",
            f"Hand movement events recorded: {context.hand_movement_count}.",
        ]

        if "water" in question or "drink" in question or "hydration" in question:
            answer = (
                f"You logged {context.hydration_progress_ml} ml out of the {context.water_goal_ml} ml goal "
                f"for {request.report_date.isoformat()}."
            )
        elif "posture" in question or "lean" in question or "slouch" in question:
            answer = (
                f"Poor posture was flagged {context.posture_alert_count} times, and poor-posture frames made up "
                f"about {round(context.poor_posture_ratio * 100)}% of analyzed captures."
            )
        elif "smok" in question or "risky" in question:
            answer = (
                f"The system recorded {context.smoking_like_count} smoking-like cues on {request.report_date.isoformat()}. "
                "These are confidence-based cues rather than certain smoking confirmation."
            )
        elif "hand" in question:
            answer = (
                f"The monitoring data recorded {context.hand_movement_count} repetitive hand-movement events "
                f"for {request.report_date.isoformat()}."
            )
        else:
            answer = context.summary

        follow_up = [
            "Ask whether posture or hydration needs the most attention.",
            "Ask when the highest-confidence cues happened.",
            "Ask which recommendation matters most tomorrow.",
        ]

        return ChatProviderResult(
            answer=answer,
            grounded_facts=facts[:4],
            follow_up_suggestions=follow_up,
            provider="mock",
            model_name=self.config.model_name,
            model_mode="mock",
        )

    async def readiness(self) -> ProviderReadiness:
        return ProviderReadiness(True, {"provider": "mock", "model": self.config.model_name})

    def _analysis_summary(self, behavior_type: AllowedBehavior, request: AnalysisRequest) -> str:
        if behavior_type == "hand_movement_pattern":
            return "Mock provider detected a repeated hand movement pattern from the current signals."
        if behavior_type == "smoking_like_gesture":
            return "Mock provider detected a smoking-like gesture from the current signals."
        if request.vision.posture_state == "poor":
            return "Mock provider did not classify a dominant risky gesture, but posture still needs attention."
        return "Mock provider did not find a dominant risky behavior in this frame."

    def _analysis_recommendation(self, behavior_type: AllowedBehavior, request: AnalysisRequest) -> str:
        if behavior_type == "hand_movement_pattern":
            return "Take a short reset and keep the hands away from the face or trigger object."
        if behavior_type == "smoking_like_gesture":
            return "Treat this as a smoking-like cue and confirm it with another frame before escalating."
        if request.vision.posture_state == "poor":
            return "Reset posture and run another frame to check if alignment improves."
        return "Continue monitoring with another frame if the behavior changes."
