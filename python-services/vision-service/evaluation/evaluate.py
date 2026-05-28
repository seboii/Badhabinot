"""CLI: etiketli manifest üzerinde davranış tespiti pipeline'ını değerlendir.

Kullanım:
    python -m evaluation.evaluate --manifest data/labels.jsonl
    python -m evaluation.evaluate --manifest data/labels.jsonl --json-out results.json

Confusion matrix + sınıf-başına precision/recall/F1 basar. Bu sayılar mevcut
heuristik+landmark pipeline'ının baseline'ını oluşturur (tez: Deneysel Sonuçlar).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from evaluation.dataset import label_distribution, load_manifest
from evaluation.labels import LABELS
from evaluation.metrics import compute_report
from evaluation.predict import predict_samples


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe çıktı güvenliği
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Davranış tespiti pipeline'ı değerlendirmesi")
    parser.add_argument("--manifest", required=True, help="JSONL etiket manifesti yolu")
    parser.add_argument("--json-out", default=None, help="Metrikleri JSON olarak buraya yaz")
    args = parser.parse_args(argv)

    samples = load_manifest(args.manifest)
    distribution = label_distribution(samples)
    print(f"Yüklenen örnek sayısı: {len(samples)}")
    print(f"Sınıf dağılımı: {distribution}\n")

    y_true, y_pred = asyncio.run(predict_samples(samples))
    report = compute_report(y_true, y_pred, LABELS)

    print(report.format_confusion_matrix())
    print()
    print(report.format_report())

    if args.json_out:
        payload = {
            "labels": report.labels,
            "confusion": report.confusion.tolist(),
            "accuracy": report.accuracy,
            "macro_precision": report.macro_precision,
            "macro_recall": report.macro_recall,
            "macro_f1": report.macro_f1,
            "weighted_f1": report.weighted_f1,
            "per_class": [
                {
                    "label": c.label,
                    "precision": c.precision,
                    "recall": c.recall,
                    "f1": c.f1,
                    "support": c.support,
                }
                for c in report.per_class
            ],
            "label_distribution": distribution,
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        print(f"\nMetrikler JSON olarak yazıldı: {args.json_out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
