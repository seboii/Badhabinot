"""Badhabinot — Türkçe davranış koçluğu LLM'i için QLoRA fine-tune iskeleti.

Mevcut chatbot, qwen2.5:7b tabanlı Ollama modeli + sistem promptu + sunucu
tarafı deterministik grounding'den ibarettir; *eğitilmiş* bir model değildir.
Bu paket, prompt-mühendisliğinden **fine-tune edilmiş, ölçülmüş** bir modele
geçişin uçtan uca iskeletini kurar:

    (senin {messages} JSONL'in) → prepare → train_lora → merge_and_export → evaluate
                                                                                │
                                                                        Ollama (GGUF)

Yapı: sentetik veri üretimi (build_dataset) KALDIRILDI. Eğitim doğrudan senin
yüklediğin sohbet-mesajları JSONL'i ({"messages": [...]}) ile yapılır.

Tasarım:
- config.py        — donanıma göre (VRAM profili) taban model + hiperparametre
- schema.py        — sohbet-mesajları (ChatExample) veri seti + JSONL G/Ç (saf python)
- prepare.py       — tokenizer chat-template + train/val ayrımı (transformers)
- train_lora.py    — QLoRA fine-tune (peft + trl + bitsandbytes)
- merge_and_export.py — adaptör birleştir → GGUF → Ollama Modelfile
- evaluate.py      — baseline (prompt-only) vs fine-tune: TR/ret/grounding metrikleri

Bağımlılık ayrımı: requirements-finetune.txt yalnızca eğitim içindir, runtime/CI'ye
dahil değildir. Saf-python modüller (schema) torch'suz çalışır ve testlerde koşar.
"""
