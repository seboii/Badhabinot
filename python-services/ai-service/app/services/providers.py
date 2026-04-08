import asyncio
import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlparse

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
            return ProviderReadiness(
                False,
                {
                    "provider": self.config.provider_name,
                    "model": self.config.model_name,
                    "mode": "invalid_configuration",
                    "provider_status": "misconfigured",
                    "reason": str(exc),
                },
            )

        return ProviderReadiness(
            True,
            {
                "provider": self.config.provider_name,
                "model": self.config.model_name,
                "mode": "external_api",
                "provider_status": "configured",
            },
        )

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
                    status_code, message = self._map_http_status(exc.response.status_code)
                    raise ProviderInvocationError(
                        message,
                        status_code=status_code,
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
        parsed = urlparse(self.config.api_base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ProviderConfigurationError("AI_API_BASE_URL must be a valid http or https URL")
        if not self.config.api_key:
            raise ProviderConfigurationError("AI_API_KEY is required for the external provider")
        if not self.config.model_name:
            raise ProviderConfigurationError("AI_MODEL_NAME is required for the external provider")

    def _map_http_status(self, status_code: int) -> tuple[int, str]:
        if status_code in {401, 403}:
            return 503, f"external AI provider authentication failed with HTTP {status_code}"
        if status_code == 429:
            return 503, "external AI provider rate limit exceeded"
        return 502, f"external AI provider returned HTTP {status_code}"

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
                        "You are a behavior-insights assistant for one authenticated user. "
                        "Use only the supplied structured monitoring context and chat history. "
                        "Never invent counts, events, times, trends, or comparisons. "
                        "If information is missing, say that clearly. "
                        "Treat smoking signals as confidence-based cues, not certainty. "
                        "When useful, separate your answer into: facts, interpretation, and practical next steps. "
                        "Return JSON only with keys answer, grounded_facts, follow_up_suggestions. "
                        "grounded_facts must contain short, directly verifiable points from context values."
                    ),
                },
                *history_lines,
                {
                    "role": "user",
                    "content": (
                        f"User timezone: {request.timezone or 'UTC'}\n"
                        f"Report date: {request.report_date.isoformat()}\n"
                        "Use the comparison and trend fields when the question asks about change over time.\n"
                        "If `data_gaps` is non-empty and relevant, mention the limitation.\n"
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
        if not grounded_facts:
            grounded_facts = [
                f"Hydration: {request.context.hydration_progress_ml}/{request.context.water_goal_ml} ml.",
                f"Posture alerts: {request.context.posture_alert_count}.",
                f"Smoking-like cues: {request.context.smoking_like_count}.",
            ]
        if not follow_up_suggestions:
            follow_up_suggestions = [
                "Which trend should I prioritize tomorrow?",
                "Show the main risk pattern for this report date.",
                "Compare hydration and posture against the previous day.",
            ]

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
        question = request.message.lower().strip()
        context = request.context
        top_event = max(context.recent_event_type_counts.items(), key=lambda item: item[1], default=("none", 0))
        hydration_ratio = 0.0 if context.water_goal_ml <= 0 else context.hydration_progress_ml / context.water_goal_ml
        hydration_percent = round(hydration_ratio * 100)
        event_summary = ", ".join(
            f"{event_type}: {count}" for event_type, count in list(context.recent_event_type_counts.items())[:3]
        ) or "no recent events"
        data_gap_note = (
            f" Data limitations: {context.data_gaps[0]}"
            if context.data_gaps
            else ""
        )

        asks_for_summary = any(term in question for term in ["summary", "summarize", "day", "gun", "ozet", "bugun"])
        asks_for_comparison = any(term in question for term in ["compare", "comparison", "trend", "before", "kar", "gecmis", "onceki"])
        asks_for_posture = any(term in question for term in ["posture", "slouch", "lean", "durus"])
        asks_for_hydration = any(term in question for term in ["water", "drink", "hydration", "su"])
        asks_for_smoking = any(term in question for term in ["smok", "risky", "sigara"])
        asks_for_most_often = any(term in question for term in ["most often", "most", "en cok", "tekrar"])

        if asks_for_hydration:
            answer = (
                f"On {request.report_date.isoformat()}, hydration reached {context.hydration_progress_ml} / "
                f"{context.water_goal_ml} ml ({hydration_percent}%). "
                f"In the last 7 days, hydration logs totaled {context.hydration_last_7_days_ml} ml.{data_gap_note}"
            )
        elif asks_for_posture:
            answer = (
                f"Poor posture alerts were {context.posture_alert_count} for {request.report_date.isoformat()}, "
                f"and poor-posture frames were about {round(context.poor_posture_ratio * 100)}% of analyzed captures. "
                f"{context.comparison_to_previous_day}{data_gap_note}"
            )
        elif asks_for_smoking:
            answer = (
                f"Smoking-like cues were recorded {context.smoking_like_count} times on {request.report_date.isoformat()}. "
                "These are confidence-based cues and should not be treated as certain smoking confirmation. "
                f"{context.comparison_to_previous_day}{data_gap_note}"
            )
        elif asks_for_most_often:
            answer = (
                f"The most frequent recent event type is '{top_event[0]}' with {top_event[1]} occurrences "
                f"in the available recent event window. Event breakdown: {event_summary}.{data_gap_note}"
            )
        elif asks_for_comparison:
            answer = (
                f"Comparison for {request.report_date.isoformat()}: {context.comparison_to_previous_day} "
                f"Across the last 7 days, analyses completed: {context.analyses_completed_last_7_days}, "
                f"sessions: {context.total_sessions_last_7_days}, "
                f"session time: {context.total_session_minutes_last_7_days} minutes.{data_gap_note}"
            )
        elif asks_for_summary or not question:
            answer = (
                f"Summary for {request.report_date.isoformat()}: {context.summary} "
                f"Hydration is {context.hydration_progress_ml}/{context.water_goal_ml} ml, "
                f"posture alerts: {context.posture_alert_count}, hand movement events: {context.hand_movement_count}, "
                f"smoking-like cues: {context.smoking_like_count}. "
                f"Recent event breakdown: {event_summary}.{data_gap_note}"
            )
        else:
            answer = (
                f"{context.summary} "
                f"For direct grounding: hydration {context.hydration_progress_ml}/{context.water_goal_ml} ml, "
                f"posture alerts {context.posture_alert_count}, smoking-like cues {context.smoking_like_count}. "
                f"{context.comparison_to_previous_day}{data_gap_note}"
            )

        facts = [
            f"Hydration reached {context.hydration_progress_ml} of {context.water_goal_ml} ml.",
            f"Posture alerts recorded: {context.posture_alert_count}.",
            f"Hand movement events recorded: {context.hand_movement_count}.",
            f"Smoking-like cues recorded: {context.smoking_like_count}.",
            context.comparison_to_previous_day,
        ]

        follow_up = [
            "Compare today with the previous report in more detail.",
            "Show which event type repeated most in the recent window.",
            "List practical improvements for posture, hydration, and smoking-like cues.",
        ]
        if context.data_gaps:
            follow_up[2] = "Tell me what is missing in my data and how to improve coverage."

        return ChatProviderResult(
            answer=answer,
            grounded_facts=[fact for fact in facts if fact][:5],
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
