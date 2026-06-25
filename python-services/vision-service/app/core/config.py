import os
from pathlib import Path

from dotenv import load_dotenv


def _load_root_dotenv() -> None:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".env"
        if candidate.exists():
            load_dotenv(candidate, override=False)
            break


_load_root_dotenv()


def _env_int(name: str, default: int) -> int:
    """Güvenli int parse — boş/bozuk değerde varsayılana düşer."""
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    app_name: str = "vision-service"
    app_version: str = "2.0.0"
    internal_api_key: str = os.getenv("INTERNAL_API_KEY", "change-me-in-real-environments")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # ──────────────────────────────────────────────────────────────────────
    # Performans / optimizasyon ayarları
    #
    # Servis arka planda sürekli çalıştığı için ağır modülleri her karede
    # çalıştırmak işlemciyi boğar. Aşağıdaki ayarlar; (1) kareyi küçülterek,
    # (2) yavaş değişen modülleri "frame skipping" ile seyrek çalıştırarak,
    # (3) thread sayısını sınırlayarak yükü düşürür. Hepsi env ile ayarlanır.
    # ──────────────────────────────────────────────────────────────────────

    # Çıkarım öncesi karenin en uzun kenarı bu piksele indirgenir (asla
    # büyütülmez). 640, YOLO/MediaPipe için yeterli, maliyeti ~4x düşürür.
    vision_max_dim: int = _env_int("VISION_MAX_DIM", 640)

    # Frame skipping aralıkları — modül her N karede bir çalışır, aradaki
    # karelerde önbellekteki son sonuç kullanılır. 1 = her kare.
    # Yüz kimliği (DeepFace) tek tek en pahalı modül; kimlik kare kare
    # değişmediği için en agresif atlanan modüldür.
    vision_owner_id_interval: int = _env_int("VISION_OWNER_ID_INTERVAL", 4)
    vision_object_interval: int = _env_int("VISION_OBJECT_INTERVAL", 3)
    vision_gaze_interval: int = _env_int("VISION_GAZE_INTERVAL", 2)
    vision_pose_interval: int = _env_int("VISION_POSE_INTERVAL", 1)
    vision_mesh_interval: int = _env_int("VISION_MESH_INTERVAL", 1)
    vision_hand_interval: int = _env_int("VISION_HAND_INTERVAL", 1)

    # Nesne tespiti (YOLOv8) model dosyası — ".onnx" uzantısı verilirse ONNX
    # Runtime üzerinden çalışır (bkz. scripts/export_yolo_onnx.py). Varsayılan
    # PyTorch (.pt). Postür artık YOLO değil MediaPipe Pose ile yapılır.
    vision_detect_model: str = os.getenv("VISION_DETECT_MODEL", "yolov8n.pt")
    vision_detect_imgsz: int = _env_int("VISION_DETECT_IMGSZ", 640)

    # MediaPipe Pose (postür iskeleti) — YOLOv8-pose yerine.
    #   complexity: 0 (en hızlı) / 1 (denge) / 2 (en doğru, en yavaş).
    #   min_confidence: kişi tespiti için minimum güven.
    posture_pose_complexity: int = _env_int("POSTURE_POSE_COMPLEXITY", 1)
    posture_pose_min_confidence: float = _env_float("POSTURE_POSE_MIN_CONFIDENCE", 0.5)

    # CPU thread tavanı (0 = dokunma/torch varsayılanı). Nesne tespiti YOLO'su
    # için geçerli; eş zamanlı isteklerde oversubscription'ı önlemek için 2-4.
    vision_torch_threads: int = _env_int("VISION_TORCH_THREADS", 0)

    # ──────────────────────────────────────────────────────────────────────
    # Postür değerlendirme eşikleri
    #
    # "Düzgün postür" = omuz hizası düz + baş omuzların üstünde + ekrana
    # makul mesafe. Eşikler omuz genişliğine göre normalize edildiği için
    # mesafeden bağımsızdır. Skor 0-100; eşiğin altı "poor".
    # ──────────────────────────────────────────────────────────────────────
    posture_poor_score: int = _env_int("POSTURE_POOR_SCORE", 70)

    # Öne eğik baş (kamburluk) — başın omuz üstündeki dikey yükseklik / omuz
    # genişliği oranı. Bu orandan büyük = iyi; küçüldükçe ceza artar.
    posture_forward_good: float = _env_float("POSTURE_FORWARD_GOOD", 0.50)
    posture_forward_bad: float = _env_float("POSTURE_FORWARD_BAD", 0.20)

    # Yana yatma — başın omuz orta noktasından yatay sapması / omuz genişliği.
    posture_lateral_good: float = _env_float("POSTURE_LATERAL_GOOD", 0.14)
    posture_lateral_bad: float = _env_float("POSTURE_LATERAL_BAD", 0.42)

    # Omuz eğikliği (derece, yataydan sapma).
    posture_shoulder_good_deg: float = _env_float("POSTURE_SHOULDER_GOOD_DEG", 6.0)
    posture_shoulder_bad_deg: float = _env_float("POSTURE_SHOULDER_BAD_DEG", 18.0)

    # Baş eğikliği / roll (derece, göz hattının yataydan sapması).
    posture_roll_good_deg: float = _env_float("POSTURE_ROLL_GOOD_DEG", 8.0)
    posture_roll_bad_deg: float = _env_float("POSTURE_ROLL_BAD_DEG", 26.0)

    # Ekrana çok yakınlık — omuz genişliği / kare genişliği bu oranı aşarsa
    # kullanıcı ekrana fazla yaklaşmış demektir.
    posture_proximity_close: float = _env_float("POSTURE_PROXIMITY_CLOSE", 0.62)
    posture_proximity_max: float = _env_float("POSTURE_PROXIMITY_MAX", 0.82)

    # Başı aşağı eğme (burun, kulak hattının altına ne kadar düşmüş / omuz gen.)
    posture_head_down_good: float = _env_float("POSTURE_HEAD_DOWN_GOOD", 0.30)
    posture_head_down_bad: float = _env_float("POSTURE_HEAD_DOWN_BAD", 0.70)

    # Skor yumuşatma (EMA) katsayısı — tek karelik gürültünün durumu
    # iyi↔kötü diye sıçratmasını engeller. 1.0 = yumuşatma yok.
    posture_smoothing_alpha: float = _env_float("POSTURE_SMOOTHING_ALPHA", 0.4)


settings = Settings()
