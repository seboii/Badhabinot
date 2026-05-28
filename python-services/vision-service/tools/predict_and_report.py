"""Eğitilmiş model.pt'i test seti üzerinde değerlendirir ve baseline ile kıyaslar.

İki rapor üretir:
  1. Model raporu (confusion matrix + per-class P/R/F1 + makro/ağırlıklı)
  2. (Opsiyonel) Faz 1 heuristik baseline raporuyla yan yana karşılaştırma

Kullanım:
    python -m tools.predict_and_report --model model.pt --data data/test.npz \
        --json-out reports/model_eval.json

    # Baseline ile karşılaştır
    python -m tools.predict_and_report --model model.pt --data data/test.npz \
        --baseline reports/baseline.json --json-out reports/comparison.json

PyTorch gereklidir (training.infer'a bağlı).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from evaluation.labels import LABELS
from evaluation.metrics import compute_report


def _predict_all(predictor, sequences: np.ndarray) -> list[str]:
    """Tüm dizileri tahmin et — predictor.predict() -> (label, confidence)."""
    preds: list[str] = []
    for seq in sequences:
        label, _conf = predictor.predict(seq.astype(np.float32))
        preds.append(label)
    return preds


def _format_delta(model_val: float, baseline_val: float) -> str:
    delta = model_val - baseline_val
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.3f}"


def _print_comparison(model_report, baseline_json: dict) -> None:
    print("\n" + "=" * 70)
    print("BASELINE vs MODEL — Per-class F1")
    print("=" * 70)
    print(f"{'Sınıf':<25} {'Baseline F1':>12} {'Model F1':>12} {'Δ':>10}")
    print("-" * 70)
    baseline_pc = {row["label"]: row for row in baseline_json.get("per_class", [])}
    for cls in model_report.per_class:
        bl = baseline_pc.get(cls.label, {})
        bl_f1 = float(bl.get("f1", 0.0))
        print(f"{cls.label:<25} {bl_f1:>12.3f} {cls.f1:>12.3f} {_format_delta(cls.f1, bl_f1):>10}")

    bl_macro_f1 = float(baseline_json.get("macro_f1", 0.0))
    print("-" * 70)
    print(f"{'Makro F1':<25} {bl_macro_f1:>12.3f} {model_report.macro_f1:>12.3f} "
          f"{_format_delta(model_report.macro_f1, bl_macro_f1):>10}")
    bl_acc = float(baseline_json.get("accuracy", 0.0))
    print(f"{'Accuracy':<25} {bl_acc:>12.3f} {model_report.accuracy:>12.3f} "
          f"{_format_delta(model_report.accuracy, bl_acc):>10}")
    print("=" * 70)


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Test seti üzerinde model değerlendir + baseline karşılaştır")
    parser.add_argument("--model", required=True, help="Eğitilmiş .pt (training.train çıktısı)")
    parser.add_argument("--data", required=True, help="Test seti npz (tools.split_dataset çıktısı)")
    parser.add_argument("--baseline", help="Faz 1 baseline JSON (evaluation.evaluate çıktısı)")
    parser.add_argument("--json-out", help="Sonucu JSON olarak yaz")
    args = parser.parse_args(argv)

    try:
        from training.infer import SequencePredictor
    except ImportError as exc:
        print(f"HATA: training.infer yüklenemedi ({exc}); pip install torch", file=sys.stderr)
        return 1

    in_path = Path(args.data)
    data = np.load(in_path)
    sequences = data["sequences"]
    labels = data["labels"]
    print(f"Test seti: {in_path} — n={len(sequences)}")

    predictor = SequencePredictor(args.model)
    preds = _predict_all(predictor, sequences)
    truth = [LABELS[int(c)] for c in labels]

    report = compute_report(truth, preds, LABELS)
    print()
    print(report.format_confusion_matrix())
    print()
    print(report.format_report())

    if args.baseline:
        bl_path = Path(args.baseline)
        if not bl_path.exists():
            print(f"UYARI: baseline JSON yok: {bl_path}", file=sys.stderr)
        else:
            with open(bl_path, encoding="utf-8") as fh:
                baseline_json = json.load(fh)
            _print_comparison(report, baseline_json)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "accuracy": report.accuracy,
            "macro_precision": report.macro_precision,
            "macro_recall": report.macro_recall,
            "macro_f1": report.macro_f1,
            "weighted_precision": report.weighted_precision,
            "weighted_recall": report.weighted_recall,
            "weighted_f1": report.weighted_f1,
            "total_support": report.total_support,
            "per_class": [
                {"label": c.label, "precision": c.precision, "recall": c.recall, "f1": c.f1, "support": c.support}
                for c in report.per_class
            ],
            "labels": list(report.labels),
            "confusion": report.confusion.tolist(),
        }
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON yazıldı: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
