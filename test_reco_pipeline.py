# -*- coding: utf-8 -*-
import os
import re

import pytest

import core.backend_gpt as backend


def _structured_card(idx: int) -> dict:
    label = f"مدار التخيل {idx}"
    what_lines = [
        "رحلة تحليلية تغرس بداخلك فضولاً متدفقًا يبقيك يقظًا لكل إشارة تمس قلب المشهد.",
        "تسافر بين طبقات شعورية متعددة وتعيد ترتيب الخطط بصبر يشبه تدوين رواية تكتيكية طويلة.",
        "تمنحك الفرصة لتصوغ خطواتك بهدوء بينما تربط الخيال بالحركة دون ضجيج.",
    ]
    why_lines = [
        "تحب الابتكار الذي يزدهر في الصمت الواثق.",
        "تبحث عن تجارب تقيس ذكاءك قبل سرعتك.",
        "تستمتع عندما تتحول الملاحظات الخفية إلى قرارات جريئة.",
    ]
    real_lines = [
        "تعدّل الإيقاع فور ملاحظة تلميح صغير في سلوكك الداخلي.",
        "ترسم سيناريوهات بديلة في ذهنك وتختبرها بحركات محسوبة.",
        "تعطي نفسك فسحة قصيرة لتستوعب المعلومة ثم تعود بخطة مطوّرة.",
    ]
    notes_lines = [
        "سجل لحظات الإلهام في مفكرة ذهنية مختصرة.",
        "اربط كل فكرة بإشارة حسية تدلك عليها لاحقًا.",
        "ذكّر نفسك بأن المفاجأة تولد من مراقبة التفاصيل الصغيرة.",
    ]
    return {
        'sport_label': label,
        'what_it_looks_like': what_lines,
        'why_you': why_lines,
        'real_world': real_lines,
        'notes': notes_lines,
        'signature': f'struct::{idx}',
        'signature_terms': [label.lower()],
    }


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
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


def test_llm_path_flag(monkeypatch, capsys):
    backend.LLM_CLIENT = object()
    backend.CHAT_MODEL = 'model-alpha'
    backend.CHAT_MODEL_FALLBACK = 'model-beta'
    monkeypatch.setattr(backend, '_llm_cards', lambda *args, **kwargs: [_structured_card(i) for i in range(3)])

    cards = backend.generate_sport_recommendation({'q1': {'answer': ['أحب التخطيط']}, '_session_id': 'api-on'}, 'العربية')
    out = capsys.readouterr().out
    assert '[REC] llm_path=ON model=model-alpha fb=model-beta' in out
    assert backend.get_last_rec_source() == 'llm'
    assert len(cards) == 3
    assert all(card.startswith('🎯') for card in cards)


def test_strict_layout_ar():
    backend.LLM_CLIENT = None
    backend.CHAT_MODEL = ''
    cards = backend.generate_sport_recommendation({'q1': {'answer': ['أحب الألغاز الهادئة']}, '_session_id': 'layout-ar'}, 'العربية')
    required = [
        '🎯 الرياضة المثالية لك:',
        '💡 ما هي؟',
        '🎮 ليه تناسبك؟',
        '🔍 شكلها الواقعي:',
        '⸻',
        '👁️‍🗨️ ملاحظات مهمة:',
    ]
    sample = cards[0]
    for token in required:
        assert token in sample


def test_no_time_cost_location():
    backend.LLM_CLIENT = None
    backend.CHAT_MODEL = ''
    answers = {'q1': {'answer': ['أبحث عن تجربة تكتيكية هادئة']}, '_session_id': 'no-time'}
    cards = backend.generate_sport_recommendation(answers, 'العربية')
    forbidden = re.compile(r'(دقيقة|ساعة|week|cost|price|equipment|gear|مكان|موقع|معدات)', re.IGNORECASE)
    for card in cards:
        assert not forbidden.search(card)


def test_diversity_signatures():
    answers = {'q1': {'answer': ['أحب التأمل والألغاز']}, '_session_id': 'diversity'}
    structs = backend._generate_cards(answers, 'العربية')
    assert len(structs) == 3
    for i in range(3):
        for j in range(i + 1, 3):
            text_i = backend._card_signature_text(structs[i])
            text_j = backend._card_signature_text(structs[j])
            assert backend._jaccard(text_i, text_j) <= 0.6
