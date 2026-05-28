"""Eğitilmiş landmark sequence classifier ile çıkarım.

Eğitilmiş bir modeli yükler ve bir landmark özellik dizisini (window, feature_dim)
bir davranış sınıfına eşler. Pipeline entegrasyonu (heuristik yerine bu modeli
kullanma) Faz 2'nin sonraki adımıdır; bu modül tek başına çıkarımı sağlar.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch

from evaluation.labels import LABELS
from training.landmark_features import FEATURE_DIM
from training.model import LandmarkSequenceClassifier


class SequencePredictor:
    def __init__(self, model_path: str | Path) -> None:
        checkpoint = torch.load(model_path, map_location="cpu")
        self.labels: list[str] = checkpoint.get("labels", LABELS)
        feature_dim: int = checkpoint.get("feature_dim", FEATURE_DIM)
        self.model = LandmarkSequenceClassifier(feature_dim, len(self.labels))
        self.model.load_state_dict(checkpoint["state_dict"])
        self.model.eval()

    def predict(self, sequence: np.ndarray) -> tuple[str, float]:
        """(window, feature_dim) dizisi → (etiket, güven)."""
        tensor = torch.from_numpy(np.asarray(sequence, dtype=np.float32)).unsqueeze(0)
        with torch.no_grad():
            probabilities = torch.softmax(self.model(tensor), dim=1)[0]
        index = int(probabilities.argmax())
        return self.labels[index], float(probabilities[index])
