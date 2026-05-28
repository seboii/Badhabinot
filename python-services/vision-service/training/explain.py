"""Faz 3 XAI — LandmarkSequenceClassifier için saliency açıklayıcı.

"Neden bu karar verildi?" sorusunu gradient × input saliency ile yanıtlar:
hangi zaman adımı ve hangi landmark/özellik kararı tetikledi.

Gradient × input, vanilla gradient'tan daha kararlı bir önem skoru üretir
(sıfır-değerli özellikler katkıda bulunmuş gibi görünmez).

Kullanım (Python):
    from training.explain import SaliencyExplainer
    explainer = SaliencyExplainer("model.pt")
    result = explainer.explain(sequence)          # (window, 58) numpy
    print(result.predicted_label, result.confidence)
    for name, score in result.top_features[:5]:
        print(f"  {name}: {score:.3f}")

Kullanım (CLI):
    python -m training.explain --model model.pt --data sequences.npz --index 0

PyTorch gerektirir (yalnızca SaliencyExplainer; FEATURE_NAMES, bar grafikleri
ve CLI yardımcıları saf numpy/python'dır).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field

import numpy as np

from evaluation.labels import LABELS
from training.landmark_features import FEATURE_DIM, FEATURE_NAMES


# ── Açıklama çıktısı ──────────────────────────────────────────────────────────

@dataclass
class ExplanationResult:
    predicted_label: str
    confidence: float
    step_importance: np.ndarray        # (T,)  — zaman adımı önemi
    feature_importance: np.ndarray     # (F,)  — özellik önemi
    saliency: np.ndarray               # (T, F) — ham saliency matrisi
    top_features: list[tuple[str, float]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "predicted_label": self.predicted_label,
            "confidence": float(self.confidence),
            "step_importance": [float(v) for v in self.step_importance],
            "top_features": [(name, float(score)) for name, score in self.top_features],
        }


# ── Saliency açıklayıcı ───────────────────────────────────────────────────────

class SaliencyExplainer:
    """Gradient × input saliency ile 1D-CNN kararlarını açıklar.

    checkpoint_path: training.train tarafından kaydedilen .pt dosyası
                     ({state_dict, feature_dim, labels} sözlüğü).
    top_k: Sonuçta döndürülecek önemli özellik sayısı.
    """

    def __init__(self, checkpoint_path: str, top_k: int = 5) -> None:
        try:
            import torch as _torch
        except ImportError as exc:
            raise ImportError(
                "SaliencyExplainer PyTorch gerektirir: pip install torch"
            ) from exc
        self._torch = _torch
        self.top_k = top_k

        ck = _torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        feature_dim: int = ck["feature_dim"]
        labels: list[str] = ck["labels"]

        from training.model import LandmarkSequenceClassifier
        self.model = LandmarkSequenceClassifier(feature_dim, len(labels))
        self.model.load_state_dict(ck["state_dict"])
        self.model.eval()
        self.labels = labels

    def explain(self, sequence: np.ndarray) -> ExplanationResult:
        """sequence: (T, F) float32 numpy dizisi → ExplanationResult döndürür."""
        torch = self._torch
        x = torch.tensor(sequence[np.newaxis], dtype=torch.float32)   # (1, T, F)
        x.requires_grad_(True)

        logits = self.model(x)
        pred_idx = int(logits.argmax(dim=1).item())
        confidence = float(torch.softmax(logits, dim=1)[0, pred_idx].item())

        # Tahmin edilen sınıf logit'i üzerinden geri yayılım.
        # Gradient × input → daha kararlı saliency (sıfır özellikler katkı yapmaz).
        self.model.zero_grad()
        logits[0, pred_idx].backward()
        saliency = (x.grad[0] * x[0]).detach().abs().numpy()   # (T, F)

        step_importance = saliency.sum(axis=1)        # (T,)
        feature_importance = saliency.sum(axis=0)     # (F,)

        max_fi = float(feature_importance.max())
        norm_fi = feature_importance / (max_fi + 1e-8)

        top_indices = np.argsort(norm_fi)[::-1][: self.top_k]
        top_features = [(FEATURE_NAMES[i], float(norm_fi[i])) for i in top_indices]

        return ExplanationResult(
            predicted_label=self.labels[pred_idx],
            confidence=confidence,
            step_importance=step_importance,
            feature_importance=feature_importance,
            saliency=saliency,
            top_features=top_features,
        )


# ── ASCII görselleştirme ──────────────────────────────────────────────────────

def render_step_bar(step_importance: np.ndarray, width: int = 40) -> str:
    """Zaman adımı önemini ASCII bar plot olarak formatla.

    width: Bar'ın maksimum karakter genişliği.
    """
    if step_importance.size == 0:
        return "(boş)"
    peak = float(step_importance.max()) or 1.0
    lines = []
    for t, value in enumerate(step_importance):
        bar_len = int(round(width * (float(value) / peak)))
        lines.append(f"  t={t:>3}  |{'█' * bar_len}{' ' * (width - bar_len)}|  {float(value):.4f}")
    return "\n".join(lines)


def format_explanation(result: ExplanationResult) -> str:
    """ExplanationResult'ı insan-okunur metne çevirir."""
    lines = [
        f"Tahmin: {result.predicted_label}  (güven: {result.confidence:.3f})",
        "",
        "En etkili özellikler:",
    ]
    for name, score in result.top_features:
        lines.append(f"  • {name:<28} {score:.3f}")
    lines.extend([
        "",
        "Zaman adımı önemi:",
        render_step_bar(result.step_importance),
    ])
    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Eğitilmiş modele tek dizi için XAI açıklaması")
    parser.add_argument("--model", required=True, help="train.py çıktısı .pt dosyası")
    parser.add_argument("--data", required=True, help="sequences.npz (collect.py çıktısı)")
    parser.add_argument("--index", type=int, default=0, help="Açıklanacak dizinin indeksi")
    parser.add_argument("--top-k", type=int, default=5, help="Listelenecek özellik sayısı")
    parser.add_argument("--json-out", help="Sonucu JSON olarak yaz")
    args = parser.parse_args(argv)

    data = np.load(args.data)
    sequences = data["sequences"]
    labels = data["labels"] if "labels" in data.files else None
    if args.index < 0 or args.index >= len(sequences):
        print(f"HATA: index {args.index} aralık dışı (0–{len(sequences) - 1})", file=sys.stderr)
        return 1

    explainer = SaliencyExplainer(args.model, top_k=args.top_k)
    result = explainer.explain(sequences[args.index].astype(np.float32))

    if labels is not None:
        gt_idx = int(labels[args.index])
        if 0 <= gt_idx < len(LABELS):
            print(f"Gerçek etiket: {LABELS[gt_idx]}")
    print(format_explanation(result))

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as fh:
            json.dump(result.to_dict(), fh, ensure_ascii=False, indent=2)
        print(f"\nJSON yazıldı: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
