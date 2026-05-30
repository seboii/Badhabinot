"""JSONL veri setini tokenizer chat-template ile metne çevirir ve böler.

Çıktı: ``prepared/`` altına kaydedilmiş bir HF DatasetDict (train/val), "text"
sütunu modelin sohbet şablonuna göre biçimlenmiş tam diyalogu içerir. train_lora.py
bunu doğrudan SFTTrainer'a verir.

KULLANIM:
    python -m finetune.prepare                     # varsayılan profil + yollar
    python -m finetune.prepare --profile local-8gb

Bağımlılık: transformers, datasets (requirements-finetune.txt).
"""

from __future__ import annotations

import argparse
import sys

from .config import FinetuneConfig
from .prompt_format import build_chat_messages
from .schema import load_jsonl


def prepare(config: FinetuneConfig) -> str:
    from datasets import Dataset, DatasetDict  # noqa: PLC0415 — ağır import
    from transformers import AutoTokenizer  # noqa: PLC0415

    config.ensure_dirs()
    examples = load_jsonl(config.dataset_path)
    if not examples:
        raise SystemExit(f"Veri seti boş: {config.dataset_path}. Önce build_dataset çalıştır.")

    tokenizer = AutoTokenizer.from_pretrained(config.base_model, trust_remote_code=True)

    texts: list[str] = []
    for ex in examples:
        messages = build_chat_messages(ex)
        # add_generation_prompt=False → asistan cevabı zaten messages'ta (eğitim hedefi)
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append(text)

    ds = Dataset.from_dict({"text": texts})
    split = ds.train_test_split(test_size=config.val_ratio, seed=config.seed)
    dataset = DatasetDict({"train": split["train"], "val": split["test"]})
    dataset.save_to_disk(str(config.prepared_dir))

    print(f"Hazırlandı: train={len(dataset['train'])} val={len(dataset['val'])}")
    print(f"Kaydedildi: {config.prepared_dir}")
    print(f"Taban model/tokenizer: {config.base_model}")
    return str(config.prepared_dir)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Veri setini fine-tune için hazırla")
    ap.add_argument("--profile", default=None, help="VRAM profili (config.VRAM_PRESETS)")
    ap.add_argument("--dataset", default=None, help="JSONL yolu (varsayılan: config)")
    args = ap.parse_args(argv)

    config = FinetuneConfig.from_profile(args.profile)
    if args.dataset:
        from pathlib import Path
        config.dataset_path = Path(args.dataset)
    prepare(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
