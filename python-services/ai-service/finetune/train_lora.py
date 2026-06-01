"""QLoRA fine-tune — qwen2.5 ailesi davranış koçluğu modeli.

4-bit taban (bitsandbytes) + LoRA adaptörü (peft) + SFTTrainer (trl). Adaptör
``outputs/lora-adapter`` altına kaydedilir; sonra merge_and_export.py ile
birleştirilip GGUF'a/Ollama'ya verilir.

KULLANIM:
    python -m finetune.prepare              # önce veri hazırla
    python -m finetune.train_lora           # sonra eğit (varsayılan local-6gb)
    python -m finetune.train_lora --profile cloud-16gb --epochs 3   # 7B (bulut GPU)

VRAM notu: local-6gb (1.5B) RTX 4050 6 GB'a sığar. 7B için cloud-16gb profili +
bir T4/A10 GPU gerekir. bitsandbytes Windows'ta >=0.43 ile desteklenir.

Bağımlılık: torch (CUDA), transformers, peft, trl, bitsandbytes, accelerate.
"""

from __future__ import annotations

import argparse
import sys

from .config import FinetuneConfig


def train(config: FinetuneConfig) -> str:
    # NOT (Windows): datasets/pyarrow torch'tan ÖNCE yüklenmeli; torch önce
    # yüklenirse 'import datasets' native çöker (DLL yükleme-sırası çakışması).
    from datasets import load_from_disk  # noqa: PLC0415
    import torch  # noqa: PLC0415
    from peft import LoraConfig, prepare_model_for_kbit_training  # noqa: PLC0415
    from transformers import (  # noqa: PLC0415
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from trl import SFTConfig, SFTTrainer  # noqa: PLC0415

    if not torch.cuda.is_available():
        print("UYARI: CUDA bulunamadı. QLoRA için GPU gerekir; CPU'da pratik değildir.")

    config.ensure_dirs()
    dataset = load_from_disk(str(config.prepared_dir))

    tokenizer = AutoTokenizer.from_pretrained(config.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = None
    if config.load_in_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model,
        quantization_config=quant_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
    )
    model.config.use_cache = False
    if config.load_in_4bit:
        model = prepare_model_for_kbit_training(model)
    else:
        # fp16/bf16 LoRA yolu (bitsandbytes yok): gradient checkpointing +
        # LoRA'nın çalışması için girdi gradyanlarını aç.
        model.enable_input_require_grads()

    lora_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=list(config.target_modules),
        bias="none",
        task_type="CAUSAL_LM",
    )

    sft_config = SFTConfig(
        output_dir=str(config.adapter_dir),
        per_device_train_batch_size=config.per_device_batch_size,
        gradient_accumulation_steps=config.grad_accum,
        learning_rate=config.learning_rate,
        num_train_epochs=config.num_epochs,
        warmup_ratio=config.warmup_ratio,
        weight_decay=config.weight_decay,
        lr_scheduler_type=config.lr_scheduler_type,
        logging_steps=config.logging_steps,
        save_steps=config.save_steps,
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        max_length=config.max_seq_len,  # trl 1.x: max_seq_length -> max_length
        completion_only_loss=True,       # kayıp yalnız asistan tamamlamasında (prompt maskeli)
        packing=False,                   # completion_only_loss ile packing kapalı olmalı
        seed=config.seed,
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset["train"],
        eval_dataset=dataset.get("val"),
        peft_config=lora_config,
        processing_class=tokenizer,
    )

    print(f"Eğitim başlıyor — taban={config.base_model} profil={config.profile} "
          f"efektif_batch={config.effective_batch_size}")
    trainer.train()
    trainer.save_model(str(config.adapter_dir))
    tokenizer.save_pretrained(str(config.adapter_dir))
    print(f"LoRA adaptörü kaydedildi: {config.adapter_dir}")
    return str(config.adapter_dir)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="QLoRA fine-tune")
    ap.add_argument("--profile", default=None, help="VRAM profili (config.VRAM_PRESETS)")
    ap.add_argument("--epochs", type=float, default=None)
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--lora-r", type=int, default=None)
    ap.add_argument("--no-4bit", action="store_true",
                    help="4-bit QLoRA yerine fp16/bf16 LoRA (bitsandbytes gerekmez)")
    ap.add_argument("--max-seq-len", type=int, default=None, help="Sekans uzunluğu (OOM'da düşür)")
    args = ap.parse_args(argv)

    overrides: dict[str, object] = {}
    if args.epochs is not None:
        overrides["num_epochs"] = args.epochs
    if args.lr is not None:
        overrides["learning_rate"] = args.lr
    if args.lora_r is not None:
        overrides["lora_r"] = args.lora_r
    if args.no_4bit:
        overrides["load_in_4bit"] = False
    if args.max_seq_len is not None:
        overrides["max_seq_len"] = args.max_seq_len

    config = FinetuneConfig.from_profile(args.profile, **overrides)
    print(config.to_json())
    train(config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
