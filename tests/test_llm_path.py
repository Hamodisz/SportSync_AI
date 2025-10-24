# -*- coding: utf-8 -*-
import json
import os

import pytest

import core.backend_gpt as backend


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Ensure environment and module globals are reset between tests."""
    monkeypatch.setenv("DISABLE_LLM", "false")
    backend.LAST_RECOMMENDER_SOURCE = "unset"
    yield
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "GROQ_API_KEY", "OPENROUTER_API_KEY"):
        os.environ.pop(key, None)
    backend.LAST_RECOMMENDER_SOURCE = "unset"


def _mock_cards_payload():
    cards = []
    for idx in range(3):
        cards.append({
            "title": f"عنوان {idx}",
            "silent": " ".join(["هدوء"] * 45),
            "what": " ".join(["حكاية"] * 45),
            "why": " ".join(["سبب"] * 45),
            "real": " ".join(["واقعي"] * 45),
            "start": " ".join(["بداية"] * 40),
            "notes": " ".join(["إلهام"] * 40),
        })
    return json.dumps({"cards": cards}, ensure_ascii=False)


def test_llm_then_fallback(monkeypatch):
    captured_sources = []

    def fake_log_event(user_id, session_id, name, payload=None, lang="ar"):
        captured_sources.append((name, (payload or {}).get("source")))

    monkeypatch.setattr(backend, "log_event", fake_log_event, raising=False)

    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

    def fake_get_client_and_models():
        class DummyClient:
            pass
        return DummyClient(), "model-main", "model-fallback"

    monkeypatch.setattr(backend, "get_client_and_models", fake_get_client_and_models)
    monkeypatch.setattr(backend, "chat_once", lambda *args, **kwargs: _mock_cards_payload())

    answers = {"q1": {"answer": ["أبحث عن ذكاء تكتيكي"]}, "_session_id": "sess-1"}
    cards = backend.generate_sport_recommendation(answers, "العربية")

    assert len(cards) == 3
    assert backend.get_last_rec_source() == "llm"
    assert captured_sources[-1][1] == "llm"
    assert all(card.startswith("🎯") for card in cards)

    captured_sources.clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(backend, "get_client_and_models", lambda: (None, "", ""))

    cards_fb = backend.generate_sport_recommendation({"q1": {"answer": ["أبحث عن تجربة هادئة"]}, "_session_id": "sess-2"}, "العربية")

    assert len(cards_fb) == 3
    assert backend.get_last_rec_source() == "fallback"
    assert captured_sources[-1][1] == "fallback"
    assert all(card.startswith("🎯") for card in cards_fb)
