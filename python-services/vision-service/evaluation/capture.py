"""Webcam'den etiketli değerlendirme kareleri toplar ve manifest'e ekler.

Kullanım:
    python -m evaluation.capture --label poor_posture --count 20 --out data
    python -m evaluation.capture --label normal --count 30 --interval 0.5

Her kare ``<out>/frames/`` altına JPEG kaydedilir ve ``<out>/labels.jsonl``
dosyasına bir satır eklenir. opencv-headless GUI desteklemediği için canlı
önizleme yoktur; kareler ``--interval`` saniye aralıkla yakalanır. Etiketleme
protokolü için bkz. README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2

from evaluation.labels import LABELS


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolunda Türkçe çıktı güvenliği
    except Exception:
        pass
    parser = argparse.ArgumentParser(description="Webcam'den etiketli değerlendirme karesi yakala")
    parser.add_argument("--label", required=True, choices=LABELS, help="Bu oturumda yakalanan karelerin sınıfı")
    parser.add_argument("--count", type=int, default=20, help="Yakalanacak kare sayısı")
    parser.add_argument("--interval", type=float, default=1.0, help="Kareler arası bekleme (saniye)")
    parser.add_argument("--out", default="data", help="Çıktı kök dizini")
    parser.add_argument("--camera", type=int, default=0, help="Kamera cihaz indeksi")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "labels.jsonl"

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        print(f"HATA: kamera {args.camera} açılamadı", file=sys.stderr)
        return 1

    print(f"'{args.label}' sınıfı için {args.count} kare yakalanıyor — pozisyonunu al.")
    written = 0
    try:
        with manifest_path.open("a", encoding="utf-8") as manifest:
            for i in range(args.count):
                ok, frame = capture.read()
                if not ok:
                    print(f"kare {i} okunamadı, atlanıyor", file=sys.stderr)
                    continue
                stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
                frame_id = f"{args.label}-{stamp}"
                rel_path = f"frames/{frame_id}.jpg"
                cv2.imwrite(str(out_dir / rel_path), frame)
                manifest.write(
                    json.dumps({"image": rel_path, "label": args.label, "frame_id": frame_id}) + "\n"
                )
                written += 1
                print(f"[{written}/{args.count}] {rel_path}")
                time.sleep(max(0.0, args.interval))
    finally:
        capture.release()

    print(f"\n{written} kare yazıldı → {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
