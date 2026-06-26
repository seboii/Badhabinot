"""Fine-tune veri seti şeması — kullanıcı-yüklemeli sohbet (chat-messages) JSONL.

Yapı değişti: artık sentetik üretim (build_dataset) YOK. Eğitim doğrudan
**senin yüklediğin** veriyle yapılır. Her JSONL satırı bir sohbet örneğidir:

    {"messages": [
        {"role": "system",    "content": "Sen Badhabinot davranış koçusun..."},
        {"role": "user",      "content": "Bugün duruşum nasıldı?"},
        {"role": "assistant", "content": "Duruş skorun 80/100, 2 uyarı aldın..."}
    ]}

Kurallar (``validate``):
- En az bir ``user`` ve son mesaj ``assistant`` olmalı (eğitim hedefi son yanıttır).
- Roller: ``system`` | ``user`` | ``assistant``. İçerikler boş olamaz.
- ``system`` opsiyoneldir; verilirse ilk mesaj olmalı. (Yoksa Ollama Modelfile'daki
  koç sistem promptu devreye girer — üretimle aynı.)

Saf python (stdlib) — torch/transformers gerektirmez; birim testlerde her zaman koşar.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROLES = ("system", "user", "assistant")


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatExample:
    """Tek bir SFT örneği = bir sohbet (son mesaj = eğitim hedefi)."""

    messages: list[ChatMessage] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def validate(self) -> None:
        if not self.messages:
            raise ValueError("messages boş olamaz")
        for i, m in enumerate(self.messages):
            if m.role not in ROLES:
                raise ValueError(f"geçersiz role: {m.role} (geçerli: {ROLES})")
            if not (m.content or "").strip():
                raise ValueError("mesaj içeriği boş olamaz")
            if m.role == "system" and i != 0:
                raise ValueError("system mesajı yalnızca ilk sırada olabilir")
        if not any(m.role == "user" for m in self.messages):
            raise ValueError("en az bir 'user' mesajı gerekli")
        if self.messages[-1].role != "assistant":
            raise ValueError("son mesaj 'assistant' (eğitim hedefi) olmalı")

    def to_messages(self) -> list[dict[str, str]]:
        """Tam diyalog (asistan hedefi dahil) — apply_chat_template girdisi."""
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def prompt_messages(self) -> list[dict[str, str]]:
        """Çıkarım girdisi: son asistan hedefi HARİÇ mesajlar."""
        return [{"role": m.role, "content": m.content} for m in self.messages[:-1]]

    @property
    def target(self) -> str:
        """Son asistan yanıtı (eğitim/değerlendirme hedefi)."""
        return self.messages[-1].content

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ChatExample":
        raw = d.get("messages", [])
        if not isinstance(raw, list):
            raise ValueError("'messages' bir liste olmalı")
        messages = [ChatMessage(role=str(m["role"]), content=str(m["content"])) for m in raw]
        return cls(messages=messages, tags=list(d.get("tags", [])))


# ── JSONL G/Ç ───────────────────────────────────────────────────────────────
def load_jsonl(path: str | Path) -> list[ChatExample]:
    """JSONL dosyasını yükler ve her örneği doğrular (satır numarasıyla hata verir)."""
    out: list[ChatExample] = []
    p = Path(path)
    with p.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                ex = ChatExample.from_dict(json.loads(line))
                ex.validate()
            except Exception as exc:  # noqa: BLE001 — satır numarasıyla zenginleştir
                raise ValueError(f"{p}:{i} geçersiz örnek — {exc}") from exc
            out.append(ex)
    return out


def dump_jsonl(examples: list[ChatExample], path: str | Path) -> int:
    """Örnekleri JSONL olarak yazar; yazılan satır sayısını döner."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as fh:
        for ex in examples:
            ex.validate()
            fh.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")
    return len(examples)


def dataset_stats(examples: list[ChatExample]) -> dict[str, object]:
    """Veri seti özeti (tez tablosu için): toplam, ortalama tur, rol dağılımı."""
    by_role: dict[str, int] = {}
    turns = 0
    for ex in examples:
        turns += len(ex.messages)
        for m in ex.messages:
            by_role[m.role] = by_role.get(m.role, 0) + 1
    return {
        "total": len(examples),
        "avg_turns": round(turns / len(examples), 2) if examples else 0.0,
        "by_role": by_role,
    }
