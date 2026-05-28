"""training.insights — saf Python, her zaman çalışır.

Confidence/anomaly etiketlerinin doğru kategorize edildiğini, TR özet
cümlesinin etkili sinyalleri içerdiğini ve to_dict çıktısının
JSON-serileştirilebilir yuvarlanmış sayılar ürettiğini doğrular.
"""

from __future__ import annotations

import json

from training.insights import BehavioralInsight, build_insight


def test_high_confidence_classification_produces_high_label() -> None:
    insight = build_insight(
        predicted_label="smoking_like_gesture",
        confidence=0.88,
        top_features=[("hand0_near_mouth", 0.92), ("mar", 0.34)],
    )
    assert insight.confidence_label == "yuksek"
    assert "smoking_like_gesture" in insight.summary_tr
    assert "hand0_near_mouth" in insight.summary_tr


def test_low_confidence_produces_low_label() -> None:
    insight = build_insight(predicted_label="normal", confidence=0.30)
    assert insight.confidence_label == "dusuk"
    assert "normal davranis" in insight.summary_tr


def test_anomaly_score_categorization() -> None:
    assert build_insight("x", 0.6, anomaly_score=0.5).anomaly_label == "normal aralik"
    assert build_insight("x", 0.6, anomaly_score=1.3).anomaly_label == "sinirda"
    assert build_insight("x", 0.6, anomaly_score=2.5).anomaly_label == "normal-disi"
    assert build_insight("x", 0.6, anomaly_score=3.5).anomaly_label == "ciddi sapma"


def test_summary_mentions_anomaly_and_deviations_when_present() -> None:
    insight = build_insight(
        predicted_label="hand_movement_pattern",
        confidence=0.66,
        top_features=[("hand0_near_face", 0.9)],
        anomaly_score=2.4,
        top_deviations=[("kp_left_wrist_y", 3.1), ("face_touch_detected", 2.6)],
    )
    assert "Kisisel baseline" in insight.summary_tr
    assert "kp_left_wrist_y" in insight.summary_tr


def test_to_dict_is_json_serializable_with_rounded_floats() -> None:
    insight = build_insight(
        predicted_label="poor_posture",
        confidence=0.4123456789,
        top_features=[("posture_score", 0.7891234)],
        anomaly_score=1.9876543,
        top_deviations=[("spine_tilt_angle", 2.5550009)],
    )
    payload = insight.to_dict()
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["predicted_label"] == "poor_posture"
    assert decoded["confidence"] == 0.4123
    assert decoded["top_features"][0] == ["posture_score", 0.7891]
    assert decoded["anomaly_score"] == 1.9877
    assert decoded["top_deviations"][0] == ["spine_tilt_angle", 2.555]


def test_default_empty_collections() -> None:
    insight = build_insight("normal", 0.7)
    assert insight.top_features == []
    assert insight.top_deviations == []
    assert insight.anomaly_score == 0.0


def test_dataclass_can_be_constructed_directly() -> None:
    insight = BehavioralInsight(
        predicted_label="x",
        confidence=0.5,
        confidence_label="orta",
    )
    assert insight.top_features == []
    assert insight.summary_tr == ""
