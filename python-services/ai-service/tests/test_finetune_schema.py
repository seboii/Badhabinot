"""finetune.schema — sohbet-mesajları (ChatExample) JSONL şeması. Saf python."""

from __future__ import annotations

import json

import pytest

from finetune.schema import (
    ChatExample,
    ChatMessage,
    dataset_stats,
    dump_jsonl,
    load_jsonl,
)


def _ex(*pairs: tuple[str, str], tags: list[str] | None = None) -> ChatExample:
    return ChatExample(messages=[ChatMessage(role=r, content=c) for r, c in pairs], tags=tags or [])


def test_valid_example_passes_validation():
    ex = _ex(("system", "Sen koçsun."), ("user", "Duruşum?"), ("assistant", "Skorun 80/100."))
    ex.validate()  # raise etmemeli


def test_user_assistant_only_is_valid():
    # system opsiyonel — yoksa Ollama Modelfile sistem promptu devreye girer.
    _ex(("user", "Su?"), ("assistant", "1500/2500 ml.")).validate()


def test_invalid_role_rejected():
    with pytest.raises(ValueError):
        _ex(("robot", "x"), ("assistant", "y")).validate()


def test_last_message_must_be_assistant():
    with pytest.raises(ValueError):
        _ex(("user", "Duruşum?")).validate()


def test_requires_at_least_one_user():
    with pytest.raises(ValueError):
        _ex(("system", "Sen koçsun."), ("assistant", "Merhaba.")).validate()


def test_system_must_be_first():
    with pytest.raises(ValueError):
        _ex(("user", "q"), ("system", "geç sistem"), ("assistant", "a")).validate()


def test_empty_content_rejected():
    with pytest.raises(ValueError):
        _ex(("user", "q"), ("assistant", "   ")).validate()


def test_prompt_messages_and_target():
    ex = _ex(("system", "S"), ("user", "U"), ("assistant", "A"))
    assert ex.target == "A"
    assert ex.prompt_messages() == [{"role": "system", "content": "S"}, {"role": "user", "content": "U"}]
    assert ex.to_messages()[-1] == {"role": "assistant", "content": "A"}


def test_jsonl_roundtrip(tmp_path):
    ex = _ex(("user", "Su?"), ("assistant", "1500/2500 ml."), tags=["gold"])
    path = tmp_path / "d.jsonl"
    assert dump_jsonl([ex], path) == 1
    loaded = load_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].messages[0].content == "Su?"
    assert loaded[0].target == "1500/2500 ml."
    assert loaded[0].tags == ["gold"]


def test_load_jsonl_reports_bad_line(tmp_path):
    path = tmp_path / "bad.jsonl"
    # son mesaj assistant değil → doğrulama hatası, satır numarasıyla.
    path.write_text(json.dumps({"messages": [{"role": "user", "content": "q"}]}) + "\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        load_jsonl(path)
    assert "bad.jsonl:1" in str(exc.value)


def test_dataset_stats():
    examples = [
        _ex(("user", "a"), ("assistant", "b")),
        _ex(("system", "s"), ("user", "c"), ("assistant", "d")),
    ]
    stats = dataset_stats(examples)
    assert stats["total"] == 2
    assert stats["by_role"] == {"user": 2, "assistant": 2, "system": 1}
