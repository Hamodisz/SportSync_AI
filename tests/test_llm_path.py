# -*- coding: utf-8 -*-
import os

import pytest

import core.backend_gpt as backend


def _make_structured_card(idx: int) -> dict:
    base_label = f"طيف التحليل {idx}"
    what_lines = [
        "تجربة تحليلية عميقة تمتد على مشاعر متعددة وتعيد تشكيل القصص في ذهنك حتى تشعر أن كل تفصيل ينطق بهدوء.",
        "تقرأ الإشارات الصغيرة وتحوّلها إلى مسارات دقيقة تعكس هدوءك الداخلي مع لمسة من التخطيط الذكي.",
        "كل انتقال يمنحك فرصة لابتكار حيلة جديدة تعلمك كيف تقود المشهد دون أن ترفع صوتك.",
    ]
    why_lines = [
        "تحب أن تمنح الخيال فرصة للهندسة قبل الحركة.",
        "تبحث عن دهشة تعتمد على الإشارات الخفية.",
        "تستمتع عندما يتنفس التخطيط في صمت واضح.",
    ]
    real_lines = [
        "تختبر زوايا الإيقاع وتبدلها بمجرد أن تلمح مسارًا مختلفًا.",
        "تشارك نفسك ملاحظات ذهنية تذكرك بأن التوازن قرار.",
        "تعيد توزيع الطاقة برفق كي تحافظ على الدقة والمرح معًا.",
    ]
    notes_lines = [
        "احتفظ بسجل قصير للحظات التي انفتح فيها المشهد.",
        "اقرن كل فكرة بإشارة حسية صغيرة تذكرك بها.",
        "ذكّر نفسك أن التغيير هو مصدر الدهشة الدائم.",
    ]
    return {
        'sport_label': base_label,
        'what_it_looks_like': what_lines,
        'why_you': why_lines,
        'real_world': real_lines,
        'notes': notes_lines,
        'signature': f'llm::{idx}',
        'signature_terms': [base_label.lower()],
    }


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    monkeypatch.setenv('DISABLE_LLM', 'false')
    original_client = backend.LLM_CLIENT
    original_model = backend.CHAT_MODEL
    original_fb = backend.CHAT_MODEL_FALLBACK
    backend.LAST_RECOMMENDER_SOURCE = 'unset'
    monkeypatch.setattr(backend, 'log_recommendation_result', lambda *args, **kwargs: None, raising=False)
    yield
    backend.LLM_CLIENT = original_client
    backend.CHAT_MODEL = original_model
    backend.CHAT_MODEL_FALLBACK = original_fb
    backend.LAST_RECOMMENDER_SOURCE = 'unset'
    for key in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'GROQ_API_KEY', 'OPENROUTER_API_KEY'):
        os.environ.pop(key, None)


def test_llm_then_fallback(monkeypatch, capsys):
    captured_sources = []

    def fake_log_event(user_id, session_id, name, payload=None, lang='ar'):
        captured_sources.append((name, (payload or {}).get('source')))

    monkeypatch.setattr(backend, 'log_event', fake_log_event, raising=False)

    backend.LLM_CLIENT = object()
    backend.CHAT_MODEL = 'model-main'
    backend.CHAT_MODEL_FALLBACK = 'model-fallback'

    monkeypatch.setattr(backend, '_llm_cards', lambda *args, **kwargs: [_make_structured_card(i) for i in range(3)])

    answers = {'q1': {'answer': ['أبحث عن ذكاء تكتيكي']}, '_session_id': 'sess-1'}
    cards = backend.generate_sport_recommendation(answers, 'العربية')

    out = capsys.readouterr().out
    assert '[REC] llm_path=ON model=model-main fb=model-fallback' in out
    assert len(cards) == 3
    assert backend.get_last_rec_source() == 'llm'
    assert captured_sources[-1][1] == 'llm'
    assert all(card.startswith('🎯') and '⸻' in card for card in cards)

    captured_sources.clear()
    backend.LLM_CLIENT = None
    backend.CHAT_MODEL = ''

    cards_fb = backend.generate_sport_recommendation({'q1': {'answer': ['أبحث عن تجربة هادئة']}, '_session_id': 'sess-2'}, 'العربية')

    out_fb = capsys.readouterr().out
    assert '[REC] llm_path=OFF (KB/Hybrid only)' in out_fb
    assert len(cards_fb) == 3
    assert backend.get_last_rec_source() == 'fallback'
    assert captured_sources[-1][1] == 'fallback'
    assert all(card.startswith('🎯') and '⸻' in card for card in cards_fb)
