"""Sınıflandırma metrikleri — saf numpy, harici ML bağımlılığı yok.

Confusion matrix, sınıf-başına precision/recall/F1, macro ve weighted ortalamalar
ve toplam doğruluk hesaplar. Tek-etiketli (single-label) çok-sınıflı değerlendirme
içindir.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClassMetrics:
    label: str
    precision: float
    recall: float
    f1: float
    support: int


@dataclass
class EvaluationReport:
    labels: list[str]
    confusion: np.ndarray          # (n, n) — satır = gerçek, sütun = tahmin
    per_class: list[ClassMetrics]
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_precision: float
    weighted_recall: float
    weighted_f1: float
    total_support: int

    def format_confusion_matrix(self) -> str:
        return _format_confusion_matrix(self.labels, self.confusion)

    def format_report(self) -> str:
        return _format_report(self)


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> np.ndarray:
    """(n, n) matris döndürür; satır gerçek sınıf, sütun tahmin edilen sınıf.

    ``labels`` dışında kalan bir değer ValueError ile reddedilir.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true ve y_pred aynı uzunlukta olmalı")
    index = {label: i for i, label in enumerate(labels)}
    matrix = np.zeros((len(labels), len(labels)), dtype=int)
    for true_label, pred_label in zip(y_true, y_pred):
        if true_label not in index:
            raise ValueError(f"bilinmeyen gerçek etiket: {true_label!r}")
        if pred_label not in index:
            raise ValueError(f"bilinmeyen tahmin etiketi: {pred_label!r}")
        matrix[index[true_label]][index[pred_label]] += 1
    return matrix


def compute_report(y_true: list[str], y_pred: list[str], labels: list[str]) -> EvaluationReport:
    """Etiket listelerinden tam bir değerlendirme raporu üretir."""
    matrix = confusion_matrix(y_true, y_pred, labels)
    total = int(matrix.sum())
    correct = int(np.trace(matrix))

    per_class: list[ClassMetrics] = []
    for i, label in enumerate(labels):
        tp = int(matrix[i][i])
        predicted = int(matrix[:, i].sum())   # bu sınıf olarak tahmin edilenler
        actual = int(matrix[i, :].sum())      # gerçekte bu sınıf olanlar (support)
        precision = _safe_div(tp, predicted)
        recall = _safe_div(tp, actual)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_class.append(ClassMetrics(label, precision, recall, f1, actual))

    n_classes = len(labels) or 1
    macro_precision = sum(c.precision for c in per_class) / n_classes
    macro_recall = sum(c.recall for c in per_class) / n_classes
    macro_f1 = sum(c.f1 for c in per_class) / n_classes

    weighted_precision = _safe_div(sum(c.precision * c.support for c in per_class), total)
    weighted_recall = _safe_div(sum(c.recall * c.support for c in per_class), total)
    weighted_f1 = _safe_div(sum(c.f1 * c.support for c in per_class), total)

    return EvaluationReport(
        labels=list(labels),
        confusion=matrix,
        per_class=per_class,
        accuracy=_safe_div(correct, total),
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        weighted_precision=weighted_precision,
        weighted_recall=weighted_recall,
        weighted_f1=weighted_f1,
        total_support=total,
    )


def _format_confusion_matrix(labels: list[str], matrix: np.ndarray) -> str:
    width = max([len(label) for label in labels] + [6])
    header = " " * (width + 3) + "".join(f"{label[:width]:>{width + 2}}" for label in labels)
    lines = ["Confusion matrix (satır = gerçek, sütun = tahmin):", header]
    for i, label in enumerate(labels):
        row = f"{label:<{width}} | " + "".join(f"{int(matrix[i][j]):>{width + 2}}" for j in range(len(labels)))
        lines.append(row)
    return "\n".join(lines)


def _format_report(report: EvaluationReport) -> str:
    width = max([len(c.label) for c in report.per_class] + [12])
    lines = [
        f"{'':<{width}}  {'precision':>9}  {'recall':>7}  {'f1':>7}  {'support':>7}",
    ]
    for c in report.per_class:
        lines.append(
            f"{c.label:<{width}}  {c.precision:>9.3f}  {c.recall:>7.3f}  {c.f1:>7.3f}  {c.support:>7d}"
        )
    lines.append("")
    lines.append(
        f"{'accuracy':<{width}}  {'':>9}  {'':>7}  {report.accuracy:>7.3f}  {report.total_support:>7d}"
    )
    lines.append(
        f"{'macro avg':<{width}}  {report.macro_precision:>9.3f}  {report.macro_recall:>7.3f}  "
        f"{report.macro_f1:>7.3f}  {report.total_support:>7d}"
    )
    lines.append(
        f"{'weighted avg':<{width}}  {report.weighted_precision:>9.3f}  {report.weighted_recall:>7.3f}  "
        f"{report.weighted_f1:>7.3f}  {report.total_support:>7d}"
    )
    return "\n".join(lines)
