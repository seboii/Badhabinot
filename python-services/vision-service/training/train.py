"""Landmark sequence classifier eğitimi (PyTorch).

Kullanım:
    python -m training.train --data data/sequences.npz --epochs 30 --out model.pt

Her epoch sonunda train loss ve doğrulama (val) accuracy basar; eğitilmiş modeli
özellik boyutu ve sınıf listesiyle birlikte kaydeder. Faz 1 değerlendirme
harness'ıyla aynı sınıf kümesini (evaluation.labels.LABELS) kullanır.
"""

from __future__ import annotations

import argparse
import sys

import torch
from torch.utils.data import DataLoader, random_split

from evaluation.labels import LABELS
from training.landmark_features import FEATURE_DIM
from training.model import LandmarkSequenceClassifier
from training.sequence_dataset import LandmarkSequenceDataset


def train(
    data_path: str,
    *,
    epochs: int = 30,
    batch_size: int = 16,
    lr: float = 1e-3,
    val_split: float = 0.2,
    out_path: str = "model.pt",
    seed: int = 42,
) -> str:
    torch.manual_seed(seed)
    dataset = LandmarkSequenceDataset(data_path)
    n_val = max(1, int(len(dataset) * val_split))
    n_train = max(1, len(dataset) - n_val)
    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(dataset, [n_train, n_val], generator=generator)
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=batch_size)

    model = LandmarkSequenceClassifier(FEATURE_DIM, len(LABELS))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(1, epochs + 1):
        model.train()
        running = 0.0
        for sequences, labels in train_dl:
            optimizer.zero_grad()
            loss = criterion(model(sequences), labels)
            loss.backward()
            optimizer.step()
            running += loss.item() * len(labels)
        train_loss = running / max(n_train, 1)

        model.eval()
        correct = 0
        with torch.no_grad():
            for sequences, labels in val_dl:
                correct += (model(sequences).argmax(dim=1) == labels).sum().item()
        val_acc = correct / max(n_val, 1)
        print(f"epoch {epoch:3d}  train_loss {train_loss:.4f}  val_acc {val_acc:.4f}")

    torch.save(
        {"state_dict": model.state_dict(), "feature_dim": FEATURE_DIM, "labels": LABELS},
        out_path,
    )
    print(f"Model kaydedildi: {out_path}")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Landmark sequence classifier eğitimi")
    parser.add_argument("--data", required=True, help="npz veri seti (sequences, labels)")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--out", default="model.pt")
    args = parser.parse_args(argv)
    train(
        args.data,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        out_path=args.out,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
