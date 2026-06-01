"""Sohbet promptu için paylaşılan 'zengin sinyal' bloğu biçimleyicisi.

Programın chat anında topladığı ama daha önce yerel (Ollama) prompt'una girmeyen
veriyi — son davranış olayları, hatırlatıcılar, 7 günlük trend, veri boşlukları —
deterministik bir Türkçe metne çevirir.

TEK DOĞRULUK KAYNAĞI: hem üretim (`providers.py`) hem fine-tune eğitim verisi
(`finetune/prompt_format.py`) bu fonksiyonu çağırır → eğitim promptu = çıkarım
promptu (drift olmaz). Saf stdlib; girdi olarak ilkel tipler alır ki her iki
bağlam tipi (Pydantic ChatContext / dataclass MonitoringContext) de besleyebilsin.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def format_recent_signals(
    events: Sequence[tuple[str, str, float, str, int]],   # (type, severity, conf[0-1], interp, hour)
    reminders: Sequence[tuple[str, str]],                  # (reminder_type, message)
    event_type_counts: Mapping[str, int],
    total_sessions_7d: int,
    total_minutes_7d: int,
    hydration_7d_ml: int,
    analyses_7d: int,
    data_gaps: Sequence[str],
) -> str:
    """Boş olmayan bölümlerden zengin sinyal metni üretir (hepsi boşsa '')."""
    lines: list[str] = []

    if events:
        lines.append("=== SON DAVRANIŞ OLAYLARI ===")
        for event_type, severity, confidence, interpretation, hour in list(events)[:6]:
            pct = round(float(confidence) * 100)
            tail = f": {interpretation}" if interpretation else ""
            lines.append(f"- {event_type} ({severity}, %{pct}) saat {int(hour):02d}{tail}")

    if event_type_counts:
        top = sorted(event_type_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
        if top:
            lines.append("Olay dağılımı: " + ", ".join(f"{k} x{v}" for k, v in top))

    if reminders:
        lines.append("=== HATIRLATICILAR ===")
        for reminder_type, message in list(reminders)[:5]:
            tail = f": {message}" if message else ""
            lines.append(f"- {reminder_type}{tail}")

    if total_sessions_7d or total_minutes_7d or hydration_7d_ml or analyses_7d:
        lines.append("=== SON 7 GÜN ===")
        lines.append(
            f"- Oturum: {total_sessions_7d} ({total_minutes_7d} dk), "
            f"Hidrasyon: {hydration_7d_ml} ml, Analiz: {analyses_7d}"
        )

    if data_gaps:
        lines.append("=== VERİ BOŞLUKLARI ===")
        for gap in list(data_gaps)[:3]:
            lines.append(f"- {gap}")

    return "\n".join(lines)
