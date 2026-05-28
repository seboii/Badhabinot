"""training.personalizer — saf numpy, her zaman çalışır.

Welford istatistiklerinin doğru biriktiğini, anomali skorunun yeterli örnek
altında bastırıldığını, sapmalı vektörün normal davranışa göre daha yüksek
skor aldığını ve baseline'ın diskte saklanıp yüklendiğini doğrular.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from training.landmark_features import FEATURE_DIM, FEATURE_NAMES
from training.personalizer import UserBaseline


@pytest.fixture
def baseline(tmp_path: Path) -> UserBaseline:
    return UserBaseline(data_dir=tmp_path)


def _normal_vector(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.5, scale=0.05, size=FEATURE_DIM).astype(np.float32)


def test_initial_state_is_empty(baseline: UserBaseline) -> None:
    assert baseline.sample_count("u1") == 0
    assert baseline.is_ready("u1") is False
    assert baseline.anomaly_score("u1", _normal_vector(0)) == 0.0


def test_anomaly_score_zero_below_min_samples(baseline: UserBaseline) -> None:
    for i in range(5):
        baseline.update("u1", _normal_vector(i))
    assert baseline.sample_count("u1") == 5
    assert baseline.is_ready("u1") is False
    # _MIN_SAMPLES_FOR_SCORING (30) altındayken skor 0 olmalı (kararlı değil).
    assert baseline.anomaly_score("u1", _normal_vector(99)) == 0.0


def test_normal_vector_scores_lower_than_outlier(baseline: UserBaseline) -> None:
    for i in range(60):
        baseline.update("u1", _normal_vector(i))
    assert baseline.is_ready("u1")
    normal = _normal_vector(1000)
    outlier = np.full(FEATURE_DIM, 5.0, dtype=np.float32)   # baseline 0.5 ± 0.05; uçuk
    s_normal = baseline.anomaly_score("u1", normal)
    s_outlier = baseline.anomaly_score("u1", outlier)
    assert s_outlier > s_normal
    assert s_outlier > 5.0   # büyük sapma → yüksek z


def test_top_deviations_returns_named_features(baseline: UserBaseline) -> None:
    for i in range(60):
        baseline.update("u1", _normal_vector(i))
    vector = _normal_vector(2000)
    # Tek bir özelliği uçuk yap.
    target_idx = 7
    vector[target_idx] = 8.0
    deviations = baseline.top_deviations("u1", vector, top_k=3)
    assert len(deviations) == 3
    names, scores = zip(*deviations)
    # En tepedeki özellik bizim uçuk yaptığımız olmalı.
    assert names[0] == FEATURE_NAMES[target_idx]
    # Tüm skorlar pozitif ve azalan sırada.
    assert all(s >= 0 for s in scores)
    assert list(scores) == sorted(scores, reverse=True)


def test_state_persists_across_instances(tmp_path: Path) -> None:
    first = UserBaseline(data_dir=tmp_path)
    for i in range(40):
        first.update("u1", _normal_vector(i))
    count_before = first.sample_count("u1")

    # Yeni instance aynı dizinden okuyabilmeli.
    second = UserBaseline(data_dir=tmp_path)
    assert second.sample_count("u1") == count_before
    assert second.is_ready("u1") is True


def test_reset_clears_user_state(baseline: UserBaseline) -> None:
    for i in range(40):
        baseline.update("u1", _normal_vector(i))
    assert baseline.is_ready("u1")
    baseline.reset("u1")
    assert baseline.sample_count("u1") == 0
    assert baseline.is_ready("u1") is False


def test_update_batch_accepts_2d_and_3d(baseline: UserBaseline) -> None:
    flat = np.stack([_normal_vector(i) for i in range(20)])         # (20, F)
    windows = np.stack([np.stack([_normal_vector(i + j) for j in range(4)]) for i in range(10)])   # (10, 4, F)
    baseline.update_batch("u1", flat)
    baseline.update_batch("u1", windows)
    assert baseline.sample_count("u1") == 20 + 10 * 4


def test_invalid_shape_raises(baseline: UserBaseline) -> None:
    with pytest.raises(ValueError):
        baseline.update("u1", np.zeros(FEATURE_DIM - 1, dtype=np.float32))
    with pytest.raises(ValueError):
        baseline.update_batch("u1", np.zeros((5, FEATURE_DIM - 1), dtype=np.float32))
