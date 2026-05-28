"""sequences.npz dosyasını train/val/test'e böler (stratified, deterministik).

Bir sınıfın tüm dizilerinin aynı bölüme düşmesi yerine, her sınıf hem train
hem val hem test'te orantılı olarak temsil edilir (stratified split). Bu,
küçük veri setlerinde dengesiz ayrımı önler.

Kullanım:
    python -m tools.split_dataset --input data/sequences.npz --out-dir data/
    # data/train.npz, data/val.npz, data/test.npz üretir

Varsayılan oran: %70 train, %15 val, %15 test.
Tohum sabitlemesi (--seed) sayesinde aynı girdi her zaman aynı bölünmeyi verir.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from evaluation.labels import LABELS


def stratified_split(
    sequences: np.ndarray,
    labels: np.ndarray,
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
    """Stratified split — her sınıf için orantılı bölüm."""
    rng = np.random.default_rng(seed)
    train_idx_list: list[int] = []
    val_idx_list: list[int] = []
    test_idx_list: list[int] = []

    for cls in range(len(LABELS)):
        cls_indices = np.where(labels == cls)[0]
        rng.shuffle(cls_indices)
        n = len(cls_indices)
        n_train = int(round(n * train_ratio))
        n_val = int(round(n * val_ratio))
        # Kalan test'e gider — yuvarlama farkı sığar
        train_idx_list.extend(cls_indices[:n_train].tolist())
        val_idx_list.extend(cls_indices[n_train : n_train + n_val].tolist())
        test_idx_list.extend(cls_indices[n_train + n_val :].tolist())

    train_idx = np.array(sorted(train_idx_list), dtype=np.int64)
    val_idx = np.array(sorted(val_idx_list), dtype=np.int64)
    test_idx = np.array(sorted(test_idx_list), dtype=np.int64)

    return (
        (sequences[train_idx], labels[train_idx]),
        (sequences[val_idx], labels[val_idx]),
        (sequences[test_idx], labels[test_idx]),
    )


def _print_distribution(name: str, labels: np.ndarray) -> None:
    counts = {LABELS[c]: int((labels == c).sum()) for c in range(len(LABELS))}
    total = int(len(labels))
    print(f"  {name:<6}  (n={total}):  " + ", ".join(f"{k}={v}" for k, v in counts.items()))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="sequences.npz → train/val/test stratified split")
    parser.add_argument("--input", required=True, help="Girdi npz (collect.py çıktısı)")
    parser.add_argument("--out-dir", default="data", help="Çıktı dizini")
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42, help="Tohum (deterministik bölünme)")
    args = parser.parse_args(argv)

    test_ratio = 1.0 - args.train - args.val
    if test_ratio <= 0:
        print(f"HATA: train+val={args.train + args.val} → test için yer kalmadı", file=sys.stderr)
        return 1

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"HATA: girdi yok: {in_path}", file=sys.stderr)
        return 1

    data = np.load(in_path)
    sequences = data["sequences"]
    labels = data["labels"]
    print(f"Girdi: {in_path} → shape {sequences.shape}, sınıf sayısı {len(LABELS)}")
    _print_distribution("toplam", labels)

    # Her sınıfta en az 3 örnek gerekir (1 train + 1 val + 1 test minimum)
    for cls in range(len(LABELS)):
        n = int((labels == cls).sum())
        if n < 3:
            print(f"UYARI: '{LABELS[cls]}' için yalnızca {n} örnek; stratified split anlamlı olmayabilir.")

    train, val, test = stratified_split(sequences, labels, args.train, args.val, args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(out_dir / "train.npz", sequences=train[0], labels=train[1])
    np.savez(out_dir / "val.npz", sequences=val[0], labels=val[1])
    np.savez(out_dir / "test.npz", sequences=test[0], labels=test[1])

    print(f"\nBölünme oranları: train={args.train}, val={args.val}, test={round(test_ratio, 4)}")
    print(f"Tohum: {args.seed}\n")
    _print_distribution("train", train[1])
    _print_distribution("val", val[1])
    _print_distribution("test", test[1])
    print(f"\nÇıktı: {out_dir}/{{train,val,test}}.npz")
    return 0


if __name__ == "__main__":
    sys.exit(main())
