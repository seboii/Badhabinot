"""Koçluk fine-tune veri seti şeması ve JSONL okuma/yazma.

Bir eğitim örneği =
    (persona, monitoring bağlamı, sohbet geçmişi, kullanıcı sorusu) → (ideal TR yanıt)

Bağlam alanları ÜRETİM ``ChatContext`` ile hizalıdır (ai-service/app/schemas/chat.py)
ki eğitim promptu çıkarım promptuyla birebir aynı olsun. Saf python (yalnızca
stdlib) — torch/transformers gerektirmez; birim testlerde her zaman koşar.

JSONL satır biçimi (her satır bir örnek):
    {
      "persona": "BEHAVIOR_COACH",
      "kind": "answer",                 # answer | refuse | casual
      "question": "Bugün duruşum nasıldı?",
      "ideal_answer": "Duruş skorun 78/100 ...",
      "context": { ...MonitoringContext... },
      "history": [{"role": "user", "content": "..."}, ...],
      "grounded_facts": ["Duruş skoru: 78/100", ...],
      "tags": ["posture", "gold"]
    }
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

# ── Sözlük sabitleri (üretimle uyumlu) ──────────────────────────────────────
PERSONAS = ("GENERAL_CHAT", "BEHAVIOR_COACH", "CUSTOM")
KINDS = ("answer", "refuse", "casual")  # data-yanıtı | gizlilik/sistem reddi | gündelik
TREND_LABELS = ("artiyor", "azaliyor", "stabil")
INTENSITY_LABELS = ("yogun", "orta", "az")


@dataclass
class BehavioralPattern:
    """Faz 4 — zaman serisi davranış örüntüsü (ChatContext.behavioral_patterns ile aynı)."""

    event_type: str
    peak_hour_of_day: int
    peak_hour_count: int
    peak_day_of_week: str
    peak_day_count: int
    total_count_last_7_days: int
    intensity_label: str
    trend_label: str

    def validate(self) -> None:
        if not 0 <= self.peak_hour_of_day <= 23:
            raise ValueError(f"peak_hour_of_day 0-23 olmalı: {self.peak_hour_of_day}")
        if self.trend_label not in TREND_LABELS:
            raise ValueError(f"trend_label geçersiz: {self.trend_label}")
        if self.intensity_label not in INTENSITY_LABELS:
            raise ValueError(f"intensity_label geçersiz: {self.intensity_label}")


@dataclass
class EventLite:
    """ChatContext.recent_events'in prompt'a giren alt kümesi (davranış olayı)."""

    event_type: str           # SLOUCHING | DROWSY | SMOKING | FACE_TOUCH | YAWNING | ...
    severity: str = "low"     # low | medium | high
    confidence: float = 0.0   # 0-1
    interpretation: str = ""
    occurred_hour: int = 12   # saat (0-23)


@dataclass
class ReminderLite:
    """ChatContext.recent_reminders'in prompt'a giren alt kümesi."""

    reminder_type: str        # hydration | exercise | posture | ...
    message: str = ""
    occurred_hour: int = 12


@dataclass
class MonitoringContext:
    """ChatContext'in prompt'a giren alt kümesi (üretim providers.py ile hizalı)."""

    report_date: str  # ISO: YYYY-MM-DD
    hydration_progress_ml: int = 0
    water_goal_ml: int = 2500
    poor_posture_ratio: float = 0.0
    posture_alert_count: int = 0
    smoking_like_count: int = 0
    hand_movement_count: int = 0
    analyses_completed: int = 0
    summary: str = ""
    comparison_to_previous_day: str = ""
    behavioral_patterns: list[BehavioralPattern] = field(default_factory=list)
    # ── Zengin sinyaller (programın gerçekten gönderdiği veri) ───────────────
    recent_events: list[EventLite] = field(default_factory=list)
    recent_reminders: list[ReminderLite] = field(default_factory=list)
    recent_event_type_counts: dict[str, int] = field(default_factory=dict)
    total_sessions_last_7_days: int = 0
    total_session_minutes_last_7_days: int = 0
    hydration_last_7_days_ml: int = 0
    analyses_completed_last_7_days: int = 0
    data_gaps: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not 0.0 <= self.poor_posture_ratio <= 1.0:
            raise ValueError(f"poor_posture_ratio 0-1 olmalı: {self.poor_posture_ratio}")
        if self.water_goal_ml < 0:
            raise ValueError("water_goal_ml negatif olamaz")
        for p in self.behavioral_patterns:
            p.validate()
        for e in self.recent_events:
            if not 0 <= e.occurred_hour <= 23:
                raise ValueError(f"occurred_hour 0-23 olmalı: {e.occurred_hour}")

    @classmethod
    def from_dict(cls, d: dict) -> "MonitoringContext":
        patterns = [BehavioralPattern(**p) for p in d.get("behavioral_patterns", [])]
        events = [EventLite(**e) for e in d.get("recent_events", [])]
        reminders = [ReminderLite(**r) for r in d.get("recent_reminders", [])]
        nested = {"behavioral_patterns", "recent_events", "recent_reminders"}
        known = {f for f in cls.__dataclass_fields__ if f not in nested}
        return cls(
            behavioral_patterns=patterns,
            recent_events=events,
            recent_reminders=reminders,
            **{k: v for k, v in d.items() if k in known},
        )


@dataclass
class ChatTurn:
    role: str  # user | assistant
    content: str


@dataclass
class CoachingExample:
    """Tek bir fine-tune örneği."""

    persona: str
    kind: str
    question: str
    ideal_answer: str
    context: MonitoringContext
    history: list[ChatTurn] = field(default_factory=list)
    grounded_facts: list[str] = field(default_factory=list)
    custom_system_prompt: str | None = None
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if self.persona not in PERSONAS:
            raise ValueError(f"persona geçersiz: {self.persona} (geçerli: {PERSONAS})")
        if self.kind not in KINDS:
            raise ValueError(f"kind geçersiz: {self.kind} (geçerli: {KINDS})")
        if not self.question.strip():
            raise ValueError("question boş olamaz")
        if not self.ideal_answer.strip():
            raise ValueError("ideal_answer boş olamaz")
        if self.persona == "CUSTOM" and not (self.custom_system_prompt or "").strip():
            raise ValueError("CUSTOM persona için custom_system_prompt gerekli")
        for t in self.history:
            if t.role not in ("user", "assistant"):
                raise ValueError(f"history role geçersiz: {t.role}")
        self.context.validate()

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "CoachingExample":
        return cls(
            persona=d["persona"],
            kind=d.get("kind", "answer"),
            question=d["question"],
            ideal_answer=d["ideal_answer"],
            context=MonitoringContext.from_dict(d.get("context", {"report_date": "1970-01-01"})),
            history=[ChatTurn(**t) for t in d.get("history", [])],
            grounded_facts=list(d.get("grounded_facts", [])),
            custom_system_prompt=d.get("custom_system_prompt"),
            tags=list(d.get("tags", [])),
        )


# ── JSONL G/Ç ───────────────────────────────────────────────────────────────
def load_jsonl(path: str | Path) -> list[CoachingExample]:
    """JSONL dosyasını yükler ve her örneği doğrular."""
    out: list[CoachingExample] = []
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                ex = CoachingExample.from_dict(json.loads(line))
                ex.validate()
            except Exception as exc:  # noqa: BLE001 — satır numarasıyla zenginleştir
                raise ValueError(f"{p}:{i} geçersiz örnek — {exc}") from exc
            out.append(ex)
    return out


def dump_jsonl(examples: list[CoachingExample], path: str | Path) -> int:
    """Örnekleri JSONL olarak yazar; yazılan satır sayısını döner."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for ex in examples:
            ex.validate()
            fh.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")
    return len(examples)


def dataset_stats(examples: list[CoachingExample]) -> dict[str, object]:
    """Persona/kind dağılımı + toplam — veri seti özeti (tez tablosu için)."""
    by_persona: dict[str, int] = {}
    by_kind: dict[str, int] = {}
    for ex in examples:
        by_persona[ex.persona] = by_persona.get(ex.persona, 0) + 1
        by_kind[ex.kind] = by_kind.get(ex.kind, 0) + 1
    return {"total": len(examples), "by_persona": by_persona, "by_kind": by_kind}
