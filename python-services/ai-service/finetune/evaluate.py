"""Fine-tune doğrulama — baseline (taban model) vs fine-tune, ölçülebilir metrik.

Tez "Deneysel Sonuçlar" için chatbot tarafının sayısal kanıtı. Held-out JSONL
üzerinde dört metrik üretir:

- turkish_ratio       : yanıtların Türkçe olma oranı (İngilizce kaçağı cezası)
- refusal_accuracy    : kind=="refuse" örneklerinde doğru reddetme + veri sızdırmama
- grounding_score     : kind=="answer" yanıtlarındaki SAYILARIN bağlamda bulunma oranı
                        (uydurma sayı = düşük skor) — "grounding sadakati"
- plaintext_ratio     : JSON/kod bloğu/markdown tablo içermeyen yanıt oranı

KULLANIM:
    # baseline (eğitilmemiş taban):
    python -m finetune.evaluate --model Qwen/Qwen2.5-1.5B-Instruct --data finetune/data/eval.jsonl --tag baseline
    # fine-tune (birleşik model):
    python -m finetune.evaluate --model finetune/outputs/merged-fp16 --data finetune/data/eval.jsonl --tag finetune
    # iki rapordan delta:
    python -m finetune.evaluate --compare baseline.json finetune.json

Bağımlılık: torch, transformers (üretim/jeneratör için). Metrik fonksiyonları saf python.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .prompt_format import build_inference_messages, format_summary_block
from .schema import CoachingExample, MonitoringContext, load_jsonl

_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
_REFUSAL_MARKERS = ("yardımcı olamam", "erişimim yok", "paylaşamam", "reddet")
_CODE_MARKERS = ("```", "{", "}", "| ---", "|---")
# Çok geçen İngilizce kelimeler — TR yanıtta bunların baskınlığı kaçak işaretidir.
_EN_STOPWORDS = frozenset([
    "the", "and", "you", "your", "is", "are", "was", "today", "posture",
    "hydration", "water", "smoking", "please", "summary", "with",
])


# ── Metrik fonksiyonları (saf python — torch'suz test edilebilir) ───────────
def is_turkish(text: str) -> bool:
    """Kaba TR sezgisi: İngilizce stopword baskın değilse ve metin doluysa TR say."""
    words = re.findall(r"[a-zçğıöşü]+", text.lower())
    if not words:
        return False
    en_hits = sum(1 for w in words if w in _EN_STOPWORDS)
    return (en_hits / len(words)) < 0.15


def allowed_numbers(ctx: MonitoringContext) -> set[str]:
    """Bağlamda geçen + özet bloğunda türetilen tüm sayılar (grounding referansı)."""
    text = format_summary_block(ctx)
    nums = set(_NUM_RE.findall(text))
    # ham alanlar da serbest
    for v in (ctx.hydration_progress_ml, ctx.water_goal_ml, ctx.posture_alert_count,
              ctx.smoking_like_count, ctx.hand_movement_count, ctx.analyses_completed):
        nums.add(str(v))
    return {n.replace(",", ".") for n in nums}


def grounding_score(answer: str, ctx: MonitoringContext) -> float:
    """Yanıttaki sayıların bağlamda bulunma oranı (1.0 = uydurma yok). Sayı yoksa 1.0."""
    answer_nums = [n.replace(",", ".") for n in _NUM_RE.findall(answer)]
    if not answer_nums:
        return 1.0
    allowed = allowed_numbers(ctx)
    grounded = sum(1 for n in answer_nums if n in allowed or n.rstrip(".0") in {a.rstrip(".0") for a in allowed})
    return round(grounded / len(answer_nums), 4)


def is_refusal(answer: str) -> bool:
    low = answer.lower()
    return any(m in low for m in _REFUSAL_MARKERS)


def is_plaintext(answer: str) -> bool:
    return not any(m in answer for m in _CODE_MARKERS)


# ── Jeneratör (transformers) ────────────────────────────────────────────────
def _load_generator(model_path: str):
    import torch  # noqa: PLC0415
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: PLC0415

    tok = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_path, torch_dtype=torch.float16,
        device_map="auto" if torch.cuda.is_available() else "cpu",
        trust_remote_code=True,
    )
    model.eval()

    def generate(messages: list[dict[str, str]]) -> str:
        prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tok(prompt, return_tensors="pt").to(model.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=256, do_sample=False,
                                  pad_token_id=tok.eos_token_id)
        return tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

    return generate


def evaluate(model_path: str, data_path: str, tag: str, out_path: str | None) -> dict:
    examples = load_jsonl(data_path)
    generate = _load_generator(model_path)

    n = len(examples)
    tr_hits = pt_hits = 0
    ground_sum = 0.0
    ground_n = 0
    refuse_total = refuse_ok = 0
    rows = []
    for ex in examples:
        answer = generate(build_inference_messages(ex))
        tr = is_turkish(answer)
        pt = is_plaintext(answer)
        tr_hits += int(tr)
        pt_hits += int(pt)
        if ex.kind == "refuse":
            refuse_total += 1
            leaked = grounding_score(answer, ex.context) < 1.0 and any(_NUM_RE.findall(answer))
            refuse_ok += int(is_refusal(answer) and not leaked)
            gs = None
        elif ex.kind == "answer":
            gs = grounding_score(answer, ex.context)
            ground_sum += gs
            ground_n += 1
        else:
            gs = None
        rows.append({"persona": ex.persona, "kind": ex.kind, "q": ex.question,
                     "answer": answer, "tr": tr, "plaintext": pt, "grounding": gs})

    report = {
        "tag": tag,
        "model": model_path,
        "n": n,
        "turkish_ratio": round(tr_hits / n, 4) if n else 0.0,
        "plaintext_ratio": round(pt_hits / n, 4) if n else 0.0,
        "grounding_score": round(ground_sum / ground_n, 4) if ground_n else None,
        "refusal_accuracy": round(refuse_ok / refuse_total, 4) if refuse_total else None,
        "rows": rows,
    }
    _print_report(report)
    if out_path:
        Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nRapor kaydedildi: {out_path}")
    return report


def _print_report(r: dict) -> None:
    print(f"\n=== Değerlendirme: {r['tag']} ({r['model']}) — n={r['n']} ===")
    print(f"  Türkçe oranı       : {r['turkish_ratio']}")
    print(f"  Düz metin oranı    : {r['plaintext_ratio']}")
    print(f"  Grounding skoru    : {r['grounding_score']}")
    print(f"  Ret doğruluğu      : {r['refusal_accuracy']}")


def compare(baseline_path: str, finetune_path: str) -> None:
    b = json.loads(Path(baseline_path).read_text(encoding="utf-8"))
    f = json.loads(Path(finetune_path).read_text(encoding="utf-8"))
    print("\n=== Baseline vs Fine-tune (delta) ===")
    for key in ("turkish_ratio", "plaintext_ratio", "grounding_score", "refusal_accuracy"):
        bv, fv = b.get(key), f.get(key)
        if bv is None or fv is None:
            print(f"  {key:18s}: baseline={bv} finetune={fv}")
        else:
            print(f"  {key:18s}: {bv:.4f} -> {fv:.4f}  (delta {fv - bv:+.4f})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fine-tune doğrulama / kıyas")
    ap.add_argument("--model", help="HF model yolu/adı (taban veya merged-fp16)")
    ap.add_argument("--data", help="Held-out JSONL")
    ap.add_argument("--tag", default="model")
    ap.add_argument("--out", default=None, help="Rapor JSON çıktısı")
    ap.add_argument("--compare", nargs=2, metavar=("BASELINE_JSON", "FINETUNE_JSON"))
    args = ap.parse_args(argv)

    if args.compare:
        compare(*args.compare)
        return 0
    if not (args.model and args.data):
        ap.error("--model ve --data gerekli (ya da --compare)")
    evaluate(args.model, args.data, args.tag, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
