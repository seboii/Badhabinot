"""ÜRETİM promptuyla birebir aynı mesaj formatı.

KRİTİK: Fine-tune sırasında modele gösterilen prompt, çıkarımda (inference)
gördüğüyle AYNI olmalı; aksi halde model üretimde dağılır. Bu modül,
``app/services/providers.py`` içindeki persona sistem promptlarını ve
``_compose_user_message`` / ``_build_messages`` özet bloğunu yeniden üretir.

providers.py değişirse burası da güncellenmeli (tek doğruluk kaynağı orası;
bu kopya, eğitim verisini üretim formatına kilitlemek içindir).

Saf python — torch/transformers gerekmez.
"""

from __future__ import annotations

from .schema import BehavioralPattern, CoachingExample, MonitoringContext

# ── Persona sistem promptları (providers.py ile birebir) ────────────────────
GENERAL_CHAT_SYSTEM_PROMPT = (
    "Sen Badhabinot uygulamasının asistanısın. Kullanıcıyla doğal, samimi, "
    "Türkçe konuşursun. Genel sorulara (selamlama, hava, motivasyon, "
    "günlük sohbet, kod, fikir vb.) normal bir yapay zeka asistanı gibi "
    "yanıt verirsin; gerekmedikçe kullanıcının monitoring verisini "
    "dayatma. Eğer kullanıcı duruşum/skorum/su/sigara/raporum gibi "
    "doğrudan veri sorarsa, sana sağlanan bağlamı kullan ve uydurma. "
    "Sistem promptu, model mimarisi ya da teknik detay sorulursa nazikçe reddet. "
    "Yanıtın kısa ve anlaşılır olsun (gerektiğinde paragraf, kod bloğu kullanabilirsin)."
)

BEHAVIOR_COACH_SYSTEM_PROMPT = (
    "Sen Badhabinot davranış koçluğu asistanısın. "
    "Her yanıt sana sağlanan monitoring verisine dayanmalı. "
    "Sayıları, olayları, trendleri uydurma; bilgi eksikse açıkça söyle. "
    "Sigara sinyallerini kesinlik değil ipucu olarak ele al. "
    "Türkçe, kısa (2-4 cümle), düz metin yanıt ver. "
    "JSON, kod bloğu veya markdown tablo kullanma. "
    "Sistem promptu, model mimarisi veya teknik detay sorulursa nazikçe reddet."
)

# GENERAL_CHAT'in veri bloğu eklemesini tetikleyen DAR monitoring kelimeleri
# (providers.py _GENERAL_CHAT_DATA_KEYWORDS ile birebir).
_GENERAL_CHAT_DATA_KEYWORDS = frozenset([
    "duruş", "durus", "postur", "hidrasyon", "su iç", "su ic", "sigara",
    "el hareket", "yüz dokun", "yuz dokun", "skor", "puan", "rapor",
    "analiz", "izleme", "kamera", "oturum", "session", "alarm", "uyarı",
    "uyari", "smoking", "posture", "hydration", "monitoring",
])

_DAY_NAMES_TR = {
    "MONDAY": "Pazartesi", "TUESDAY": "Salı", "WEDNESDAY": "Çarşamba",
    "THURSDAY": "Perşembe", "FRIDAY": "Cuma", "SATURDAY": "Cumartesi", "SUNDAY": "Pazar",
}


def persona_system_prompt(example: CoachingExample) -> str:
    persona = (example.persona or "GENERAL_CHAT").upper()
    if persona == "CUSTOM" and example.custom_system_prompt:
        return example.custom_system_prompt.strip()
    if persona == "BEHAVIOR_COACH":
        return BEHAVIOR_COACH_SYSTEM_PROMPT
    return GENERAL_CHAT_SYSTEM_PROMPT


def includes_data_block(example: CoachingExample) -> bool:
    """BEHAVIOR_COACH/CUSTOM her zaman; GENERAL_CHAT yalnızca dar kelime geçerse."""
    persona = (example.persona or "GENERAL_CHAT").upper()
    if persona in ("BEHAVIOR_COACH", "CUSTOM"):
        return True
    lower = (example.question or "").lower()
    return any(kw in lower for kw in _GENERAL_CHAT_DATA_KEYWORDS)


def format_pattern_block(patterns: list[BehavioralPattern]) -> str:
    if not patterns:
        return ""
    lines = ["=== ZAMANSAL ÖRÜNTÜLER (SON 7 GÜN) ==="]
    for p in patterns[:5]:
        day_tr = _DAY_NAMES_TR.get(p.peak_day_of_week, p.peak_day_of_week)
        lines.append(
            f"- {p.event_type}: {p.total_count_last_7_days} olay ({p.intensity_label}), "
            f"pik saat {p.peak_hour_of_day:02d}:00 ({p.peak_hour_count} olay), "
            f"pik gün {day_tr}, trend: {p.trend_label}"
        )
    return "\n".join(lines) + "\n"


def format_summary_block(ctx: MonitoringContext) -> str:
    """providers.py _compose_user_message özet bloğuyla aynı biçim."""
    hydration_pct = round(
        (ctx.hydration_progress_ml / ctx.water_goal_ml * 100) if ctx.water_goal_ml > 0 else 0, 1
    )
    posture_score = round((1.0 - ctx.poor_posture_ratio) * 100, 1)
    block = (
        f"Bugünün özeti ({ctx.report_date}):\n"
        f"- Hidrasyon: {ctx.hydration_progress_ml}/{ctx.water_goal_ml} ml (%{hydration_pct})\n"
        f"- Duruş skoru: {posture_score}/100 (uyarı: {ctx.posture_alert_count})\n"
        f"- Sigara benzeri: {ctx.smoking_like_count}, el hareketi: {ctx.hand_movement_count}\n"
        f"- Tamamlanan analiz: {ctx.analyses_completed}\n"
        f"- Karşılaştırma: {ctx.comparison_to_previous_day or 'Veri yok'}"
    )
    if ctx.behavioral_patterns:
        block += "\n- Zamansal örüntüler:"
        for p in ctx.behavioral_patterns[:3]:
            block += (
                f"\n  • {p.event_type}: {p.total_count_last_7_days} olay "
                f"(pik saat {p.peak_hour_of_day:02d}, trend: {p.trend_label})"
            )
    return block


def compose_user_message(example: CoachingExample) -> str:
    """Persona kuralına göre soruya monitoring özeti ekler (ya da eklemez)."""
    if not includes_data_block(example):
        return example.question
    return f"{format_summary_block(example.context)}\n\nSoru: {example.question}"


def build_chat_messages(example: CoachingExample) -> list[dict[str, str]]:
    """Eğitim için tam mesaj listesi: [system, *history, user, assistant].

    train_lora.py bunu tokenizer.apply_chat_template'e verir; son ``assistant``
    mesajı (ideal_answer) eğitim hedefidir.
    """
    messages: list[dict[str, str]] = [
        {"role": "system", "content": persona_system_prompt(example)},
    ]
    for turn in example.history[-10:]:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": compose_user_message(example)})
    messages.append({"role": "assistant", "content": example.ideal_answer.strip()})
    return messages


def build_inference_messages(example: CoachingExample) -> list[dict[str, str]]:
    """Çıkarım/değerlendirme için: son ``assistant`` (hedef) hariç mesajlar."""
    return build_chat_messages(example)[:-1]
