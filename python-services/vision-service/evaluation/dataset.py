"""Etiketli değerlendirme veri setini JSONL manifest'ten okur.

Manifest formatı — her satır bir JSON nesnesi::

    {"image": "frames/0001.jpg", "label": "poor_posture", "frame_id": "0001"}

`image` yolları manifest dosyasının bulunduğu dizine görelidir. Boş satırlar ve
`#` ile başlayan satırlar (yorum) yok sayılır.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from evaluation.labels import LABELS


@dataclass(frozen=True)
class Sample:
    image_path: Path
    label: str
    frame_id: str


def load_manifest(manifest_path: str | Path) -> list[Sample]:
    """Manifest'i okur ve doğrular; geçersiz etiket/eksik alan ValueError verir."""
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest bulunamadı: {manifest_path}")

    base_dir = manifest_path.parent
    samples: list[Sample] = []
    with manifest_path.open("r", encoding="utf-8") as handle:
        for line_no, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"satır {line_no}: geçersiz JSON ({exc})") from exc

            label = record.get("label")
            if label not in LABELS:
                raise ValueError(
                    f"satır {line_no}: bilinmeyen etiket {label!r}; izinli sınıflar: {LABELS}"
                )
            image = record.get("image")
            if not image:
                raise ValueError(f"satır {line_no}: 'image' alanı zorunlu")

            samples.append(Sample(
                image_path=(base_dir / image).resolve(),
                label=label,
                frame_id=str(record.get("frame_id", f"frame-{line_no}")),
            ))

    if not samples:
        raise ValueError(f"manifest boş: {manifest_path}")
    return samples


def label_distribution(samples: list[Sample]) -> dict[str, int]:
    """Sınıf başına örnek sayısı — dengesizliği raporlamak için."""
    counts = {label: 0 for label in LABELS}
    for sample in samples:
        counts[sample.label] += 1
    return counts
