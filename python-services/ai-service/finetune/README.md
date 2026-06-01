# Chatbot Fine-Tune — Türkçe Davranış Koçluğu LLM'i (QLoRA)

Bu paket, Badhabinot sohbet asistanını **prompt mühendisliğinden** çıkarıp
**fine-tune edilmiş, ölçülmüş bir modele** taşıyan uçtan uca iskelettir.
Vision tarafındaki `training/` + `evaluation/` desenini izler.

> **Durum (2026-06-01): fine-tune ÇALIŞTIRILDI ve deploy edildi.** Qwen2.5-1.5B-Instruct
> üzerinde QLoRA (4-bit) + **completion-only loss** ile eğitildi; merge → GGUF → Ollama
> (`badhabinot-coach:latest`) ile yüklenip üretim prompt formatıyla doğrulandı. Taban model
> (prompt-only) baseline'ına karşı dört metrikle ölçüldü (`finetune/outputs/*.json`).
> **Değerlendirme held-out (eğitimde olmayan) set üzerindedir** (`eval_heldout.jsonl`);
> in-sample `eval.jsonl` eğitimle örtüşür, yalnızca ablation/kıyas için. Sonuç tabloları:
> tez §5. Daha fazla grounding kazanımı için **gold veri büyütülmeli** (veri = tavan).

---

## Neden fine-tune? (Tez gerekçesi)

Mevcut chatbot = `qwen2.5:7b` (Ollama) + sistem promptu + sunucu-tarafı
deterministik grounding. Yani "yapay zeka" davranışı **eğitilmemiş**; kurallı bir
sarmalayıcıdır. Fine-tune bunu değiştirir:

- **Özgün katkı:** Türkçe, gizlilik-koruyan, davranış-verisine-dayalı koçluk için
  alanına özel bir modelin QLoRA ile eğitilmesi.
- **Ölçülebilirlik:** baseline (taban model) vs fine-tune → grounding sadakati,
  ret doğruluğu, Türkçe uyumu, düz-metin uyumu (bkz. `evaluate.py`).
- **Savunulabilir donanım:** parametre-verimli (LoRA) eğitim, tüketici GPU'sunda.

---

## ⚠️ Donanım / VRAM

Bu projedeki yerel GPU: **RTX 4050 Laptop = 6 GB VRAM.**

| Profil | Taban model | Yaklaşık VRAM (4-bit QLoRA) | Nerede |
|--------|-------------|------------------------------|--------|
| `local-6gb` *(varsayılan)* | Qwen2.5-**1.5B**-Instruct | ~4-5 GB | Yerel RTX 4050 ✅ |
| `local-8gb` | Qwen2.5-**3B**-Instruct | ~6-7 GB (sıkı) | Yerel (8 GB+ ideal) |
| `cloud-16gb` | Qwen2.5-**7B**-Instruct | ~10-12 GB | Colab/Kaggle/RunPod T4+ |

> **6 GB ile 7B fine-tune edilemez.** 7B istiyorsan `--profile cloud-16gb` ile
> bir bulut GPU'da çalıştır — betikler birebir aynıdır, sadece taban model değişir.
> Profili `FINETUNE_PROFILE` ortam değişkeniyle de sabitleyebilirsin.

---

## Kurulum

```bash
cd python-services/ai-service
# 1) PyTorch'u CUDA derlemesiyle:
pip install torch --index-url https://download.pytorch.org/whl/cu121
# 2) Fine-tune bağımlılıkları:
pip install -r finetune/requirements-finetune.txt
```

GGUF dışa aktarımı için (Ollama'ya yüklemek üzere) ayrıca llama.cpp:
```bash
git clone https://github.com/ggerganov/llama.cpp
```

---

## İş akışı (5 adım)

```
build_dataset → prepare → train_lora → merge_and_export → evaluate
   (veri)        (token)    (QLoRA)       (GGUF/Ollama)     (kıyas)
```

### 1. Veri seti üret/büyüt
```bash
# Başlangıç: elle yazılmış gold + 200 sentetik örnek
python -m finetune.build_dataset --out finetune/data/coaching_dataset.jsonl --synthetic 200
```
- **Sentetik örnekler formatı öğretir**, ama akademik değer GOLD örneklerdedir.
  `build_dataset.py` içindeki `_gold_examples()`'ı çoğalt; ideal yanıtların kalitesi
  = model kalitesi. Hedef: persona (GENERAL_CHAT / BEHAVIOR_COACH / CUSTOM) ve
  kind (answer / casual / refuse) dengeli birkaç yüz gerçek örnek.
- Ayrı bir held-out **değerlendirme** seti üret (kıyas için):
  ```bash
  python -m finetune.build_dataset --out finetune/data/eval.jsonl --synthetic 40 --seed 7
  ```

Veri biçimi ve doğrulama: `schema.py` (saf python). Prompt biçimi üretimle birebir:
`prompt_format.py` (— `app/services/providers.py` ile senkron tutulmalı).

### 2. Hazırla (tokenize + böl)
```bash
python -m finetune.prepare                 # local-6gb (varsayılan)
# python -m finetune.prepare --profile cloud-16gb
```

### 3. Eğit (QLoRA)
```bash
python -m finetune.train_lora              # adaptör → outputs/lora-adapter
# python -m finetune.train_lora --profile cloud-16gb --epochs 3
```

### 4. Birleştir + Ollama'ya aktar
```bash
python -m finetune.merge_and_export --llama-cpp ./llama.cpp
# → outputs/merged-fp16, outputs/badhabinot-coach.gguf, outputs/Modelfile.coach
ollama create badhabinot-coach:latest -f finetune/outputs/Modelfile.coach
```
Sonra kullanıcı **Ayarlar → LOCAL mod**'da `local_model_name = badhabinot-coach:latest`
seçince AI servis (OllamaProvider) bu fine-tune modeli kullanır. Backend tarafında
kod değişikliği gerekmez.

### 5. Değerlendir (baseline vs fine-tune)
```bash
# baseline (eğitilmemiş taban):
python -m finetune.evaluate --model Qwen/Qwen2.5-1.5B-Instruct --data finetune/data/eval.jsonl --tag baseline --out finetune/outputs/baseline.json
# fine-tune:
python -m finetune.evaluate --model finetune/outputs/merged-fp16 --data finetune/data/eval.jsonl --tag finetune --out finetune/outputs/finetune.json
# delta:
python -m finetune.evaluate --compare finetune/outputs/baseline.json finetune/outputs/finetune.json
```
Metrikler: `turkish_ratio`, `plaintext_ratio`, `grounding_score` (uydurma sayı cezası),
`refusal_accuracy`. Bu tablo doğrudan tezin "Deneysel Sonuçlar — Chatbot" bölümüne girer.

---

## Dosyalar

| Dosya | Bağımlılık | Sorumluluk |
|-------|-----------|------------|
| `config.py` | — | VRAM profili → taban model + hiperparametre |
| `schema.py` | saf python | Veri seti şeması + JSONL G/Ç + doğrulama |
| `prompt_format.py` | saf python | Üretimle birebir mesaj/özet biçimi |
| `build_dataset.py` | saf python | Gold + sentetik örnek üretimi |
| `prepare.py` | transformers, datasets | Chat-template tokenize + train/val ayrımı |
| `train_lora.py` | torch, peft, trl, bnb | QLoRA fine-tune → adaptör |
| `merge_and_export.py` | torch, peft | Adaptör birleştir → GGUF → Ollama Modelfile |
| `evaluate.py` | torch, transformers | baseline vs fine-tune metrikleri |

Saf-python modüller (schema, prompt_format, build_dataset) torch'suz çalışır ve
`tests/test_finetune_*.py` ile her zaman test edilir.

---

## Notlar / sonraki adımlar

- **Completion-only loss:** Şu an tüm diyalog üzerinde SFT yapılır. Yalnızca asistan
  yanıtına loss vermek (prompt'u maskelemek) kaliteyi artırabilir — TRL
  `DataCollatorForCompletionOnlyLM` ile eklenebilir.
- **Veri = tavan.** Model kalitesi gold veri kalitesine bağlıdır; sentetik orana güvenme.
- **KVKK:** Veri seti gerçek kullanıcı diyaloglarından türetilirse anonimleştir;
  `data/` git'e girmez (bkz. `.gitignore`).
