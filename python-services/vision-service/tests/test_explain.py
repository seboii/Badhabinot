"""training.explain — torch-gated (torch yoksa skip).

ExplanationResult şekillerinin doğru, top_features adlarının FEATURE_NAMES'ten
geldiğini, üretilen saliency'nin sıfır gradient değil "gerçek" bir önem
dağılımı olduğunu (modeli küçük bir batch'e overfit ettikten sonra) doğrular.

Render yardımcıları (format_explanation, render_step_bar) saf python — torch
kurulu olmasa da içe aktarılabilir; ancak SaliencyExplainer torch gerektirir,
o yüzden tüm modül torch'a koşullu.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from evaluation.labels import LABELS                              # noqa: E402
from training.explain import SaliencyExplainer, format_explanation, render_step_bar  # noqa: E402
from training.landmark_features import FEATURE_DIM, FEATURE_NAMES   # noqa: E402
from training.model import LandmarkSequenceClassifier             # noqa: E402


def _train_tiny_model(tmp_path: Path, window: int = 6, samples_per_class: int = 4) -> Path:
    """Küçük sentetik veriye overfit edilmiş bir model döndür."""
    torch.manual_seed(0)
    np.random.seed(0)
    n_classes = len(LABELS)
    sequences = []
    labels = []
    for cls in range(n_classes):
        # Her sınıf için özellik vektörünün belirli bir bölümünü "1.0"a yakın yapalım.
        for _ in range(samples_per_class):
            seq = np.random.normal(0.0, 0.05, size=(window, FEATURE_DIM)).astype(np.float32)
            seq[:, cls * 3 : cls * 3 + 3] += 1.0   # sınıfa özgü güçlü sinyal
            sequences.append(seq)
            labels.append(cls)
    x = torch.tensor(np.stack(sequences))
    y = torch.tensor(labels, dtype=torch.long)

    model = LandmarkSequenceClassifier(FEATURE_DIM, n_classes)
    optim = torch.optim.Adam(model.parameters(), lr=1e-2)
    loss_fn = torch.nn.CrossEntropyLoss()
    for _ in range(80):
        optim.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optim.step()

    ck_path = tmp_path / "model.pt"
    torch.save({"state_dict": model.state_dict(), "feature_dim": FEATURE_DIM, "labels": LABELS}, ck_path)
    return ck_path


@pytest.fixture(scope="module")
def trained_model_path(tmp_path_factory) -> Path:
    return _train_tiny_model(tmp_path_factory.mktemp("xai-model"))


def test_explanation_shapes_and_label(trained_model_path: Path) -> None:
    explainer = SaliencyExplainer(str(trained_model_path), top_k=4)
    window = 6
    sequence = np.random.RandomState(7).normal(0.0, 0.05, size=(window, FEATURE_DIM)).astype(np.float32)
    sequence[:, 0:3] += 1.0   # 0. sınıfa özgü sinyal — model bu sinyali öğrendi
    result = explainer.explain(sequence)

    assert result.predicted_label in LABELS
    assert 0.0 <= result.confidence <= 1.0
    assert result.step_importance.shape == (window,)
    assert result.feature_importance.shape == (FEATURE_DIM,)
    assert result.saliency.shape == (window, FEATURE_DIM)
    assert len(result.top_features) == 4
    for name, score in result.top_features:
        assert name in FEATURE_NAMES
        assert 0.0 <= score <= 1.0


def test_top_features_align_with_signal_block(trained_model_path: Path) -> None:
    """0. sınıfa karşılık gelen ilk 3 özellik (0,1,2) en üstte yer almalı."""
    explainer = SaliencyExplainer(str(trained_model_path), top_k=5)
    window = 6
    sequence = np.random.RandomState(11).normal(0.0, 0.05, size=(window, FEATURE_DIM)).astype(np.float32)
    sequence[:, 0:3] += 1.0
    result = explainer.explain(sequence)

    top_names = {name for name, _ in result.top_features}
    expected = {FEATURE_NAMES[i] for i in (0, 1, 2)}
    overlap = top_names & expected
    assert len(overlap) >= 2, f"En etkili özellikler arasında sınıfa özgü blok beklenirdi, ancak: {top_names}"


def test_saliency_is_nonzero_and_finite(trained_model_path: Path) -> None:
    explainer = SaliencyExplainer(str(trained_model_path))
    sequence = np.random.RandomState(13).normal(0.0, 0.05, size=(5, FEATURE_DIM)).astype(np.float32)
    sequence[:, 6:9] += 1.0   # farklı bir sınıfı tetikle
    result = explainer.explain(sequence)
    assert float(result.feature_importance.sum()) > 0.0
    assert np.isfinite(result.saliency).all()


def test_to_dict_is_json_serializable(trained_model_path: Path) -> None:
    import json
    explainer = SaliencyExplainer(str(trained_model_path), top_k=3)
    sequence = np.random.RandomState(17).normal(0.0, 0.05, size=(4, FEATURE_DIM)).astype(np.float32)
    payload = explainer.explain(sequence).to_dict()
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)
    assert decoded["predicted_label"] in LABELS
    assert len(decoded["top_features"]) == 3


def test_render_helpers_produce_text() -> None:
    step = np.array([0.1, 0.5, 0.2, 0.9])
    bar = render_step_bar(step, width=20)
    assert "t=  0" in bar and "t=  3" in bar
    assert "█" in bar   # en az bir bar karakteri çıkmalı
