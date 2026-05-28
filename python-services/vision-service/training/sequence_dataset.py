"""Landmark dizisi veri seti (npz) — PyTorch Dataset.

npz dosyası şu dizileri içerir::

    sequences: (N, window, feature_dim) float32
    labels:    (N,) int64   — evaluation.labels.LABELS indeksleri

collect.py bu formatta veri üretir.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


class LandmarkSequenceDataset(Dataset):
    def __init__(self, npz_path: str | Path) -> None:
        data = np.load(npz_path)
        if "sequences" not in data or "labels" not in data:
            raise ValueError("npz 'sequences' ve 'labels' dizilerini içermeli")
        self.sequences = data["sequences"].astype(np.float32)
        self.labels = data["labels"].astype(np.int64)
        if len(self.sequences) != len(self.labels):
            raise ValueError("sequences ve labels uzunlukları uyuşmuyor")

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        return torch.from_numpy(self.sequences[idx]), int(self.labels[idx])
