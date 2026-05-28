"""Tek pencere için uçtan uca Faz 2+3+4 demosu — savunmada kullanılır.

Akış (kullanıcı tek bir komut çalıştırır):
    1. sequences.npz'den (veya canlı toplanan) bir dizi seçilir
    2. Eğitilmiş model.pt ile tahmin yapılır
    3. Saliency açıklayıcı top_features çıkarır
    4. Kullanıcı baseline'ı (varsa) z-skoru ve top_deviations hesaplar
    5. BehavioralInsight oluşur — JSON + TR özet basılır

Bu çıktıyı tezde "Multimodal Füzyon" örneği olarak, savunmada da canlı demo
slaytında gösterirsin.

Kullanım:
    python -m tools.demo_pipeline --model model.pt --data data/test.npz \
        --index 0 --user demo-user --baselines-dir data/baselines \
        --json-out demo_output.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Uçtan uca Faz 2+3+4 demo")
    parser.add_argument("--model", required=True, help="Eğitilmiş model.pt")
    parser.add_argument("--data", required=True, help="sequences.npz")
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--user", default="demo-user")
    parser.add_argument("--baselines-dir", default="data/baselines",
                        help="UserBaseline veri dizini (boşsa anomaly skoru atlanır)")
    parser.add_argument("--json-out", help="Sonucu JSON dosyasına yaz")
    args = parser.parse_args(argv)

    # Veri yükle
    data = np.load(args.data)
    sequences = data["sequences"]
    if args.index < 0 or args.index >= len(sequences):
        print(f"HATA: index {args.index} aralık dışı (0–{len(sequences) - 1})", file=sys.stderr)
        return 1
    sequence = sequences[args.index].astype(np.float32)

    # Faz 2 — tahmin
    try:
        from training.infer import SequencePredictor
    except ImportError as exc:
        print(f"HATA: PyTorch yok ({exc}). pip install torch", file=sys.stderr)
        return 1

    predictor = SequencePredictor(args.model)
    predicted_label, confidence = predictor.predict(sequence)
    print(f"\n[Faz 2] Model tahmini: {predicted_label}  (güven: {confidence:.3f})")

    # Faz 3a — saliency
    from training.explain import SaliencyExplainer
    explainer = SaliencyExplainer(args.model, top_k=5)
    saliency_result = explainer.explain(sequence)
    print(f"\n[Faz 3a] XAI top features:")
    for name, score in saliency_result.top_features:
        print(f"  • {name:<28} {score:.3f}")

    # Faz 3b — kişisel baseline
    from training.personalizer import UserBaseline
    baseline = UserBaseline(args.baselines_dir)
    feature_vector = sequence.mean(axis=0).astype(np.float64)  # pencerenin ortalama vektörü
    anomaly_score = 0.0
    top_deviations: list[tuple[str, float]] = []
    if baseline.is_ready(args.user):
        anomaly_score = baseline.anomaly_score(args.user, feature_vector)
        top_deviations = baseline.top_deviations(args.user, feature_vector, top_k=5)
        print(f"\n[Faz 3b] Kişisel baseline (n={baseline.sample_count(args.user)}):")
        print(f"  Anomaly skoru (mean |z|): {anomaly_score:.3f}")
        for name, score in top_deviations:
            print(f"  • {name:<28} |z|={score:.3f}")
    else:
        print(f"\n[Faz 3b] Kişisel baseline atlandı — {args.user} için yeterli örnek yok "
              f"(n={baseline.sample_count(args.user)}, gerekli ≥ 30)")

    # Faz 4 — BehavioralInsight
    from training.insights import build_insight
    insight = build_insight(
        predicted_label=predicted_label,
        confidence=confidence,
        top_features=saliency_result.top_features,
        anomaly_score=anomaly_score,
        top_deviations=top_deviations,
    )
    print(f"\n[Faz 4] BehavioralInsight:")
    print(f"  TR özet: {insight.summary_tr}")

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(insight.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON yazıldı: {out_path}")

    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
