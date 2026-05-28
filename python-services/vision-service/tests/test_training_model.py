"""training.model — torch-gated (torch yoksa skip).

`pip install -r requirements-train.txt` sonrası çalışır. Model mimarisinin doğru
şekil ürettiğini ve öğrenebildiğini (küçük batch'i ezberleyebildiğini) doğrular.
"""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from evaluation.labels import LABELS                       # noqa: E402
from training.landmark_features import FEATURE_DIM          # noqa: E402
from training.model import LandmarkSequenceClassifier       # noqa: E402


def test_forward_output_shape() -> None:
    model = LandmarkSequenceClassifier(FEATURE_DIM, len(LABELS))
    batch = torch.randn(4, 8, FEATURE_DIM)   # batch=4, window=8
    out = model(batch)
    assert out.shape == (4, len(LABELS))


def test_single_sample_batch_works() -> None:
    # BatchNorm kullanılmadığı için batch=1 de geçmeli.
    model = LandmarkSequenceClassifier(FEATURE_DIM, len(LABELS))
    out = model(torch.randn(1, 5, FEATURE_DIM))
    assert out.shape == (1, len(LABELS))


def test_model_can_overfit_tiny_batch() -> None:
    torch.manual_seed(0)
    model = LandmarkSequenceClassifier(FEATURE_DIM, len(LABELS))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-2)
    criterion = torch.nn.CrossEntropyLoss()
    x = torch.randn(8, 6, FEATURE_DIM)
    y = torch.randint(0, len(LABELS), (8,))
    for _ in range(60):
        optimizer.zero_grad()
        loss = criterion(model(x), y)
        loss.backward()
        optimizer.step()
    accuracy = (model(x).argmax(dim=1) == y).float().mean().item()
    assert accuracy >= 0.9
