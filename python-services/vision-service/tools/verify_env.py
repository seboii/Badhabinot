"""Bitirme çalışmasına başlamadan önce ortamın hazır olduğunu doğrular.

Tüm runtime + eğitim bağımlılıklarını dener; webcam'i açar; modellerin
yüklenebildiğini test eder; PyTorch ile küçük bir tensör işlemi yapar.

Kullanım:
    python -m tools.verify_env             # tam kontrol
    python -m tools.verify_env --no-camera # kamerasız ortamda (CI vb.)
    python -m tools.verify_env --no-torch  # PyTorch kurulu olmasa da

Çıktı: her satır [OK]/[UYARI]/[HATA]; çıkış kodu 0 = hazır, 1 = eksik.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    warning: bool = False

    def render(self) -> str:
        tag = "[OK]   " if self.ok else ("[UYARI]" if self.warning else "[HATA] ")
        line = f"{tag} {self.name}"
        if self.detail:
            line += f" — {self.detail}"
        return line


def _check_import(module: str, *, optional: bool = False) -> CheckResult:
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, "__version__", "?")
        return CheckResult(f"import {module}", True, f"v{version}")
    except ImportError as exc:
        return CheckResult(f"import {module}", False, str(exc), warning=optional)


def _check_camera(index: int = 0) -> CheckResult:
    try:
        import cv2
    except ImportError:
        return CheckResult("webcam", False, "cv2 yüklü değil")
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        return CheckResult("webcam", False, f"kamera {index} açılamadı", warning=True)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return CheckResult("webcam", False, "kare okunamadı", warning=True)
    return CheckResult("webcam", True, f"kare boyutu {frame.shape[1]}x{frame.shape[0]}")


def _check_mediapipe_load() -> CheckResult:
    try:
        import mediapipe as mp
        # FaceMesh ve Hands gerçekten ilkleyebiliyor mu?
        mp.solutions.face_mesh.FaceMesh(max_num_faces=1).close()
        mp.solutions.hands.Hands(max_num_hands=2).close()
        return CheckResult("mediapipe init", True, "FaceMesh + Hands tamam")
    except Exception as exc:   # noqa: BLE001
        return CheckResult("mediapipe init", False, str(exc))


def _check_yolo_load() -> CheckResult:
    try:
        from ultralytics import YOLO
        # En küçük poz modelini yükle (gerekirse otomatik iner)
        YOLO("yolov8n-pose.pt")
        return CheckResult("yolo pose", True, "yolov8n-pose hazır")
    except Exception as exc:   # noqa: BLE001
        return CheckResult("yolo pose", False, str(exc), warning=True)


def _check_torch_compute() -> CheckResult:
    try:
        import torch
    except ImportError as exc:
        return CheckResult("torch compute", False, str(exc), warning=True)
    x = torch.randn(4, 16, 58)
    y = torch.nn.Conv1d(58, 32, 3)(x.transpose(1, 2))
    return CheckResult("torch compute", True, f"output shape {tuple(y.shape)}")


def _check_pipeline_packages() -> list[CheckResult]:
    """Bizim yazdığımız evaluation/training paketlerini import edebiliyor muyuz?"""
    targets = [
        "evaluation.labels",
        "evaluation.metrics",
        "training.landmark_features",
        "training.model",
        "training.personalizer",
        "training.insights",
    ]
    return [_check_import(t, optional=("training" in t)) for t in targets]


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="Bitirme ortamını doğrula")
    parser.add_argument("--no-camera", action="store_true", help="Webcam testini atla")
    parser.add_argument("--no-torch", action="store_true", help="PyTorch testini atla")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args(argv)

    results: list[CheckResult] = []

    print("=" * 60)
    print("Badhabinot bitirme — ortam doğrulama")
    print("=" * 60)

    runtime_libs = ["numpy", "cv2", "mediapipe", "ultralytics", "deepface", "tensorflow", "fastapi"]
    for lib in runtime_libs:
        results.append(_check_import(lib))

    if not args.no_torch:
        results.append(_check_import("torch", optional=True))
        results.append(_check_torch_compute())

    results.append(_check_mediapipe_load())
    results.append(_check_yolo_load())
    results.extend(_check_pipeline_packages())

    if not args.no_camera:
        results.append(_check_camera(args.camera_index))

    print()
    for r in results:
        print(r.render())
    print()

    failed = [r for r in results if not r.ok and not r.warning]
    warned = [r for r in results if not r.ok and r.warning]
    print(f"Toplam: {len(results)}  |  Geçti: {sum(1 for r in results if r.ok)}  "
          f"|  Hata: {len(failed)}  |  Uyarı: {len(warned)}")

    if failed:
        print("\n>>> Ortam HAZIR DEĞİL. Eksik bağımlılıkları kurup tekrar dene.")
        return 1
    if warned:
        print("\n>>> Ortam çoğunlukla hazır; uyarı verenler opsiyonel modüller "
              "(ör. eğitim için torch, webcam erişimi).")
    else:
        print("\n>>> Ortam HAZIR. `collect`, `train`, `evaluate` çalıştırabilirsin.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
