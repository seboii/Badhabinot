"""evaluation.metrics doğruluğu — elle hesaplanmış değerlerle (ML gerektirmez)."""

from __future__ import annotations

import pytest

from evaluation.metrics import compute_report, confusion_matrix

LABELS = ["normal", "poor_posture", "hand_movement_pattern", "smoking_like_gesture"]


def test_confusion_matrix_counts_are_correct() -> None:
    y_true = ["normal", "normal", "poor_posture", "poor_posture"]
    y_pred = ["normal", "poor_posture", "poor_posture", "normal"]
    matrix = confusion_matrix(y_true, y_pred, ["normal", "poor_posture"])
    # satır = gerçek, sütun = tahmin
    assert matrix.tolist() == [[1, 1], [1, 1]]


def test_perfect_predictions_score_one() -> None:
    y_true = ["normal", "poor_posture", "smoking_like_gesture"]
    report = compute_report(y_true, list(y_true), LABELS)
    assert report.accuracy == pytest.approx(1.0)
    for c in report.per_class:
        if c.support > 0:
            assert c.precision == pytest.approx(1.0)
            assert c.recall == pytest.approx(1.0)
            assert c.f1 == pytest.approx(1.0)


def test_known_two_class_metrics() -> None:
    labels = ["normal", "poor_posture"]
    y_true = ["normal", "normal", "normal", "poor_posture", "poor_posture"]
    y_pred = ["normal", "normal", "poor_posture", "poor_posture", "normal"]
    report = compute_report(y_true, y_pred, labels)

    normal = next(c for c in report.per_class if c.label == "normal")
    poor = next(c for c in report.per_class if c.label == "poor_posture")

    assert normal.precision == pytest.approx(2 / 3)
    assert normal.recall == pytest.approx(2 / 3)
    assert poor.precision == pytest.approx(0.5)
    assert poor.recall == pytest.approx(0.5)
    assert report.accuracy == pytest.approx(0.6)
    assert report.macro_precision == pytest.approx((2 / 3 + 0.5) / 2)
    assert report.weighted_precision == pytest.approx(0.6)
    assert report.total_support == 5


def test_absent_class_yields_zero_not_nan() -> None:
    labels = ["normal", "poor_posture"]
    report = compute_report(["normal", "normal"], ["normal", "normal"], labels)
    poor = next(c for c in report.per_class if c.label == "poor_posture")
    assert poor.precision == 0.0
    assert poor.recall == 0.0
    assert poor.f1 == 0.0
    assert report.accuracy == pytest.approx(1.0)


def test_unknown_label_rejected() -> None:
    with pytest.raises(ValueError):
        confusion_matrix(["mystery"], ["normal"], LABELS)


def test_length_mismatch_rejected() -> None:
    with pytest.raises(ValueError):
        confusion_matrix(["normal", "normal"], ["normal"], LABELS)


def test_report_formatting_runs() -> None:
    report = compute_report(["normal", "poor_posture"], ["normal", "normal"], LABELS)
    assert "precision" in report.format_report()
    assert "Confusion matrix" in report.format_confusion_matrix()
