"""Faz 3 — Kullanıcıya özel landmark baseline; z-skoru ile anomali tespiti.

Her kullanıcının "normal" davranışı farklıdır (ör. ortalama duruş açısı,
tipik el konumu). Bu modül, kullanıcı oturumlarından gelen landmark
özelliklerinin kayan ortalama/varyansını Welford algoritmasıyla saklar.
Yeni bir kare geldiğinde kişiye özel z-skoru ile normal-dışı davranışları
saptayabilir — global sabit eşiklere bağlı kalmaz.

Gizlilik: Ham görüntü kaydedilmez; sadece özellik vektörü istatistikleri
(ortalama + ikinci-moment toplamı + sayım) saklanır.

Kullanım (Python):
    from training.personalizer import UserBaseline
    baseline = UserBaseline(data_dir="data/baselines")
    for frame_features in normal_session:
        baseline.update("user-123", frame_features)
    score = baseline.anomaly_score("user-123", new_frame)   # 0.0 = normal

Kullanım (CLI):
    python -m training.personalizer --user user-123 --stats
    python -m training.personalizer --user user-123 --check sequences.npz --index 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from training.landmark_features import FEATURE_DIM, FEATURE_NAMES

_MIN_SAMPLES_FOR_SCORING = 30


class UserBaseline:
    """Kullanıcı başına landmark istatistikleri (Welford online).

    data_dir: Kullanıcı başına npz dosyalarının saklanacağı dizin.
    """

    def __init__(self, data_dir: str | Path = "data/baselines") -> None:
        self._dir = Path(data_dir)

    # ── Güncelleme ─────────────────────────────────────────────────────────────

    def update(self, user_id: str, feature_vector: np.ndarray) -> None:
        """Welford online ortalama + ikinci moment güncelleme.

        feature_vector: (FEATURE_DIM,) float32/float64 vektör.
        """
        fv = self._validated(feature_vector)
        state = self._load(user_id)
        n = state["n"] + 1
        delta = fv - state["mean"]
        mean = state["mean"] + delta / n
        delta2 = fv - mean
        m2 = state["M2"] + delta * delta2
        self._save(user_id, {"n": n, "mean": mean, "M2": m2})

    def update_batch(self, user_id: str, sequences: np.ndarray) -> None:
        """sequences: (N, FEATURE_DIM) veya (N, T, FEATURE_DIM) — düzleştirilip eklenir."""
        arr = np.asarray(sequences, dtype=np.float64)
        if arr.ndim == 3:
            arr = arr.reshape(-1, arr.shape[-1])
        if arr.ndim != 2 or arr.shape[-1] != FEATURE_DIM:
            raise ValueError(
                f"sequences şekli (N,{FEATURE_DIM}) veya (N,T,{FEATURE_DIM}) olmalı, geldi: {arr.shape}"
            )
        for row in arr:
            self.update(user_id, row)

    # ── Sorgulama ──────────────────────────────────────────────────────────────

    def anomaly_score(self, user_id: str, feature_vector: np.ndarray) -> float:
        """Tüm özellikler üzerinden ortalama |z|. Yüksek = normal-dışı.

        _MIN_SAMPLES_FOR_SCORING'dan az örnek varsa 0.0 döner (henüz kararlı değil).
        """
        state = self._load(user_id)
        if state["n"] < _MIN_SAMPLES_FOR_SCORING:
            return 0.0
        fv = self._validated(feature_vector)
        z = self._z_vector(fv, state)
        return float(z.mean())

    def top_deviations(
        self,
        user_id: str,
        feature_vector: np.ndarray,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """En yüksek |z| skoruna sahip özellikleri (ad, skor) olarak döndürür."""
        state = self._load(user_id)
        if state["n"] < _MIN_SAMPLES_FOR_SCORING:
            return []
        fv = self._validated(feature_vector)
        z = self._z_vector(fv, state)
        order = np.argsort(z)[::-1][:top_k]
        return [(FEATURE_NAMES[i], float(z[i])) for i in order]

    def is_ready(self, user_id: str) -> bool:
        return self._load(user_id)["n"] >= _MIN_SAMPLES_FOR_SCORING

    def sample_count(self, user_id: str) -> int:
        return int(self._load(user_id)["n"])

    def reset(self, user_id: str) -> None:
        path = self._dir / f"{user_id}.npz"
        if path.exists():
            path.unlink()

    # ── İç yardımcılar ─────────────────────────────────────────────────────────

    @staticmethod
    def _validated(feature_vector: np.ndarray) -> np.ndarray:
        fv = np.asarray(feature_vector, dtype=np.float64)
        if fv.shape != (FEATURE_DIM,):
            raise ValueError(f"feature_vector şekli ({FEATURE_DIM},) olmalı, geldi: {fv.shape}")
        return fv

    @staticmethod
    def _z_vector(fv: np.ndarray, state: dict) -> np.ndarray:
        variance = state["M2"] / max(state["n"], 1)
        std = np.sqrt(variance + 1e-8)
        return np.abs((fv - state["mean"]) / std)

    def _load(self, user_id: str) -> dict:
        path = self._dir / f"{user_id}.npz"
        if path.exists():
            data = np.load(path)
            return {
                "n": int(data["n"]),
                "mean": data["mean"].copy(),
                "M2": data["M2"].copy(),
            }
        return {
            "n": 0,
            "mean": np.zeros(FEATURE_DIM, dtype=np.float64),
            "M2": np.zeros(FEATURE_DIM, dtype=np.float64),
        }

    def _save(self, user_id: str, state: dict) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / f"{user_id}.npz"
        np.savez(path, n=np.array(state["n"]), mean=state["mean"], M2=state["M2"])


# ── CLI ───────────────────────────────────────────────────────────────────────

def _print_stats(baseline: UserBaseline, user_id: str) -> None:
    state = baseline._load(user_id)
    n = state["n"]
    print(f"Kullanıcı: {user_id}")
    print(f"  Toplam örnek    : {n}")
    print(f"  Skorlamaya hazır : {'evet' if n >= _MIN_SAMPLES_FOR_SCORING else f'hayır (≥{_MIN_SAMPLES_FOR_SCORING} gerekli)'}")
    if n == 0:
        return
    variance = state["M2"] / max(n, 1)
    std = np.sqrt(variance + 1e-8)
    spread = std.mean()
    print(f"  Ortalama std     : {spread:.4f}")
    most_variable = np.argsort(std)[::-1][:5]
    print("  En değişken özellikler:")
    for idx in most_variable:
        print(f"    • {FEATURE_NAMES[idx]:<28} std={std[idx]:.4f}  mean={state['mean'][idx]:.4f}")


def _print_check(baseline: UserBaseline, user_id: str, data_path: str, index: int) -> int:
    data = np.load(data_path)
    if "sequences" not in data.files:
        print(f"HATA: {data_path} 'sequences' anahtarı içermiyor", file=sys.stderr)
        return 1
    sequences = data["sequences"]
    if index < 0 or index >= len(sequences):
        print(f"HATA: index {index} aralık dışı (0–{len(sequences) - 1})", file=sys.stderr)
        return 1
    # Pencerenin ortalama vektörünü baseline'a karşı ölç (dizi ortalama davranışı).
    fv = sequences[index].astype(np.float64).mean(axis=0)
    score = baseline.anomaly_score(user_id, fv)
    print(f"Kullanıcı: {user_id} | dizi index: {index}")
    if not baseline.is_ready(user_id):
        print(f"  (baseline henüz hazır değil — örnek sayısı: {baseline.sample_count(user_id)})")
        return 0
    print(f"  Anomali skoru (ortalama |z|): {score:.3f}")
    threshold = 2.0
    verdict = "normal-dışı" if score > threshold else "normal aralık"
    print(f"  Sonuç: {verdict} (eşik = {threshold:.1f})")
    print("  En sapma gösteren özellikler:")
    for name, z in baseline.top_deviations(user_id, fv):
        print(f"    • {name:<28} |z|={z:.3f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Kullanıcıya özel landmark baseline (Welford z-skoru)")
    parser.add_argument("--user", required=True, help="Kullanıcı kimliği")
    parser.add_argument("--data-dir", default="data/baselines", help="Baseline npz dizini")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stats", action="store_true", help="Mevcut baseline istatistiklerini yazdır")
    group.add_argument("--learn", help="sequences.npz dosyasından baseline'a öğret (tüm kareler)")
    group.add_argument("--check", help="sequences.npz içindeki bir diziyi baseline'a karşı kontrol et")
    group.add_argument("--reset", action="store_true", help="Bu kullanıcının baseline dosyasını sil")
    parser.add_argument("--index", type=int, default=0, help="--check için dizi indeksi")
    args = parser.parse_args(argv)

    baseline = UserBaseline(args.data_dir)

    if args.stats:
        _print_stats(baseline, args.user)
        return 0
    if args.reset:
        baseline.reset(args.user)
        print(f"Baseline silindi: {args.user}")
        return 0
    if args.learn:
        data = np.load(args.learn)
        sequences = data["sequences"]
        baseline.update_batch(args.user, sequences)
        print(f"{sequences.shape} → {args.user} baseline'a eklendi (toplam: {baseline.sample_count(args.user)})")
        return 0
    if args.check:
        return _print_check(baseline, args.user, args.check, args.index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
