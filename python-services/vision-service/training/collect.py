"""Webcam'den landmark dizisi (sequence) toplar ve npz olarak kaydeder.

Her dizi ardışık `window` karenin landmark özellik vektöründen oluşur: kareler
vision pipeline'ından (VisionAnalysisService) geçirilir ve features_from_response
ile vektörleştirilir. Yeni diziler mevcut npz ile birleştirilir.

Kullanım:
    python -m training.collect --label smoking_like_gesture --sequences 20 --window 16 --out data/sequences.npz

Çıktı npz: sequences (N, window, FEATURE_DIM) float32, labels (N,) int64.
Gizlilik: kaydedilen şey landmark özellik vektörleridir — ham görüntü değil.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from app.schemas.vision import VisionAnalysisRequest
from app.services.vision_analysis_service import VisionAnalysisService
from evaluation.labels import LABELS
from training.landmark_features import FEATURE_DIM, features_from_response


async def _frame_features(
    service: VisionAnalysisService,
    frame: np.ndarray,
    session_id: str,
    frame_id: str,
) -> np.ndarray:
    ok, encoded = cv2.imencode(".jpg", frame)
    if not ok:
        return np.zeros(FEATURE_DIM, dtype=np.float32)
    request = VisionAnalysisRequest(
        request_id=f"collect-{frame_id}",
        user_id="collect-user",
        session_id=session_id,
        frame_id=frame_id,
        captured_at=datetime.now(tz=timezone.utc),
        image_base64=base64.b64encode(encoded.tobytes()).decode("utf-8"),
        image_content_type="image/jpeg",
    )
    response = await service.analyze(request)
    return features_from_response(response)


async def _collect(args: argparse.Namespace, service: VisionAnalysisService, capture: cv2.VideoCapture) -> list[np.ndarray]:
    collected: list[np.ndarray] = []
    for seq_index in range(args.sequences):
        session_id = f"collect-{args.label}-{seq_index}"
        frames: list[np.ndarray] = []
        for frame_index in range(args.window):
            ok, frame = capture.read()
            if not ok:
                continue
            features = await _frame_features(service, frame, session_id, f"{seq_index}-{frame_index}")
            frames.append(features)
            time.sleep(max(0.0, args.interval))
        if len(frames) == args.window:
            collected.append(np.stack(frames))
            print(f"[{len(collected)}/{args.sequences}] dizi toplandı")
    return collected


def _merge_npz(out_path: str | Path, new_sequences: np.ndarray, new_labels: np.ndarray) -> int:
    out_path = Path(out_path)
    if out_path.exists():
        existing = np.load(out_path)
        sequences = np.concatenate([existing["sequences"], new_sequences], axis=0)
        labels = np.concatenate([existing["labels"], new_labels], axis=0)
    else:
        sequences, labels = new_sequences, new_labels
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_path, sequences=sequences, labels=labels)
    return int(len(labels))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Webcam'den landmark dizisi topla")
    parser.add_argument("--label", required=True, choices=LABELS, help="Bu oturumun davranış sınıfı")
    parser.add_argument("--sequences", type=int, default=20, help="Toplanacak dizi sayısı")
    parser.add_argument("--window", type=int, default=16, help="Dizi başına kare sayısı")
    parser.add_argument("--interval", type=float, default=0.1, help="Kareler arası bekleme (saniye)")
    parser.add_argument("--out", default="data/sequences.npz", help="Çıktı npz yolu")
    parser.add_argument("--camera", type=int, default=0, help="Kamera cihaz indeksi")
    args = parser.parse_args(argv)

    label_index = LABELS.index(args.label)
    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        print(f"HATA: kamera {args.camera} açılamadı", file=sys.stderr)
        return 1

    service = VisionAnalysisService()
    print(f"'{args.label}' için {args.sequences} dizi × {args.window} kare toplanıyor — davranışı sergile.")
    try:
        collected = asyncio.run(_collect(args, service, capture))
    finally:
        capture.release()

    if not collected:
        print("Hiç dizi toplanamadı.", file=sys.stderr)
        return 1

    new_sequences = np.stack(collected).astype(np.float32)
    new_labels = np.full(len(collected), label_index, dtype=np.int64)
    total = _merge_npz(args.out, new_sequences, new_labels)
    print(f"\n{len(collected)} dizi eklendi → {args.out} (toplam {total} dizi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
