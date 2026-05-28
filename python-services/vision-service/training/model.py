"""Temporal landmark sequence classifier — 1D-CNN (PyTorch).

Girdi:  (batch, window, feature_dim) — kare penceresi boyunca landmark özellikleri
Çıktı:  (batch, num_classes) — sınıf logitleri

Davranış tek karede değil bir hareket dizisinde belirir; bu yüzden zaman ekseni
üzerinde 1D konvolüsyon uygulanır. BatchNorm yerine sade Conv+ReLU kullanılır,
böylece batch boyutu 1 olsa bile çalışır.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class LandmarkSequenceClassifier(nn.Module):
    def __init__(self, feature_dim: int, num_classes: int, hidden: int = 64, dropout: float = 0.3) -> None:
        super().__init__()
        self.feature_dim = feature_dim
        self.num_classes = num_classes
        self.encoder = nn.Sequential(
            nn.Conv1d(feature_dim, hidden, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(hidden, hidden, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),       # zaman eksenini özetle → (B, hidden, 1)
        )
        self.head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, F) → (B, F, T) (Conv1d kanal-önce bekler)
        x = x.transpose(1, 2)
        encoded = self.encoder(x).squeeze(-1)   # (B, hidden)
        return self.head(encoded)
