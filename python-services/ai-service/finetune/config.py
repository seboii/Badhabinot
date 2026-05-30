"""Fine-tune yapılandırması — donanıma (VRAM) göre taban model + hiperparametre.

Yerel GPU tespiti (bu projede): NVIDIA RTX 4050 Laptop = 6 GB VRAM.
6 GB ile 7B QLoRA pratik DEĞİLDİR (~10-12 GB ister) → varsayılan profil
``local-6gb`` (Qwen2.5-1.5B). 7B fine-tune için ``cloud-16gb`` profilini
bir bulut GPU'da (Colab/Kaggle T4 16 GB) kullan — betikler aynıdır.

Profili ortam değişkeniyle de seçebilirsin:  FINETUNE_PROFILE=local-8gb
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("FINETUNE_DATA_DIR", str(_ROOT / "data")))
OUTPUT_DIR = Path(os.getenv("FINETUNE_OUTPUT_DIR", str(_ROOT / "outputs")))

# Donanım profilleri: VRAM → güvenli taban model + sekans/batch ayarları.
# 4-bit QLoRA varsayımıyla yaklaşık VRAM ihtiyacı:
#   1.5B ≈ 4-5 GB | 3B ≈ 6-7 GB (sıkı) | 7B ≈ 10-12 GB
VRAM_PRESETS: dict[str, dict[str, object]] = {
    "local-6gb": {
        "base_model": "Qwen/Qwen2.5-1.5B-Instruct",
        "max_seq_len": 1024,
        "load_in_4bit": True,
        "per_device_batch_size": 1,
        "grad_accum": 16,
    },
    "local-8gb": {
        "base_model": "Qwen/Qwen2.5-3B-Instruct",
        "max_seq_len": 1024,
        "load_in_4bit": True,
        "per_device_batch_size": 1,
        "grad_accum": 16,
    },
    "cloud-16gb": {
        "base_model": "Qwen/Qwen2.5-7B-Instruct",
        "max_seq_len": 2048,
        "load_in_4bit": True,
        "per_device_batch_size": 1,
        "grad_accum": 8,
    },
}
DEFAULT_PROFILE = os.getenv("FINETUNE_PROFILE", "local-6gb")


@dataclass
class FinetuneConfig:
    """Tek yerden tüm fine-tune ayarları. ``from_profile`` ile donanıma göre kur."""

    profile: str = DEFAULT_PROFILE
    base_model: str = "Qwen/Qwen2.5-1.5B-Instruct"

    # ── LoRA / QLoRA ────────────────────────────────────────────────────────
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Qwen2.5 attention + MLP projeksiyonları
    target_modules: tuple[str, ...] = (
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    )
    load_in_4bit: bool = True

    # ── Eğitim ──────────────────────────────────────────────────────────────
    max_seq_len: int = 1024
    per_device_batch_size: int = 1
    grad_accum: int = 16          # efektif batch = batch_size * grad_accum
    learning_rate: float = 2e-4
    num_epochs: float = 3.0
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    lr_scheduler_type: str = "cosine"
    logging_steps: int = 10
    save_steps: int = 200
    val_ratio: float = 0.1
    seed: int = 42

    # ── Yollar / çıktı ──────────────────────────────────────────────────────
    dataset_path: Path = field(default_factory=lambda: DATA_DIR / "coaching_dataset.jsonl")
    prepared_dir: Path = field(default_factory=lambda: DATA_DIR / "prepared")
    adapter_dir: Path = field(default_factory=lambda: OUTPUT_DIR / "lora-adapter")
    merged_dir: Path = field(default_factory=lambda: OUTPUT_DIR / "merged-fp16")
    gguf_path: Path = field(default_factory=lambda: OUTPUT_DIR / "badhabinot-coach.gguf")
    ollama_model_name: str = "badhabinot-coach:latest"

    @classmethod
    def from_profile(cls, profile: str | None = None, **overrides: object) -> "FinetuneConfig":
        """Bir VRAM profilinden config üret; ``overrides`` ile tek tek alan ezilebilir."""
        profile = profile or DEFAULT_PROFILE
        preset = VRAM_PRESETS.get(profile)
        if preset is None:
            raise ValueError(
                f"Bilinmeyen profil: {profile!r}. Seçenekler: {sorted(VRAM_PRESETS)}"
            )
        values: dict[str, object] = {"profile": profile, **preset, **overrides}
        return cls(**values)  # type: ignore[arg-type]

    @property
    def effective_batch_size(self) -> int:
        return int(self.per_device_batch_size) * int(self.grad_accum)

    def to_json(self) -> str:
        d = asdict(self)
        # Path → str (JSON-serileştirilebilir)
        for k, v in d.items():
            if isinstance(v, Path):
                d[k] = str(v)
            if isinstance(v, tuple):
                d[k] = list(v)
        return json.dumps(d, ensure_ascii=False, indent=2)

    def ensure_dirs(self) -> None:
        for p in (DATA_DIR, OUTPUT_DIR, self.prepared_dir, self.adapter_dir):
            Path(p).mkdir(parents=True, exist_ok=True)


def detect_suggested_profile() -> str:
    """nvidia-smi'den boş VRAM'e göre profil önerir; bulunamazsa varsayılan döner.

    Saf bilgilendirme amaçlı — eğitim betiği yine de ``FINETUNE_PROFILE`` /
    ``--profile`` değerini kullanır.
    """
    try:
        import subprocess

        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip().splitlines()
        total_mib = max(int(x) for x in out if x.strip())
        gb = total_mib / 1024
        if gb >= 15:
            return "cloud-16gb"
        if gb >= 7.5:
            return "local-8gb"
        return "local-6gb"
    except Exception:
        return DEFAULT_PROFILE
