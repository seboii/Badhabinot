"""Faz 4 — Eğitilmiş modelin tahminini + XAI + kişisel baseline'ı yapılandırılmış
bir BehavioralInsight'a dönüştürür.

Bu insight, ham olay verisi yerine LLM koçluğuna **veriye dayalı, kişiselleştirilmiş**
bir sinyal olarak geçer. Backend tarafındaki TemporalPatternAnalyzer zaman boyutunu
ekler; bu modül ise tek bir dizi (window) için anlık bir özet üretir.

Tezin "multimodal füzyon" anlatısının vision tarafıdır.

Kullanım:
    from training.insights import build_insight
    digest = build_insight(
        predicted_label="smoking_like_gesture",
        confidence=0.81,
        top_features=[("hand0_near_mouth", 0.92), ("mar", 0.34)],
        anomaly_score=2.3,
        top_deviations=[("kp_left_wrist_y", 3.1)],
    )
    payload = digest.to_dict()   # LLM'e gönderilecek JSON
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


def _intensity_from_confidence(confidence: float) -> str:
    if confidence >= 0.75:
        return "yuksek"
    if confidence >= 0.50:
        return "orta"
    return "dusuk"


def _anomaly_label(score: float) -> str:
    """Welford z-skorunu insan-okunur etikete çevirir."""
    if score >= 3.0:
        return "ciddi sapma"
    if score >= 2.0:
        return "normal-disi"
    if score >= 1.0:
        return "sinirda"
    return "normal aralik"


@dataclass
class BehavioralInsight:
    """Tek bir pencere için yapılandırılmış davranış özeti."""

    predicted_label: str
    confidence: float
    confidence_label: str               # yuksek | orta | dusuk
    top_features: list[tuple[str, float]] = field(default_factory=list)
    anomaly_score: float = 0.0
    anomaly_label: str = "normal aralik"   # normal | sinirda | normal-disi | ciddi
    top_deviations: list[tuple[str, float]] = field(default_factory=list)
    summary_tr: str = ""                # LLM'in doğrudan kullanabileceği TR cümle

    def to_dict(self) -> dict:
        return {
            "predicted_label": self.predicted_label,
            "confidence": round(float(self.confidence), 4),
            "confidence_label": self.confidence_label,
            "top_features": [(name, round(float(score), 4)) for name, score in self.top_features],
            "anomaly_score": round(float(self.anomaly_score), 4),
            "anomaly_label": self.anomaly_label,
            "top_deviations": [(name, round(float(score), 4)) for name, score in self.top_deviations],
            "summary_tr": self.summary_tr,
        }


def build_insight(
    predicted_label: str,
    confidence: float,
    top_features: Iterable[tuple[str, float]] | None = None,
    anomaly_score: float = 0.0,
    top_deviations: Iterable[tuple[str, float]] | None = None,
) -> BehavioralInsight:
    """Faz 2 (model) + Faz 3 (XAI + baseline) çıktısından özet üretir.

    predicted_label: SequencePredictor.predict() sonucu.
    confidence: aynı tahminin sınıf olasılığı.
    top_features: SaliencyExplainer.explain().top_features.
    anomaly_score: UserBaseline.anomaly_score().
    top_deviations: UserBaseline.top_deviations().
    """
    features = list(top_features or [])
    deviations = list(top_deviations or [])

    confidence_label = _intensity_from_confidence(confidence)
    anomaly_label = _anomaly_label(anomaly_score)

    parts: list[str] = []
    if predicted_label and predicted_label != "normal":
        parts.append(
            f"Tahmin: {predicted_label} ({confidence_label} guven, %{round(confidence * 100)})"
        )
    else:
        parts.append(f"Tahmin: normal davranis (guven %{round(confidence * 100)})")
    if features:
        names = ", ".join(name for name, _ in features[:3])
        parts.append(f"En etkili sinyaller: {names}")
    if anomaly_score > 0:
        parts.append(f"Kisisel baseline: {anomaly_label} (|z|={anomaly_score:.2f})")
    if deviations:
        dev_names = ", ".join(name for name, _ in deviations[:3])
        parts.append(f"En sapma gosteren ozellikler: {dev_names}")

    return BehavioralInsight(
        predicted_label=predicted_label,
        confidence=float(confidence),
        confidence_label=confidence_label,
        top_features=features,
        anomaly_score=float(anomaly_score),
        anomaly_label=anomaly_label,
        top_deviations=deviations,
        summary_tr=". ".join(parts) + ".",
    )
