"""Badhabinot — Türkçe davranış koçluğu LLM'i için QLoRA fine-tune iskeleti.

Mevcut chatbot, qwen2.5:7b tabanlı Ollama modeli + sistem promptu + sunucu
tarafı deterministik grounding'den ibarettir; *eğitilmiş* bir model değildir.
Bu paket, prompt-mühendisliğinden **fine-tune edilmiş, ölçülmüş** bir modele
geçişin uçtan uca iskeletini kurar:

    build_dataset → prepare → train_lora → merge_and_export → evaluate
                                                                  │
                                                          Ollama (GGUF)

Tasarım (vision-service/training desenini izler):
- config.py        — donanıma göre (VRAM profili) taban model + hiperparametre
- schema.py        — koçluk veri seti şeması + JSONL G/Ç (saf python, test edilebilir)
- prompt_format.py — ÜRETİM promptuyla birebir aynı mesaj formatı (saf python)
- build_dataset.py — şablon + altın örneklerden veri seti üretimi (saf python)
- prepare.py       — tokenizer chat-template + train/val ayrımı (transformers)
- train_lora.py    — QLoRA fine-tune (peft + trl + bitsandbytes)
- merge_and_export.py — adaptör birleştir → GGUF → Ollama Modelfile
- evaluate.py      — baseline (prompt-only) vs fine-tune: TR/ret/grounding metrikleri

Bağımlılık ayrımı: requirements-finetune.txt yalnızca eğitim içindir, runtime/CI'ye
dahil değildir. Saf-python modüller (schema, prompt_format, build_dataset) torch'suz
çalışır ve birim testlerde her zaman koşar.
"""
