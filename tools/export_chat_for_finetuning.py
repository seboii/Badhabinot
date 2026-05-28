"""Sohbet geçmişini fine-tune dataset'ine çevirir (OpenAI veya Ollama formatında).

PostgreSQL'deki `chat_messages` tablosundan kullanıcı/asistan mesaj çiftlerini
okur ve seçilen formatta JSONL üretir. Tezin "kişisel sohbet verisinden
model ince ayarı" anlatısının veri tarafıdır.

İki çıktı formatı desteklenir:

* `openai`  — OpenAI fine-tune format (https://platform.openai.com/docs/guides/fine-tuning)
              Her satır: {"messages":[{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]}
* `ollama`  — Ollama Modelfile için (MESSAGE bloku) hazırlık + sade JSONL
              Her satır: {"prompt": "...", "response": "..."}

Kullanım:
    # OpenAI formatı (varsayılan), tüm kullanıcılar
    python tools/export_chat_for_finetuning.py \\
        --out training_data.jsonl

    # Belirli bir kullanıcı + Ollama formatı
    python tools/export_chat_for_finetuning.py \\
        --user-id <uuid> --format ollama --out badhabinot_finetune.jsonl

    # Sadece son N gün + en fazla M konuşma çifti
    python tools/export_chat_for_finetuning.py --days 30 --max-pairs 1000

Gereksinim: `pip install psycopg[binary]` (veya psycopg2)

DB bağlantısı .env'den okunur (POSTGRES_USER, POSTGRES_PASSWORD, vb.).
Docker'da: `docker exec badhabinot-platform-postgres-1 ...` ile çalıştırılabilir
ama bu script host'tan da DB'ye erişebilir (port 5432 açık).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _load_dotenv() -> None:
    """Basit .env okuyucu (python-dotenv olmadan)."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _connect():
    try:
        import psycopg
        connection_factory = psycopg.connect
    except ImportError:
        try:
            import psycopg2 as psycopg
            connection_factory = psycopg.connect
        except ImportError as exc:
            print(
                "HATA: psycopg veya psycopg2 yüklü değil. "
                "Çözüm: pip install psycopg[binary]",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "badhabinot")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    database = os.environ.get("POSTGRES_DB_MONITORING", "badhabinot_monitoring")
    return connection_factory(
        host=host, port=int(port), user=user, password=password, dbname=database,
    )


def fetch_pairs(
    user_id: str | None,
    days: int | None,
    max_pairs: int | None,
) -> list[dict]:
    """chat_messages'ten ardışık (user → assistant) çiftleri çıkarır."""
    where_clauses: list[str] = []
    params: list[object] = []
    if user_id:
        where_clauses.append("user_id = %s")
        params.append(user_id)
    if days is not None:
        since = datetime.now(tz=timezone.utc) - timedelta(days=days)
        where_clauses.append("created_at >= %s")
        params.append(since)
    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = (
        "SELECT conversation_id, role, content, created_at "
        "FROM chat_messages" + where_sql + " "
        "ORDER BY user_id, conversation_id, created_at ASC"
    )

    with _connect() as conn, conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    pairs: list[dict] = []
    pending_user: dict | None = None
    for conversation_id, role, content, created_at in rows:
        if not content:
            continue
        if role == "user":
            pending_user = {
                "conversation_id": str(conversation_id),
                "user_message": content,
                "user_created_at": created_at.isoformat() if created_at else None,
            }
        elif role == "assistant" and pending_user is not None:
            pending_user["assistant_message"] = content
            pending_user["assistant_created_at"] = created_at.isoformat() if created_at else None
            pairs.append(pending_user)
            pending_user = None
            if max_pairs and len(pairs) >= max_pairs:
                break
    return pairs


# ── Format dönüştürücüler ────────────────────────────────────────────────────

def to_openai(pairs: list[dict], system_prompt: str) -> list[dict]:
    return [
        {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": p["user_message"]},
                {"role": "assistant", "content": p["assistant_message"]},
            ]
        }
        for p in pairs
    ]


def to_ollama(pairs: list[dict]) -> list[dict]:
    return [
        {"prompt": p["user_message"], "response": p["assistant_message"]}
        for p in pairs
    ]


# ── Modelfile çıktısı (Ollama için bonus) ───────────────────────────────────

def write_ollama_modelfile(pairs: list[dict], base_model: str, system_prompt: str, out_path: Path) -> None:
    """Ollama 'MESSAGE' blokları ile Modelfile üretir.

    Bu Modelfile fine-tune değildir — sadece runtime'da örnek konuşma
    içeriği enjekte eder. Gerçek fine-tune için (LoRA vb.) ayrı bir araç
    gerekir; bu daha ileri bir adımdır.
    """
    lines = [
        f"FROM {base_model}",
        f'SYSTEM """{system_prompt}"""',
        "PARAMETER temperature 0.2",
        "",
    ]
    for p in pairs[:50]:   # ilk 50 örnek
        u = p["user_message"].replace('"', '\\"')
        a = p["assistant_message"].replace('"', '\\"')
        lines.extend([
            f'MESSAGE user "{u}"',
            f'MESSAGE assistant "{a}"',
        ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="chat_messages → fine-tune dataset")
    parser.add_argument("--user-id", help="Sadece belirli bir kullanıcı (UUID)")
    parser.add_argument("--days", type=int, help="Son N gün (varsayılan: hepsi)")
    parser.add_argument("--max-pairs", type=int, help="Maks konuşma çifti")
    parser.add_argument("--format", choices=["openai", "ollama"], default="openai")
    parser.add_argument(
        "--system-prompt",
        default="Sen Badhabinot davranış asistanısın. Doğal, Türkçe konuş; veriyi uydurma.",
        help="OpenAI veya Modelfile için system prompt",
    )
    parser.add_argument("--out", required=True, help="Çıktı JSONL")
    parser.add_argument(
        "--ollama-modelfile",
        help="Bonus: ek olarak Ollama Modelfile yaz (MESSAGE blokları)",
    )
    parser.add_argument(
        "--base-model",
        default="qwen2.5:7b",
        help="Modelfile için temel model",
    )
    args = parser.parse_args(argv)

    _load_dotenv()
    print("DB'ye bağlanılıyor...")
    pairs = fetch_pairs(args.user_id, args.days, args.max_pairs)
    if not pairs:
        print("Hiç konuşma çifti bulunamadı.", file=sys.stderr)
        return 1
    print(f"{len(pairs)} konuşma çifti çekildi.")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records: list[dict]
    if args.format == "openai":
        records = to_openai(pairs, args.system_prompt)
    else:
        records = to_ollama(pairs)

    with out_path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"JSONL yazıldı: {out_path}  (format: {args.format})")

    if args.ollama_modelfile:
        mf_path = Path(args.ollama_modelfile)
        mf_path.parent.mkdir(parents=True, exist_ok=True)
        write_ollama_modelfile(pairs, args.base_model, args.system_prompt, mf_path)
        print(f"Modelfile yazıldı: {mf_path}")
        print(
            f"  → Eğitmek için: ollama create badhabinot-finetuned "
            f"-f {mf_path}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
