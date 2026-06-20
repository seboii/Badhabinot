"""YOLOv8 modellerini ONNX'e dışa aktarma yardımcısı (CPU optimizasyonu).

ONNX Runtime, CPU üzerinde YOLOv8n için genellikle saf PyTorch'tan hızlıdır ve
daha az bellek kullanır. Bu script pose + nesne modellerini ONNX'e çevirir;
ardından env ile servise gösterilir:

    VISION_POSE_MODEL=yolov8n-pose.onnx
    VISION_DETECT_MODEL=yolov8n.onnx

Kullanım (önce: pip install onnx onnxruntime):

    python scripts/export_yolo_onnx.py
    python scripts/export_yolo_onnx.py --imgsz 512 --models yolov8n-pose.pt yolov8n.pt

Not: ultralytics, ".onnx" yolu verildiğinde modeli otomatik ONNX Runtime ile
çalıştırır; ayrıca kod değişikliği gerekmez.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Export YOLOv8 models to ONNX")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["yolov8n-pose.pt", "yolov8n.pt"],
        help="Dışa aktarılacak .pt model dosyaları",
    )
    parser.add_argument("--imgsz", type=int, default=640, help="Giriş çözünürlüğü")
    parser.add_argument(
        "--opset", type=int, default=12, help="ONNX opset sürümü"
    )
    parser.add_argument(
        "--simplify", action="store_true", help="onnx-simplifier ile sadeleştir"
    )
    args = parser.parse_args()

    try:
        from ultralytics import YOLO  # type: ignore[import-untyped]
    except ImportError:
        print("HATA: ultralytics kurulu değil. `pip install ultralytics`", file=sys.stderr)
        return 1

    for model_path in args.models:
        print(f"→ {model_path} dışa aktarılıyor (imgsz={args.imgsz})…")
        model = YOLO(model_path)
        out = model.export(
            format="onnx",
            imgsz=args.imgsz,
            opset=args.opset,
            simplify=args.simplify,
            dynamic=False,
        )
        print(f"  ✓ {out}")

    print("\nTamam. .env içine ekleyin:")
    print("  VISION_POSE_MODEL=yolov8n-pose.onnx")
    print("  VISION_DETECT_MODEL=yolov8n.onnx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
