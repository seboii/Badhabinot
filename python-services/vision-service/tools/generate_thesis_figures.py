"""Tez için figür üretici — confusion matrix, baseline-model bar, saliency heatmap.

matplotlib gereklidir (`pip install matplotlib`). Üretilen PNG'ler doğrudan
tez metnine eklenebilir.

Kullanım:
    # Confusion matrix (baseline veya model raporu JSON'undan)
    python -m tools.generate_thesis_figures confusion --report reports/model_eval.json \
        --out figures/confusion_model.png

    # Baseline vs Model bar grafiği
    python -m tools.generate_thesis_figures comparison \
        --baseline reports/baseline.json --model reports/model_eval.json \
        --out figures/comparison.png

    # Saliency heatmap (model + tek dizi)
    python -m tools.generate_thesis_figures saliency --model model.pt \
        --data data/test.npz --index 0 --out figures/saliency_sample0.png

    # Welford z-skoru dağılımı (baseline öğrendikten sonra)
    python -m tools.generate_thesis_figures baseline-z --user demo \
        --check data/test.npz --baselines-dir data/baselines --out figures/zscore_dist.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


def _import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")   # GUI gerek yok
        import matplotlib.pyplot as plt
        return plt
    except ImportError as exc:
        print(f"HATA: matplotlib gerekli ({exc}). pip install matplotlib", file=sys.stderr)
        sys.exit(1)


# ── Confusion matrix ─────────────────────────────────────────────────────────

def cmd_confusion(args: argparse.Namespace) -> int:
    plt = _import_matplotlib()
    with open(args.report, encoding="utf-8") as fh:
        report = json.load(fh)
    labels = report["labels"]
    cm = np.array(report["confusion"], dtype=np.int64)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Tahmin")
    ax.set_ylabel("Gerçek")
    ax.set_title(args.title or "Confusion Matrix")

    # Her hücreye sayıyı yaz
    threshold = cm.max() / 2.0 if cm.max() > 0 else 1
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            color = "white" if cm[i, j] > threshold else "black"
            ax.text(j, i, int(cm[i, j]), ha="center", va="center", color=color)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    _save(fig, args.out)
    return 0


# ── Baseline vs Model karşılaştırması ────────────────────────────────────────

def cmd_comparison(args: argparse.Namespace) -> int:
    plt = _import_matplotlib()
    with open(args.baseline, encoding="utf-8") as fh:
        baseline = json.load(fh)
    with open(args.model, encoding="utf-8") as fh:
        model = json.load(fh)

    labels = [row["label"] for row in model["per_class"]]
    bl_f1 = {row["label"]: row["f1"] for row in baseline.get("per_class", [])}
    model_f1 = [row["f1"] for row in model["per_class"]]
    baseline_f1 = [bl_f1.get(lbl, 0.0) for lbl in labels]

    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - width / 2, baseline_f1, width, label="Heuristik baseline")
    ax.bar(x + width / 2, model_f1, width, label="1D-CNN model")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("F1")
    ax.set_title("Sınıf bazında F1 — Baseline vs Model")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    _save(fig, args.out)
    return 0


# ── Saliency heatmap ─────────────────────────────────────────────────────────

def cmd_saliency(args: argparse.Namespace) -> int:
    plt = _import_matplotlib()
    try:
        from training.explain import SaliencyExplainer
    except ImportError as exc:
        print(f"HATA: training.explain yüklenemedi ({exc}). pip install torch", file=sys.stderr)
        return 1

    data = np.load(args.data)
    sequences = data["sequences"]
    if args.index < 0 or args.index >= len(sequences):
        print(f"HATA: index {args.index} aralık dışı (0–{len(sequences) - 1})", file=sys.stderr)
        return 1

    explainer = SaliencyExplainer(args.model, top_k=10)
    result = explainer.explain(sequences[args.index].astype(np.float32))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6),
                              gridspec_kw={"width_ratios": [3, 1]})

    # Sol: saliency matrisi (zaman × özellik)
    ax0 = axes[0]
    im = ax0.imshow(result.saliency.T, aspect="auto", cmap="viridis")
    ax0.set_xlabel("Zaman adımı (kare)")
    ax0.set_ylabel("Özellik indeksi")
    ax0.set_title(f"Saliency — tahmin: {result.predicted_label} ({result.confidence:.2f})")
    fig.colorbar(im, ax=ax0)

    # Sağ: top features bar
    ax1 = axes[1]
    names = [n for n, _ in result.top_features]
    scores = [s for _, s in result.top_features]
    y_pos = np.arange(len(names))
    ax1.barh(y_pos, scores)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(names, fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlabel("Normalize önem")
    ax1.set_title("Top features")
    fig.tight_layout()
    _save(fig, args.out)
    return 0


# ── Welford z-skoru dağılımı ─────────────────────────────────────────────────

def cmd_baseline_z(args: argparse.Namespace) -> int:
    plt = _import_matplotlib()
    from training.personalizer import UserBaseline

    baseline = UserBaseline(args.baselines_dir)
    if not baseline.is_ready(args.user):
        print(f"HATA: {args.user} baseline henüz hazır değil "
              f"(n={baseline.sample_count(args.user)})", file=sys.stderr)
        return 1

    data = np.load(args.check)
    sequences = data["sequences"]
    scores: list[float] = []
    for seq in sequences:
        fv = seq.astype(np.float64).mean(axis=0)
        scores.append(baseline.anomaly_score(args.user, fv))

    scores_arr = np.array(scores)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(scores_arr, bins=20, edgecolor="black")
    ax.axvline(2.0, color="red", linestyle="--", label="Eşik 2.0")
    ax.set_xlabel("Anomali skoru (ortalama |z|)")
    ax.set_ylabel("Dizi sayısı")
    ax.set_title(f"Kişisel baseline z-skoru dağılımı — {args.user}")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    _save(fig, args.out)
    return 0


# ── Yardımcı ─────────────────────────────────────────────────────────────────

def _save(fig, path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(p, dpi=150, bbox_inches="tight")
    print(f"Yazıldı: {p}")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Tez figürleri üret")
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_cm = subparsers.add_parser("confusion", help="Confusion matrix PNG")
    p_cm.add_argument("--report", required=True, help="evaluation.evaluate veya predict_and_report JSON")
    p_cm.add_argument("--out", required=True)
    p_cm.add_argument("--title")
    p_cm.set_defaults(func=cmd_confusion)

    p_cmp = subparsers.add_parser("comparison", help="Baseline vs Model F1 bar")
    p_cmp.add_argument("--baseline", required=True)
    p_cmp.add_argument("--model", required=True)
    p_cmp.add_argument("--out", required=True)
    p_cmp.set_defaults(func=cmd_comparison)

    p_sal = subparsers.add_parser("saliency", help="Saliency heatmap + top features")
    p_sal.add_argument("--model", required=True)
    p_sal.add_argument("--data", required=True)
    p_sal.add_argument("--index", type=int, default=0)
    p_sal.add_argument("--out", required=True)
    p_sal.set_defaults(func=cmd_saliency)

    p_bz = subparsers.add_parser("baseline-z", help="Welford z-skoru dağılım histogramı")
    p_bz.add_argument("--user", required=True)
    p_bz.add_argument("--check", required=True, help="sequences.npz")
    p_bz.add_argument("--baselines-dir", default="data/baselines")
    p_bz.add_argument("--out", required=True)
    p_bz.set_defaults(func=cmd_baseline_z)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
