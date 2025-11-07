# -- coding: utf-8 --
"""Rich analytical fallback recommendations for SportSync."""
from __future__ import annotations

if __name__ == '__main__':  # allow running as script
    import sys
    from pathlib import Path as _Path
    sys.path.append(str(_Path(__file__).resolve().parent.parent))

import hashlib
import json
import os
import random
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence, Optional, Tuple

try:  # Optional LLM client; fallback works without it.
    from core.llm_client import make_llm_client, pick_models, chat_once  # type: ignore
    from core.dual_model_client import (  # type: ignore
        analyze_user_with_reasoning,
        generate_recommendations_with_intelligence
    )
    DUAL_MODEL_ENABLED = True
except Exception:  # pragma: no cover - LLM unavailable
    make_llm_client = None
    pick_models = None
    chat_once = None
    analyze_user_with_reasoning = None
    generate_recommendations_with_intelligence = None
    DUAL_MODEL_ENABLED = False
from core.user_logger import log_event, log_recommendation_result


LLM_CLIENT: Optional[Any]
CHAT_MODEL: str
CHAT_MODEL_FALLBACK: str

if make_llm_client is not None:
    try:
        LLM_CLIENT = make_llm_client()
    except Exception:
        LLM_CLIENT = None
else:
    LLM_CLIENT = None

if pick_models is not None:
    try:
        CHAT_MODEL, CHAT_MODEL_FALLBACK = pick_models()
    except Exception:
        CHAT_MODEL, CHAT_MODEL_FALLBACK = ("", "")
else:
    CHAT_MODEL = ""
    CHAT_MODEL_FALLBACK = ""

BANNED_TERMS = ["خسارة الوزن", "حرق الدهون", "سعرات", "وزن", "خطة أسبوعية", "دقيقة", "دقائق", "ساعة", "ساعات"]

ARACHETYPE_DATA: Dict[str, Dict[str, Any]] = {}
LAST_RECOMMENDER_SOURCE = "unset"


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[\w\u0600-\u06FF]+", text.lower())


def _jaccard(a: str, b: str) -> float:
    set_a = set(_tokenize(a))
    set_b = set(_tokenize(b))
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _stable_json(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, sort_keys=True)
    except Exception:
        return str(data)


def _session_id_from_answers(answers: Dict[str, Any]) -> str:
    for key in ("_session_id", "session_id", "sessionId"):
        if key in answers and answers[key]:
            return str(answers[key])
    return "anon"


def _extract_identity(answers: Dict[str, Any]) -> Dict[str, float]:
    text = (str(answers) or "").lower()
    def flag(keys: Sequence[str]) -> float:
        return 0.6 if any(k in text for k in keys) else 0.45

    identity = {
        "tactical": flag(["تكتي", "تحليل", "استراتيجية", "strategy", "smart"]),
        "sensory": flag(["هدوء", "تنفس", "سكون", "حس", "calm", "breath"]),
        "adventure": flag(["مغام", "استكشاف", "explore", "طبيعة"]),
        "achievement": flag(["تحد", "إنجاز", "تفوق", "win"]),
        "social": flag(["فريق", "جماعي", "مجموعة", "team", "friends"]),
        "solo": flag(["فردي", "لوحد", "solo", "انعزال"]),
        "indoor": flag(["داخل", "indoor", "استوديو", "صالة"]),
        "outdoor": flag(["هواء", "outdoor", "حديقة", "سماء"]),
    }
    return identity


def _drivers(identity: Dict[str, float], lang: str) -> List[str]:
    ar = lang in ("العربية", "ar")
    lines: List[str] = []
    if identity["tactical"] >= 0.58:
        lines.append("تحب قراءة المشهد قبل الحركة وتحتفظ بخطط سرية في ذهنك." if ar else "You read the scene before moving and keep quiet strategies in mind.")
    if identity["sensory"] >= 0.58:
        lines.append("تهدأ عندما تراقب أنفاسك وتلتقط الإشارات الصامتة من المكان." if ar else "You settle when you listen to your breath and catch the room’s silent cues.")
    if identity["adventure"] >= 0.58:
        lines.append("تنجذب للمسارات الجديدة وتعتبر كل زاوية فرصة لقصّة اكتشاف." if ar else "You are pulled toward new routes and treat each corner as an exploration story.")
    if identity["achievement"] >= 0.58:
        lines.append("يبهرك الشعور بإنجاز يحمل توقيعك الشخصي دون الحاجة للضجيج." if ar else "You cherish wins that carry your signature without noise.")
    if identity["social"] >= 0.58:
        lines.append("تتلون طاقتك مع الفريق وتستمتع حين تتحول الجلسة إلى حوار حركي." if ar else "Your energy blooms with a team when every drill becomes a kinetic dialogue.")
    if identity["solo"] >= 0.58:
        lines.append("تزدهر في اللحظات الهادئة التي تسمع فيها صوتك الداخلي بوضوح." if ar else "You flourish in calm moments where your inner voice is the guide.")
    if identity["indoor"] >= 0.58:
        lines.append("تميل إلى البيئات المضبوطة التي يمكنك إعادة تشكيلها حسب مزاجك." if ar else "You lean toward controlled environments you can reshape to fit your mood.")
    if identity["outdoor"] >= 0.58:
        lines.append("يعجبك الهواء المفتوح لأنه يحرر الخيال وينعش خطواتك." if ar else "Open air frees your imagination and refreshes your stride.")
    if not lines:
        lines.append("تحب التعرف على نفسك عبر تجربة حركية تنبض بالدهشة." if ar else "You enjoy discovering yourself through surprising motion.")
    return lines


def _drivers_sentence(drivers: List[str], lang: str) -> str:
    if not drivers:
        return ""
    if lang in ("العربية", "ar"):
        if len(drivers) == 1:
            return drivers[0]
        return "؛ ".join(drivers[:-1]) + "؛ " + drivers[-1]
    if len(drivers) == 1:
        return drivers[0]
    if len(drivers) == 2:
        return f"{drivers[0]} and {drivers[1]}"
    return ", ".join(drivers[:-1]) + ", and " + drivers[-1]


CARD_SECTION_LIMIT = 3

FORBIDDEN_REGEX_PATTERNS = [
    r"\b\d+\s*(?:دقيقة|دقائق|ساعة|ساعات|minute|minutes|hour|hours|week|weeks|day|days)\b",
    r"\b(?:تكلفة|سعر|budget|cost|price)\b",
    r"\b(?:موقع|مكان|venue|stadium|field|court|club|arena|gym|studio)\b",
    r"\b(?:معدات|أجهزة|gear|equipment|ball|weights|dumbbell)\b",
]

FORBIDDEN_TERMS_AR = [
    "أجرة", "رسوم", "مصروف", "موعد", "جدول", "موقع", "مكان", "ملعب", "صالة", "استوديو", "معدات",
]

FORBIDDEN_TERMS_EN = [
    "cost", "fee", "price", "schedule", "location", "venue", "equipment", "gear", "ball", "court",
]

TRAIT_KEYWORDS = {
    "solo": ["solo", "منفرد", "فردي", "وحيد", "انعزال", "independent", "self"],
    "team": ["team", "جماعي", "مجموعة", "شركاء", "ثنائي", "co-op", "cooperative", "collaborative"],
    "calm": ["calm", "هدوء", "تنفس", "steady", "مستقر", "سكون", "مطمئن", "تناغم"],
    "adrenaline": ["adrenaline", "إثارة", "اندفاع", "حماس", "سريع", "انفجار", "thrill", "حماسية"],
    "precision": ["دقة", "محسوبة", "تصويب", "precision", "measured", "calibrated", "محكمة"],
    "puzzles": ["لغز", "ألغاز", "puzzle", "تحليل", "متاهة", "معادلة", "brain", "ذكاء"],
    "stealth": ["تخفي", "خفي", "ظل", "stealth", "silent", "صامت", "خفيف", "invisible"],
    "vr": ["vr", "واقع افتراضي", "virtual", "immersive", "محاكاة", "simulated", "هولوغرام", "واقع رقمي"],
}


def _flatten_answers(answers: Dict[str, Any]) -> List[str]:
    collected: List[str] = []

    def _walk(value: Any) -> None:
        if isinstance(value, dict):
            for item in value.values():
                _walk(item)
        elif isinstance(value, list):
            for item in value:
                _walk(item)
        elif value is not None:
            collected.append(str(value))

    _walk(answers)
    return collected


def _derive_binary_traits(answers: Dict[str, Any]) -> Dict[str, float]:
    base_score = 0.42
    text = " ".join(_flatten_answers(answers)).lower()
    traits = {name: base_score for name in TRAIT_KEYWORDS.keys()}
    for trait, tokens in TRAIT_KEYWORDS.items():
        hits = sum(1 for token in tokens if token in text)
        if hits >= 2:
            traits[trait] = 0.92
        elif hits == 1:
            traits[trait] = 0.78
    if traits["vr"] < 0.7 and "محاكاة" in text:
        traits["vr"] = 0.78
    if traits["puzzles"] < 0.7 and ("تحليل" in text or "strategy" in text):
        traits["puzzles"] = 0.74
    if traits["calm"] < 0.7 and ("breath" in text or "تنفس" in text):
        traits["calm"] = 0.76
    if traits["adrenaline"] < 0.7 and ("سرعة" in text or "fast" in text):
        traits["adrenaline"] = 0.7
    if traits["solo"] > 0.7 and traits["team"] > 0.7:
        traits["solo"] = traits["team"] = 0.62
    return traits


def _scrub_forbidden(text: str, lang: str) -> str:
    if not text:
        return ""
    cleaned = text
    for pattern in FORBIDDEN_REGEX_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    for term in BANNED_TERMS:
        if term in cleaned:
            cleaned = cleaned.replace(term, "هوية ممتعة")
    if lang in ("العربية", "ar"):
        for term in FORBIDDEN_TERMS_AR:
            cleaned = cleaned.replace(term, "")
    else:
        for term in FORBIDDEN_TERMS_EN:
            cleaned = re.sub(term, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def _mask_names(text: str) -> str:
    if not text:
        return ""

    def _mask(match: re.Match[str]) -> str:
        return "the persona"

    masked = re.sub(r"\b(?:[A-Z][a-z]{2,}\s+){1,2}[A-Z][a-z]{2,}\b", _mask, text)
    return masked


def _normalize_sentences(value: Any) -> List[str]:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
    else:
        raw = str(value).replace("•", "\n").replace("-", "\n")
        parts = [seg.strip() for seg in re.split(r"[\n\.!؟]+", raw) if seg.strip()]
    return parts


def _to_bullets(value: Any, lang: str, *, minimum: int = 2, maximum: int = CARD_SECTION_LIMIT) -> str:
    parts = _normalize_sentences(value)
    cleaned: List[str] = []
    for part in parts:
        sanitized = _mask_names(_scrub_forbidden(part, lang))
        if sanitized and sanitized not in cleaned:
            cleaned.append(sanitized)
        if len(cleaned) == maximum:
            break
    if not cleaned:
        return ""
    if len(cleaned) < minimum and parts:
        idx = 0
        while len(cleaned) < minimum and idx < len(parts):
            candidate = _mask_names(_scrub_forbidden(parts[idx], lang))
            if candidate and candidate not in cleaned:
                cleaned.append(candidate)
            idx += 1
    if len(cleaned) == 1:
        cleaned = cleaned * minimum
    return "\n".join(f"- {item}" for item in cleaned[:maximum])


def _fallback_blueprints() -> List[Dict[str, Any]]:
    return [
        {
            "id": "shadow_maze",
            "trait_weights": {"stealth": 0.6, "puzzles": 0.4, "precision": 0.2},
            "identity_weights": {"tactical": 0.35, "sensory": 0.2},
            "signature_terms": ["shadow", "maze", "logic"],
            "labels": {
                "ar": [
                    "ممر التخفي الذكي",
                    "مختبر الشيفرة الصامتة",
                    "طيف الظلال التحليلية",
                ],
                "en": [
                    "Shadow Cipher Lab",
                    "Silent Tactic Corridor",
                    "Veiled Logic Circuit",
                ],
            },
            "what": {
                "ar": [
                    [
                        "رحلة تدريبية تبني حكاية من الضوء والهمس حتى تشعر أن كل إشارة تومض كأنها سطر من رواية سرية.",
                        "تتبع خطوطًا متعرجة وتعيد ترتيب زخمك ببطء كي تثبت أن التخطيط يمكن أن يتنفس من دون رفع الصوت.",
                        "كل انتقال يطلب منك قراءة الرسالة قبل أن تتحرك قدماك، فتكتب مشهدًا تكتيكيًا بلمسات محسوبة.",
                    ],
                    [
                        "مختبر ذهني يعلّمك كيف تجمع بين التحليل والحركة عبر مشاهد تتغير كلما التقطت همسة جديدة.",
                        "تترك الخيال يرسم مسارات خفيفة ثم تختبرها بجسدك لتصنع جسرًا بين الحدس والعقل.",
                        "النتيجة تجربة تضعك في دور الراوي الذي يوزع الإشارات دون أن يكشف اليد الأولى.",
                    ],
                ],
                "en": [
                    [
                        "A training tale built from glimmers and whispering cues where every spark feels like a hidden line of code.",
                        "You trace serpentine paths and adjust your tempo gently to prove strategy can breathe without any noise.",
                        "Each transition asks you to read the message before you move, letting you author a tactical scene through measured touches.",
                    ],
                    [
                        "An imagined lab that fuses analysis with motion as the scene reshapes whenever you notice a subtle hint.",
                        "You allow imagination to sketch soft routes and then test them with your body, bridging instinct and intellect.",
                        "The result crowns you as a narrator who distributes signals carefully without exposing the opening move.",
                    ],
                ],
            },
            "why": {
                "ar": [
                    "تستمتع عندما تتحول البصمة الذهنية إلى لعبة صامتة.",
                    "تفضل بناء خطة متعددة الطبقات بدل الاندفاع العشوائي.",
                    "تقرأ الإشارات الصغيرة وتحوّلها إلى قرار من دون توتر.",
                    "تبحث عن مغامرة تستعير ذكاءك قبل قوتك.",
                ],
                "en": [
                    "You enjoy turning mental fingerprints into a quiet game.",
                    "You prefer layering plans instead of rushing with guesswork.",
                    "You translate tiny cues into decisions without tension.",
                    "You crave adventures that borrow your intellect before your power.",
                ],
            },
            "real": {
                "ar": [
                    "تعدّل إيقاعك فور رؤية خيال جديد لتبقي الخطوة التالية لغزًا.",
                    "تستخدم نظرة أو حركة أصابع كإشارة سرية لتغيير الاتجاه.",
                    "تدوّن في ذهنك أثر كل انتقال لتستدعيه عندما يتغير المشهد.",
                    "تسمح للخطوة بأن تتلاشى ثم تعود بإيماءة محسوبة تكسر التوقع.",
                ],
                "en": [
                    "Shift your tempo the moment a new silhouette appears so the next move stays enigmatic.",
                    "Use a glance or finger motion as a covert signal to redirect the sequence.",
                    "Catalog the feeling of each transition so you can reuse it when the scene pivots.",
                    "Let a step fade and return with a precise gesture that bends expectation.",
                ],
            },
            "notes": {
                "ar": [
                    "ذكّر نفسك أن البطء المتعمد يمنح الخطة قوة إضافية.",
                    "احفظ قاموسًا صغيرًا للإشارات كي لا تضيع التفاصيل.",
                    "اسمح للخيال أن يسبق الحركة حتى لو بدا المشهد ساكنًا.",
                    "إذا تكررت الفكرة، أعد صياغتها من زاوية جديدة بدل استنساخها.",
                ],
                "en": [
                    "Remind yourself that deliberate slowness reinforces the plan.",
                    "Keep a tiny glossary of cues so no detail is lost.",
                    "Let imagination outrun motion even when the scene feels still.",
                    "If an idea repeats, rewrite it from a new angle instead of cloning it.",
                ],
            },
        },
        {
            "id": "precision_hush",
            "trait_weights": {"calm": 0.55, "precision": 0.45, "solo": 0.25},
            "identity_weights": {"sensory": 0.35, "tactical": 0.15},
            "signature_terms": ["precision", "stillness", "hush"],
            "labels": {
                "ar": [
                    "مختبر اللمسة الهادئة",
                    "نواة الدقة الساكنة",
                    "أفق التناغم المحسوب",
                ],
                "en": [
                    "Quiet Precision Atelier",
                    "Stillness Calibration Core",
                    "Measured Harmony Deck",
                ],
            },
            "what": {
                "ar": [
                    [
                        "مجال تدريبي يدعوك لالتقاط أنفاس موزونة ثم تحويلها إلى خطوط حركة شفافة.",
                        "تزن كل انتقال كما لو أنك تلمس لوحة دقيقة، فتمنع أي ضجيج من اختراق التجربة.",
                        "التقدم يحدث حين تسمح للعقل أن يرسم المتتابعة، وللجسد أن ينفذها من دون أقواس زائدة.",
                    ],
                    [
                        "مخطط هادئ يبني جسورًا بين الاسترخاء والحدة لتتعلم كيف تجاور النعومة والحسم.",
                        "تراقب الاهتزازات الصغيرة في جسدك وتحوّلها إلى توقيع يضمن ثباتك.",
                        "كل ما عليك هو ترك الإيقاع الداخلي يقودك إلى خطوة نقية التطويع كأنك تصيغ قطعة موسيقية تحترم كل نبضة صغيرة.",
                    ],
                ],
                "en": [
                    [
                        "A learning field that invites you to balance each breath before converting it into translucent lines of motion.",
                        "You weigh every transition as if touching a delicate canvas, keeping interference far from the experience.",
                        "Progress appears when mind drafts the sequence and body executes it without extra flourishes.",
                    ],
                    [
                        "A calm blueprint that bridges relaxation and sharpness so you can place softness beside decisiveness.",
                        "You monitor micro-vibrations and convert them into a signature that keeps your posture steady.",
                        "All you do is let your internal rhythm guide you toward a neatly tuned step.",
                    ],
                ],
            },
            "why": {
                "ar": [
                    "تحب الشعور بأن التفاصيل الدقيقة هي التي تقود القصة.",
                    "تجد الراحة عندما يصبح التنفس جزءًا من الخطة.",
                    "تبحث عن تجربة تمنحك تركيزًا مستمرًا من دون ضجيج.",
                    "تحب سماع الرسائل الهادئة قبل أن تتحول إلى فعل.",
                ],
                "en": [
                    "You love when delicate details are the ones steering the story.",
                    "You relax once breathing becomes part of the plan.",
                    "You want a practice that keeps your focus alive without spectacle.",
                    "You enjoy hearing quiet messages before turning them into action.",
                ],
            },
            "real": {
                "ar": [
                    "تضبط كتفيك مع كل زفير لتذكّر نفسك بأن الاستقرار قرار داخلي.",
                    "تعدّل طول الخطوة كأنك تحرر مقطعًا موسيقيًا من أي حدة زائدة.",
                    "تختبر تنويعًا بسيطًا في مسار العين لتضمن أن التركيز لم يتشوه.",
                    "تجرب التوقف القصير ثم العودة السلسة لتؤكد أن العقل ما زال يقود.",
                ],
                "en": [
                    "Align your shoulders with each exhale to remember stability is internal.",
                    "Adjust the stride length as if editing a musical bar to remove excess tension.",
                    "Test a slight shift in eye path to ensure attention stays unblurred.",
                    "Experiment with a brief pause then a smooth return to prove mind remains in charge.",
                ],
            },
            "notes": {
                "ar": [
                    "دوّن نبرة التنفس التي منحتك أكبر حالة صفاء.",
                    "لا تسمح للتكرار أن يصبح آليًا؛ أدخل ملمسًا حسّيًا صغيرًا.",
                    "تذكر أن الصمت المحيط حليف وليس فراغًا.",
                    "إن شعرت بالسرعة، أبطئ الحكاية بدل مقاومة الجسد.",
                ],
                "en": [
                    "Record the breath tone that produced your clearest state.",
                    "Prevent repetition from going robotic by adding a tiny sensory cue.",
                    "Remember surrounding silence is an ally, not a void.",
                    "If speed creeps in, slow the story instead of wrestling your body.",
                ],
            },
        },
        {
            "id": "signal_alliance",
            "trait_weights": {"team": 0.6, "puzzles": 0.3, "adrenaline": 0.2},
            "identity_weights": {"social": 0.4, "achievement": 0.2},
            "signature_terms": ["signal", "alliance", "team"],
            "labels": {
                "ar": [
                    "تحالف الإشارات الخفية",
                    "جماعة الحيلة التفاعلية",
                    "شبكة التناغم التشاركي",
                ],
                "en": [
                    "Hidden Signal Collective",
                    "Interactive Tactic Ensemble",
                    "Collaborative Rhythm Grid",
                ],
            },
            "what": {
                "ar": [
                    [
                        "منصة تعاون تزرع داخل الفريق لغة حركية مشفرة تستيقظ كلما تبادلتم النظرات.",
                        "تتعاقب الأدوار بسلاسة، فتغمر المجموعة طاقة تشعر أنها مشروع إبداعي لا مجرد تدريب.",
                        "كل عضو يضيف خيطًا تكتيكيًا، ومعًا تنسجون مشهدًا يحافظ على عنصر المفاجأة.",
                    ],
                    [
                        "تجربة لعب تشاركية تبني خريطة غير مرئية تسمح لكم بنقل القيادة دون إعلان.",
                        "تظهر براعتكم عندما تترجمون الهتاف الداخلي إلى إشارات مختزلة.",
                        "النهاية ليست فوزًا سريعًا بل قصة مشتركة ترفع سقف الثقة بينكم وتمنح كل فرد فرصة ليوقع بصمته الخاصة.",
                    ],
                ],
                "en": [
                    [
                        "A collaborative stage that plants an encrypted motion language awakening whenever glances cross.",
                        "Roles flow in calm succession so the group feels like a creative project rather than simple training.",
                        "Each member adds a tactical thread and together you weave a scene that protects surprise.",
                    ],
                    [
                        "A shared-play experience that sketches an invisible map letting you pass leadership without announcement.",
                        "Your brilliance shows when inner cheering becomes condensed signals.",
                        "The finish is not a quick win but a shared story that lifts everyone's trust.",
                    ],
                ],
            },
            "why": {
                "ar": [
                    "تتفوق عندما يتحدث الفريق بلغة مختصرة.",
                    "تحفزك فكرة أن النجاح هنا يُكتب بأكثر من يد.",
                    "تحب توليد شرارة مفاجأة تقرأها العيون قبل الكلمات.",
                    "تبحث عن تحدٍ يحترم ذكاء التعاون.",
                ],
                "en": [
                    "You thrive when the team speaks in condensed language.",
                    "You feel driven knowing success here is co-written.",
                    "You enjoy sparking surprises that eyes decode before words.",
                    "You want a challenge that respects collaborative intelligence.",
                ],
            },
            "real": {
                "ar": [
                    "تنقل القيادة عبر إشارة صغيرة بالكتف لتبدل الإيقاع من دون كلام.",
                    "تعيد توزيع التشكيل خلال لحظات بفضل قاموس مشترك من الإيماءات.",
                    "تختبر فكرة جديدة ثم تسلمها لزميل يكملها بطابعه الخاص.",
                    "تستخدم صمتًا قصيرًا لتهيئة الفريق قبل الانعطاف المفاجئ.",
                ],
                "en": [
                    "Hand leadership over with a subtle shoulder cue to switch tempo silently.",
                    "Redistribute formation within seconds through a shared gesture lexicon.",
                    "Prototype an idea then pass it to a teammate who stamps their own style.",
                    "Use a short silence to prime the team before the sudden turn.",
                ],
            },
            "notes": {
                "ar": [
                    "ثبّت طقوسًا صغيرة لافتتاح كل جلسة كي يتوحّد الإيقاع.",
                    "شجّع تدوين اللمحات الملهمة حتى تتضاعف الأفكار.",
                    "ذكّر المجموعة أن المفاجأة لا تعني فوضى بل دقة تشاركية.",
                    "إن ارتفع الصوت، أعد ضبط النبرة إلى حوار هادئ.",
                ],
                "en": [
                    "Anchor a tiny opening ritual so rhythm unifies quickly.",
                    "Encourage jotting down inspiring moments to multiply ideas.",
                    "Remind the crew that surprise is precise collaboration, not chaos.",
                    "If volume climbs, reset the tone to a calm dialogue.",
                ],
            },
        },
        {
            "id": "vr_echo",
            "trait_weights": {"vr": 0.7, "puzzles": 0.2, "stealth": 0.2},
            "identity_weights": {"adventure": 0.4, "tactical": 0.15},
            "signature_terms": ["vr", "echo", "immersive"],
            "labels": {
                "ar": [
                    "مدار الواقع المتداخل",
                    "طيف المحاكاة الحية",
                    "متاهة الإشارات الافتراضية",
                ],
                "en": [
                    "Immersive Echo Circuit",
                    "Living Simulation Orbit",
                    "Virtual Signal Maze",
                ],
            },
            "what": {
                "ar": [
                    [
                        "رحلة تتنقل بين طبقات واقع متداخل، حيث تؤثر كل حركة على قصة رقمية تتشكل حولك وتشعر أن الحدود بين الواقع والخيال تتلاشى برفق.",
                        "تتعامل مع الألوان والصوت كأنها ألغاز يجب فكّها قبل الانتقال إلى المرحلة التالية.",
                        "الهدف أن تكتشف كيف يمكن للخيال التقني أن يدعم جرأتك من دون أن يفقدك الهدوء.",
                    ],
                    [
                        "تجربة معدّة لتختبر ذكاءك داخل فضاء محاكى يتفاعل مع نبضك وإيماءاتك.",
                        "كل مرة تبتكر مسارًا جديدًا، تعيد الخوارزمية تحليل خطواتك وتمنحك مشهدًا مطورًا.",
                        "تشعر وكأنك تهندس لعبة خاصة بك، بقدر ما تستمتع بإعادة تصميمها من الداخل فتكتشف كيف يعيد الخيال صياغة شجاعتك كل مرة.",
                    ],
                ],
                "en": [
                    [
                        "A journey moving through layered realities where each action edits a digital story around you.",
                        "You treat color and sound as puzzles to solve before stepping into the next phase.",
                        "The aim is to prove tech-driven imagination can amplify your courage without draining your calm.",
                    ],
                    [
                        "An experience built to test your intellect inside a simulated realm that reacts to pulse and gesture.",
                        "Whenever you design a new route, the algorithm reinterprets it and gifts you a refreshed scene.",
                        "You feel as if you are engineering your own game while enjoying its constant re-design.",
                    ],
                ],
            },
            "why": {
                "ar": [
                    "تحب المزج بين الخيال الرقمي والمهارة الذهنية.",
                    "تستمتع عندما تتحول التكنولوجيا إلى شريك استراتيجي.",
                    "تنجذب إلى التجارب التي تتغير كلما قدمت فكرة جديدة.",
                    "تقدّر المسارات التي تسمح لك بالاختفاء ثم الظهور بشكل مبتكر.",
                ],
                "en": [
                    "You adore mixing digital imagination with mental skill.",
                    "You enjoy technology acting as a strategic teammate.",
                    "You gravitate to experiences that evolve when you offer a new idea.",
                    "You value routes that let you vanish and reappear creatively.",
                ],
            },
            "real": {
                "ar": [
                    "تختبر نمطًا بصريًا جديدًا ثم تقيس تأثيره على تنفسك قبل تثبيته.",
                    "تعيد برمجة ترتيب المراحل لتصنع تحديًا يعكس بصمتك.",
                    "تستخدم وقفات قصيرة لتحليل المعلومات القادمة من النظام.",
                    "ترسم في ذهنك خريطة افتراضية تساعدك على احتواء المفاجآت.",
                ],
                "en": [
                    "Try a new visual motif then evaluate how it shifts your breathing before committing.",
                    "Reprogram the stage order to craft a challenge that mirrors your signature.",
                    "Use micro-pauses to analyse the feedback streaming from the system.",
                    "Sketch a virtual map in your mind to manage any surprise.",
                ],
            },
            "notes": {
                "ar": [
                    "دوّن الإلهامات التقنية حتى تبني أرشيفًا شخصيًا.",
                    "وازن بين الفضول والراحة كي لا يتحول الانبهار إلى إرهاق.",
                    "احمِ عينيك من التشبع البصري عبر لحظات استرخاء قصيرة.",
                    "ذكّر نفسك أن التقنية وسيلة لقصتك وليست بديلًا عنها.",
                ],
                "en": [
                    "Document tech inspirations to build a personal archive.",
                    "Balance curiosity with comfort so wonder never becomes fatigue.",
                    "Protect your eyes from overload by inserting short rests.",
                    "Remind yourself technology serves your story, not the other way around.",
                ],
            },
        },
        {
            "id": "pulse_dash",
            "trait_weights": {"adrenaline": 0.6, "precision": 0.3, "stealth": 0.2},
            "identity_weights": {"achievement": 0.35, "adventure": 0.25},
            "signature_terms": ["pulse", "dash", "focus"],
            "labels": {
                "ar": [
                    "اندفاع النبض المحسوب",
                    "وحدة الشعلة المتوازنة",
                    "أفق الإيقاع المركّز",
                ],
                "en": [
                    "Calibrated Pulse Rush",
                    "Balanced Flame Unit",
                    "Focused Rhythm Horizon",
                ],
            },
            "what": {
                "ar": [
                    [
                        "مسار ديناميكي يمنحك إثارة محسوبة حيث يرتفع النبض لكن العقل يظل المخرج.",
                        "تعتمد على تغييرات سرعة مخطط لها مسبقًا لتثبت أنك تستطيع الجمع بين الجرأة والدقة.",
                        "كل قفزة فكرية تسبق الحركة، فتتحول الطاقة العالية إلى لوحة منسجمة وتلمس كيف يتحول الانفجار إلى نغمة واعية.",
                    ],
                    [
                        "برنامج مصمم ليشعل الحماس ثم يوجهه برفق لتبقى السيطرة في يدك.",
                        "تتعلم كيف تدير دفعات الأدرينالين عبر هندسة انتقالات قصيرة ومتقنة.",
                        "التجربة تذكرك بأن الإبداع يمكن أن يكون صاخبًا من الداخل، لكنه هادئ في شكله الخارجي ويمنحك قدرة على إعادة تشغيل الحماس متى شئت.",
                    ],
                ],
                "en": [
                    [
                        "A dynamic path delivering measured thrill where pulse spikes yet mind stays the director.",
                        "You rely on pre-planned tempo shifts to prove courage can coexist with precision.",
                        "Every mental leap precedes motion so high energy becomes a coherent canvas.",
                    ],
                    [
                        "A program built to ignite excitement then steer it gently so control remains yours.",
                        "You learn to manage adrenaline bursts by engineering short, exact transitions.",
                        "The experience reminds you creativity can roar inside while looking composed outside.",
                    ],
                ],
            },
            "why": {
                "ar": [
                    "تحب الإحساس بحرارة الطاقة عندما تظل الخطة في يدك.",
                    "تبحث عن مغامرة تجعل الجرأة أداة مدروسة.",
                    "تستمتع بتصعيد الحماس ثم تهدئته وفق إشارة منك.",
                    "تحتاج لإثبات أن سرعتك يمكن أن تكون واعية.",
                ],
                "en": [
                    "You love feeling energy flare while the plan stays in your hands.",
                    "You want an adventure that turns boldness into a calculated tool.",
                    "You enjoy raising excitement then settling it on your cue.",
                    "You need to prove your speed can remain mindful.",
                ],
            },
            "real": {
                "ar": [
                    "ترسم في ذهنك خطًا ثلاثي الأجزاء لضبط ارتفاع الطاقة وانخفاضها.",
                    "تستخدم إشارة داخلية تشعر بها في صدرك لتحديد لحظة تخفيف الاندفاع.",
                    "تعيد تشكيل الاستراتيجية فورًا إذا شعرت بأن الحماس تجاوز الحدود التي رسمتها.",
                    "تدمج وقفات قصيرة من التنفس العميق لتعيد التوازن من دون كبح الإثارة.",
                ],
                "en": [
                    "Sketch a three-part mental line to regulate when energy rises and eases.",
                    "Use an internal cue pulsing in your chest to decide when to soften the surge.",
                    "Rework the strategy instantly when excitement crosses the edge you set.",
                    "Blend brief deep-breath moments to restore balance without muting thrill.",
                ],
            },
            "notes": {
                "ar": [
                    "راقب الإشارات الجسدية التي تسبق الإفراط لتبقى متحكمًا.",
                    "لا تترك الحماس يقود وحده؛ ذكر نفسك دومًا بالغاية الإبداعية.",
                    "احتفل بالهدوء بعد الاندفاع لأنه دليل على النضج.",
                    "إن شعرت بالتشتت، عد إلى مخططك الذهني بدل زيادة السرعة.",
                ],
                "en": [
                    "Track the bodily cues that warn of overload so you stay in command.",
                    "Do not let excitement steer solo; keep the creative aim in sight.",
                    "Celebrate the calm after the rush because it proves maturity.",
                    "If focus scatters, return to your mental blueprint instead of speeding up.",
                ],
            },
        },
    ]


FALLBACK_BLUEPRINTS = _fallback_blueprints()


def _egate_fallback(identity: Dict[str, float], traits: Dict[str, float], rng: random.Random) -> List[Dict[str, Any]]:
    scored: List[Tuple[float, Dict[str, Any]]] = []
    for blueprint in FALLBACK_BLUEPRINTS:
        score = 0.0
        for key, weight in blueprint.get("trait_weights", {}).items():
            score += traits.get(key, 0.42) * weight
        for key, weight in blueprint.get("identity_weights", {}).items():
            score += identity.get(key, 0.45) * weight
        scored.append((score + rng.random() * 0.01, blueprint))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [bp for _, bp in scored]


def _top_trait_terms(traits: Dict[str, float], limit: int = 3) -> List[str]:
    ordered = sorted(traits.items(), key=lambda item: item[1], reverse=True)
    return [name for name, value in ordered[:limit] if value >= 0.6]


def _fallback_identity(blueprint: Dict[str, Any], lang: str, identity: Dict[str, float], traits: Dict[str, float], drivers: List[str], rng: random.Random) -> Dict[str, Any]:
    locale = "ar" if lang in ("العربية", "ar") else "en"
    label = rng.choice(blueprint["labels"][locale])
    what_variant = rng.choice(blueprint["what"][locale])
    what_lines = [_mask_names(_scrub_forbidden(line, lang)) for line in what_variant]
    why_pool = list(blueprint["why"][locale])
    if drivers:
        driver_sentence = _mask_names(_scrub_forbidden(drivers[0], lang))
        if driver_sentence:
            why_pool.append(driver_sentence)
    if len(why_pool) >= 3:
        why_selected = rng.sample(why_pool, k=3)
    elif len(why_pool) == 2:
        why_selected = list(why_pool)
    elif why_pool:
        why_selected = why_pool * 2
    else:
        why_selected = []
    if len(why_selected) > 3:
        rng.shuffle(why_selected)
        why_selected = why_selected[:3]
    if len(why_selected) < 2 and why_pool:
        base = why_selected or why_pool[:1]
        why_selected = (base * 2)[:2]
    seen: set[str] = set()
    deduped: list[str] = []
    for item in why_selected:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    why_selected = deduped[:3]
    if len(why_selected) < 2:
        extra = next((line for line in blueprint["why"][locale] if line not in why_selected), None)
        if extra:
            why_selected.append(extra)
    if len(why_selected) < 2:
        base = why_selected or blueprint["why"][locale][:1]
        why_selected = (base * 2)[:2]
    real_pool = blueprint["real"][locale]
    notes_pool = blueprint["notes"][locale]
    real_selected = rng.sample(real_pool, k=min(3, len(real_pool)))
    notes_selected = rng.sample(notes_pool, k=min(3, len(notes_pool)))
    signature_terms = set(blueprint["signature_terms"])
    signature_terms.update(_top_trait_terms(traits))
    signature_terms.update(label.lower().split())
    signature = f"{blueprint['id']}::{rng.random():.4f}"
    return {
        "sport_label": _mask_names(_scrub_forbidden(label, lang)),
        "what_it_looks_like": what_lines,
        "why_you": why_selected,
        "real_world": real_selected,
        "notes": notes_selected,
        "signature": signature,
        "signature_terms": list(signature_terms),
    }


def _card_signature_text(card: Dict[str, Any]) -> str:
    what = card.get("what_it_looks_like", [])
    if isinstance(what, list):
        what_text = " ".join(str(x) for x in what)
    else:
        what_text = str(what)
    why = card.get("why_you", [])
    if isinstance(why, list):
        why_text = " ".join(str(x) for x in why)
    else:
        why_text = str(why)
    real = card.get("real_world", [])
    if isinstance(real, list):
        real_text = " ".join(str(x) for x in real)
    else:
        real_text = str(real)
    notes = card.get("notes", [])
    if isinstance(notes, list):
        notes_text = " ".join(str(x) for x in notes)
    else:
        notes_text = str(notes)
    joined = f"{card.get('sport_label', '')} {what_text} {why_text} {real_text} {notes_text}"
    return _postprocess_text(joined)


def _quality_filter(card: Dict[str, Any], lang: str) -> bool:
    what = card.get("what_it_looks_like", [])
    if isinstance(what, list):
        what_text = " ".join(what)
    else:
        what_text = str(what)
    if len(_scrub_forbidden(what_text, lang)) < 220:
        return False
    for section in ("why_you", "real_world", "notes"):
        values = card.get(section, [])
        if isinstance(values, list):
            cleaned = [str(item).strip() for item in values if str(item).strip()]
        else:
            cleaned = [seg.strip() for seg in str(values).splitlines() if seg.strip()]
        if len(cleaned) < 2:
            return False
        joined = " ".join(cleaned).lower()
        for term in ("minute", "hour", "week", "cost", "price", "equipment", "location", "stadium", "gear", "ball", "court", "مكان", "موقع", "ساعة", "دقيقة", "معدات", "ملعب", "صالة", "تكلفة", "سعر", "وقت"):
            if term in joined:
                return False
    return True


def _hard_dedupe_and_fill(initial_cards: List[Dict[str, Any]], blueprint_order: List[Dict[str, Any]], lang: str, identity: Dict[str, float], traits: Dict[str, float], drivers: List[str], rng: random.Random) -> List[Dict[str, Any]]:
    final_cards: List[Dict[str, Any]] = []

    def _is_unique(candidate: Dict[str, Any]) -> bool:
        cand_text = _card_signature_text(candidate)
        return all(_jaccard(_card_signature_text(existing), cand_text) <= 0.6 for existing in final_cards)

    for card in initial_cards:
        if _quality_filter(card, lang) and _is_unique(card):
            final_cards.append(card)
    for blueprint in blueprint_order:
        attempts = 0
        while len(final_cards) < 3 and attempts < 6:
            candidate = _fallback_identity(blueprint, lang, identity, traits, drivers, rng)
            attempts += 1
            if not _quality_filter(candidate, lang):
                continue
            if not _is_unique(candidate):
                continue
            final_cards.append(candidate)
        if len(final_cards) >= 3:
            break
    while len(final_cards) < 3 and blueprint_order:
        candidate = _fallback_identity(rng.choice(blueprint_order), lang, identity, traits, drivers, rng)
        candidate["sport_label"] = candidate["sport_label"] + (" ∂" if lang in ("العربية", "ar") else " ∂")
        candidate["signature"] = candidate.get("signature", "sig") + f":{rng.random():.3f}"
        if _quality_filter(candidate, lang) and _is_unique(candidate):
            final_cards.append(candidate)
    return final_cards[:3]


# Archetype content ---------------------------------------------------------

def _archetype_data() -> Dict[str, Dict[str, Any]]:
    ar = "ar"
    en = "en"
    data: Dict[str, Dict[str, Any]] = {
        "tactical_immersive": {
            "score": lambda ident: ident["tactical"] + 0.35 * ident["achievement"],
            "titles": {
                ar: ["Tactical Immersive Combat", "سرد تكتيكي حي"],
                en: ["Tactical Immersive Combat", "Live Tactical Narrative"],
            },
            "silent": {
                ar: [
                    "{drivers}. هذا الأثر الهادئ يمنحك شعورًا بأنك قائد خلف الكواليس يقرأ المشهد من الأعلى قبل أن يلامس الأرض. تحب أن تتذوق لحظة الترقب تلك، حيث تتداخل خرائط ذهنية دقيقة وتلتقط عيناك أضعف الإشارات. كلما طال الصمت الأولي ازداد وضوح الهدف وكأنك تبني سيناريو سريًا لا يراه سواك.",
                    "{drivers}. تشعر بأن عقلك هو غرفة عمليات مصغّرة، تسمع فيها وقع الخطوات القادمة قبل وصولها، وتمنحك المسافة ما يكفي لإعادة ترتيب القطع. هذا المحرك الصامت يذكّرك بأن الذكاء ليس ادعاءً بل حضور مستتر ينتظر اللحظة المناسبة ليعلن نفسه."],
                en: [
                    "{drivers}. The quiet impact makes you feel like a director behind the curtain, surveying the scene before anything touches the floor. You savour that moment of anticipation where intricate mental maps overlap and your eyes register faint signals. The longer the initial silence, the clearer the mission becomes, as if you are scripting a secret story.",
                    "{drivers}. Your mind behaves like a compact command room that hears approaching steps before they arrive, gifting you a chance to reorganise the board. This silent engine reminds you that intelligence is not a show but a subtle presence waiting for the right cue."],
            },
            "what": {
                ar: [
                    "هذه الهوية تجمعك مع مساحات تحاكي ألعاب التجسس والأفلام الذهنية. تدخل قاعة أو بيئة واقع افتراضي تتغير مع كل خطوة، فتجد مسارات ضوء تفتح وتغلق، وأصواتًا تحرك خيالك الاستراتيجي. يُطلب منك تصميم فخاخ ذهنية أو تدوين ملاحظات عن إيماءاتك، لتشعر أن التدريب نفسه قصة غامرة كتبتها بنفسك." ,
                    "تجد نفسك في عالم يدمج التكنولوجيا بالحركة: غرف مغلقة قابلة لإعادة التشكيل، وأجهزة تراقب زاوية نظرك لتعطيك ردود فعل ذكية. يتم تشجيعك على بناء منظومات خداع بصري، واختبار سيناريوهات متعددة، وكأنك تحيي رواية متجددة في كل مرة."],
                en: [
                    "This identity pairs you with spaces that echo stealth games and cerebral films. You enter a hall or VR environment that morphs with each step, witnessing beams of light opening and closing while sounds stir your strategic imagination. You are invited to engineer mental traps and journal your gestures so the practice itself becomes a story you authored.",
                    "You inhabit a realm that fuses technology with deliberate movement: modular rooms, sensors tracking your gaze, and responsive cues. You are encouraged to craft optical misdirection and rehearse multiple scenarios, as though you revive a fresh narrative each time."],
            },
            "why": {
                ar: [
                    "لأنك تبحث عن متعة السيطرة دون صخب، ولأن القرارات المحسوبة تمنحك راحة داخلية لا تشبه فوزًا سريعًا. هذا الأسلوب يحترم رغبتك في اختبار ذكائك الحركي، ويمنحك مساحة لتجريب جرأة جديدة كل مرة دون فقدان الهيبة. تشعر بأنك تخلق لغة خاصة بين الجسد والعقل." ,
                    "تنجذب لهذا المسار لأنه يسمح لك بالاحتفاظ بأناقتك الفكرية أثناء الحركة. توازن بين الحذر والاندفاع، وتستمتع حين ترى التخطيط يتجسد على الأرض. ليس الهدف إثارة الإعجاب بل بناء يقين داخلي بأن ذكاءك قابل للترجمة إلى حركة ملموسة."],
                en: [
                    "Because you crave mastery without noise and calculated decisions soothe you more than quick wins. This approach honours your desire to challenge your kinetic intellect, letting you test bold ideas without losing grace. You end up crafting a personal language between mind and body.",
                    "You lean toward this path because it lets you keep intellectual elegance while moving. You balance caution and momentum and enjoy watching strategy take physical form. The goal is not applause but the inner certainty that your intelligence can migrate into motion."],
            },
            "real": {
                ar: [
                    "في الواقع قد تبدأ بدخول مساحة شبه مظلمة تضيء أجسامها الذكية بمجرد أن تستشعر خطواتك. يتم تمرير أهداف مرئية وصوتية أمامك، فتتعلم استخدام نظراتك وإشارات كتفك قبل أي حركة. كل حصة تنتهي بحوار قصير مع ذاتك، تستعرض فيه ما التقطته حواسك من تفاصيل." ,
                    "ستختبر جلسات تتدرج من مشي مترقب إلى مواجهات افتراضية سريعة، مع مجال لإعادة التجربة من زوايا مختلفة. المدرب أو التطبيق يصغي لأسئلتك ويعيد بناء المشهد بناءً على فضولك، لتخرج بقصة جديدة في كل مرة."],
                en: [
                    "In reality you may step into a semi-dark chamber where responsive surfaces glow once they sense your stride. Visual and audio targets sweep past, teaching you to deploy your gaze and shoulder cues before any bigger move. Each session ends with an inner debrief about the details your senses captured.",
                    "You experience sessions evolving from cautious walks to brisk virtual duels, always leaving room to replay from new angles. A coach or intelligent system listens to your questions and rebuilds the scene according to your curiosity, so every outing closes with a fresh storyline."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nتخيل موقفًا حقيقيًا شعرت فيه بأنك تريد قول شيء ولكنك التزمت الصمت لتحلل التفاصيل. اكتب ذلك في سطر واحد، ثم حوّله إلى مشهد تدريبي تستخدم فيه نفس المشاعر ولكن بحركة صغيرة، مثل التفاف الرأس أو خطوة للأمام. كلما أعدت المشهد وجدت زاوية جديدة تضاف إلى لغتك البدنية." ,
                    "🔄 ابدأ من هنا\nاستعد ذكرى موقف استحضرت فيه الجرأة الذهنية، واسأل نفسك كيف تبدو لو تحولت إلى حركة. مارس تصوير السيناريو بعينيك وأنت تمشي ببطء في الغرفة، ثم امنح جسدك إشارة ليترجم تلك الصورة. المهم أن تبقي الفكرة حية وتشعر بأن الخيال يسبق الفعل بثوانٍ طويلة."],
                en: [
                    "🔄 ابدأ من هنا\nRecall a real moment when you chose silence to analyse the details. Write it in one line, then convert it into a training vignette where you reuse the same emotions with a small gesture, like a head tilt or a forward step. Each retelling reveals a new angle in your body language.",
                    "🔄 ابدأ من هنا\nBring back a memory where mental courage guided you and ask how it would look if expressed physically. Practice drawing the scene with your eyes while strolling slowly, then let your body translate the idea. Keep the concept alive and let imagination precede action by several heartbeats."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nإذا تحوّل التدريب إلى صخب، أطفئ بعض الأضواء، أو بدّل الخلفية الصوتية إلى حوار هادئ. ذكّـر نفسك أن الذكاء قابل للتجديد، وأن الاستراحة الفكرية جزء من رحلتك. استعن بشريك يفهم شغفك كي يمدك بقراءات جديدة للمشهد." ,
                    "👁️‍🗨️ ملاحظات\nراقب متى تشعر بأن الخيال سبق الحركة، وسجل ذلك في مفكرة صغيرة. قد تكشف لاحقًا أن أفضل الأفكار أتت من لحظات الظل وليس من الضوء المباشر. امنح جسدك حرية إعادة ترتيب التسلسل كما يشاء دون توقعات صارمة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nIf the training turns noisy, dim some lights or switch to a quiet dialogue soundtrack. Remind yourself that intelligence renews itself and that mental pauses are part of the journey. Invite a partner who grasps your passion to offer new readings of each scene.",
                    "👁️‍🗨️ ملاحظات\nNotice when imagination leaps ahead of the move and jot it in a small notebook. You may later find that the finest ideas emerged from shadow rather than direct glare. Let your body reorder the storyline freely without strict expectations."],
            },
        },
        "stealth_flow": {
            "score": lambda ident: ident["sensory"] + 0.25 * ident["solo"],
            "titles": {
                ar: ["Stealth-Flow Missions", "انسياب الظلال الهادئ"],
                en: ["Stealth-Flow Missions", "Silent Flow Odyssey"],
            },
            "silent": {
                ar: [
                    "{drivers}. تحب أن تستمع إلى الصمت وهو يتنفس، وتفضل اللحظات التي ينساب فيها الهواء حولك دون أن يشعر بك أحد. هنا يصبح الهدوء محركًا حقيقيًا؛ يمنحك ثقة أن كل خطوة متوازنة مع نبضك الداخلي، وأنك تستطيع التلاعب بالمشهد من دون أن تفسد صفاءه." ,
                    "{drivers}. تتعامل مع الصمت كأداة فنية، فأنت لا تهرب منه بل تدعوه ليصبح شريكًا في الحركة. كلما تتبعت أنفاسك بعمق، انفتحت أمامك طبقات جديدة من الإحساس لا تحتاج إلى ضوضاء كي تثبت حضورها."],
                en: [
                    "{drivers}. You enjoy hearing silence breathe and prefer when air glides around you without drawing attention. Calm transforms into a genuine engine, gifting you the confidence that every step mirrors your pulse and lets you sculpt the scene gently.",
                    "{drivers}. You treat stillness as an artistic tool: you do not run from it, you invite it to partner with your movement. Each deep breath unveils new layers of sensation that never require noise to prove their existence."],
            },
            "what": {
                ar: [
                    "هذه الهوية تقودك إلى ممرات مظللة، غرف استوديو بعناية سينمائية، أو بيئات واقع افتراضي تلعب بالضوء والصوت لتضعك في حالة حلم يقظ. تتحسس الجدران، تغير اتجاهك كي تكتشف الانسياب المناسب، وتتعلم كيف تُذيب حركتك داخل المكان بدلًا من فرضها." ,
                    "ستتنقل بين منصات لينة، أقمشة معلقة، ودوائر إضاءة متدرجة، وكأنك ترقص مع ظلّك الشخصي. تُشجع على رسم مسارات متعرجة، حفر توقيعك على الأرض بلمسات خفيفة، والاستماع للفراغ وهو يجاوب على خطواتك."],
                en: [
                    "This identity ushers you through shaded hallways, studio rooms curated like slow-burn cinema, or VR landscapes that toy with light and sound to place you in a waking dream. You feel surfaces, alter direction to discover the right flow, and learn to dissolve your motion inside the space instead of imposing it.",
                    "You will move among soft platforms, suspended fabrics, and graduated light halos as if you dance with your own silhouette. You are encouraged to sketch winding trajectories, leave a delicate signature on the floor, and listen to empty space responding to your steps."],
            },
            "why": {
                ar: [
                    "لأنك تبحث عن تجربة تنغمس فيها حواسك من دون ضجيج خارجي، ولأنك تثمّن اللحظة التي يتحول فيها الجسد إلى ريشة ترسم إحساسًا يصعب وصفه بالكلمات. هذا المسار يمنحك سياقًا تستعرض فيه قدرتك على البقاء هادئًا حتى وأنت تتحرك بقوة." ,
                    "أنت تميل للهدوء الذي يحمل سرًا؛ لا تحتاج إلى صراخ كي تثبت وجودك، لكنك ترغب في ترك أثر ناعم يراه من يدقق. هنا يتم الاحتفاء برغبتك في الانغماس الداخلي، وتُمنح فرصة لتوليد جمال من مجرّد همسة حركة."],
                en: [
                    "Because you seek an experience where senses immerse without external commotion, and you value the moment when your body becomes a brush painting emotions words cannot contain. This path offers a context to showcase how calm remains even when you move powerfully.",
                    "You gravitate toward quiet that holds secrets; you do not need loud declarations yet still wish to leave a soft trace for attentive eyes. Here your desire for inner immersion is celebrated and you gain room to create beauty from a whisper of motion."],
            },
            "real": {
                ar: [
                    "في الواقع ستتعرف على تقنيات تجعل كل حصة مختلفة: أحيانًا تُطفأ الأضواء ويستعاض عنها بمصادر ضوء خافتة، وأحيانًا يُضاف بخار خفيف ليكشف مسار الهواء حولك. تعبر من وضعية لوقفة ثم إلى انزلاق، وتشعر أن كل تغير بسيط يفتح بوابة جديدة." ,
                    "قد تبدأ بجلسة استشعار تنصت فيها إلى نبضك، ثم تنتقل إلى مسار يجمع التوازن مع التحول السريع، دون أن تفقد إحساسك بالأمان. المدرب أو التطبيق يشجعك على استكشاف تفاصيل ملمس الأرض، ورصد كيف يستجيب جسدك لكل انعطافة."],
                en: [
                    "In practice you discover techniques that keep each session unique: sometimes lights dim to mere glows, other times a soft mist reveals air currents around you. You shift from stillness to poised stances to gliding sequences, realising that every subtle change opens a new portal.",
                    "You might begin with a sensing routine listening to your pulse, then ease into a pathway mixing balance with quick shifts without losing your sense of safety. A coach or app nudges you to notice textures underfoot and chart how your body answers each turn."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nاختر زاوية في غرفتك وأطفئ الإضاءة القوية، ثم دع شعاعًا صغيرًا يحدد مساحة اللعب. تحرك ببطء، وكأنك تكتب رسالة غير مرئية، ولاحظ كيف يتغير الإحساس عندما تقرّب يدك من الضوء أو تبتعد عنه. سجّل شعورك بعد التجربة لتعرف أي عنصر فتح لك الباب." ,
                    "🔄 ابدأ من هنا\nضع قطعة قماش خفيفة على كتفك وتحرك داخل الغرفة مع مراقبة تفاعل القماش مع الهواء. عندما تسمع حركته أو تراه يتمايل، استثمر تلك اللحظة لصنع إيقاعك الداخلي. الفكرة أن تجعل التفاصيل الصغيرة تعلن حضورك بدلاً من رفع الصوت."],
                en: [
                    "🔄 ابدأ من هنا\nPick a corner in your room, dim bright lights, and let a single glow define the playground. Move slowly as if writing an invisible letter and observe how sensation changes when your hand nears or leaves the beam. Journal the feeling afterwards to know which element opened the gate.",
                    "🔄 ابدأ من هنا\nPlace a light fabric on your shoulder and wander through the room while watching how it responds to the air. When you hear or see it sway, use that instant to craft your internal rhythm. The idea is to let tiny details announce your presence instead of raising the volume."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nلا تجعل التجربة تنحبس في مكان واحد؛ جرّب الروائح أو الخلفيات الموسيقية الهادئة أو تغيير درجة الحرارة قليلاً. حافظ على دفتر تسجل فيه اللحظات التي شعرت فيها أن جسدك اختفى داخل المشهد وأعد قراءتها حين تبحث عن إلهام جديد." ,
                    "👁️‍🗨️ ملاحظات\nإذا شعرت أن الانسياب أصبح آليًا، بدّل إيقاعات القدمين أو أدخل عنصرًا بصريًا جديدًا مثل خيط ضوء أو مرآة صغيرة. احتفل بكل مرة يذكرك فيها جسدك أن الصمت لا يعني الغياب بل الاستعداد لخطوة أجمل."],
                en: [
                    "👁️‍🗨️ ملاحظات\nDo not let the experience lock into one room; experiment with scents, hushed background music, or slight temperature shifts. Keep a notebook of moments when your body felt absorbed into the scene and revisit it when you need inspiration.",
                    "👁️‍🗨️ ملاحظات\nIf the flow turns automatic, alter foot rhythms or introduce a new visual element like a thin beam of light or a small mirror. Celebrate each time your body reminds you that silence is not absence but readiness for a finer move."],
            },
        },
        "urban_exploration": {
            "score": lambda ident: ident["adventure"] + 0.25 * ident["outdoor"],
            "titles": {
                ar: ["Urban Exploration Athletics", "رحلة الاستكشاف الحضري"],
                en: ["Urban Exploration Athletics", "Urban Discovery Circuit"],
            },
            "silent": {
                ar: [
                    "{drivers}. تشعر أن المدينة تناديك باسمك السري، وتمنحك أزقتها فرصة لإعادة كتابة العلاقة بينك وبين الحركة. صمتك الداخلي يتحول إلى بوصلة تستشعر بها أحجار الأرصفة وروائح المقاهي، فتدرك أن كل منعطف يخفي لعبة جديدة." ,
                    "{drivers}. لديك حس المغامر الذي يعرف كيف يختار لحظته، فلا تهرول بلا هدف ولا تتوقف بلا معنى. كل ما حولك يتحول إلى خريطة حية تتجاوب مع خطواتك الشعرية."],
                en: [
                    "{drivers}. You hear the city calling your hidden name and offering its alleyways as a canvas to rewrite your relationship with motion. Your inner quiet becomes a compass sensing pavement textures and café aromas, revealing a new game at every turn.",
                    "{drivers}. You possess the explorer’s instinct to choose the right moment—never rushing without purpose nor halting without intention. Everything around you becomes a living map that responds to your poetic stride."],
            },
            "what": {
                ar: [
                    "هذا الأركتايب يحول الأحياء إلى ملعب قصصي: جدران يمكن التسلق عليها، حواف ضيقة للتوازن، وأسقف تمارس عليها باركورًا مصممًا بعناية. تتعامل مع أعمدة الإنارة كأنها أصدقاء قدامى، وتحول الأرصفة إلى متاهة ممتعة من الانعطافات الذكية." ,
                    "ستكتشف أن كل شارع يخبئ مستوى جديدًا من المغامرة؛ ربما تنظم جولة جيوكاشينغ حركية مع أصدقاء، أو ترسم مساراتك على خريطة رقمية، فتشعر أن المدينة تستجيب لخيالك وتعيد تشكيل نفسها حولك."],
                en: [
                    "This archetype turns neighbourhoods into narrative playgrounds: walls for scaling, narrow edges for balance, and rooftops for carefully designed parkour. Streetlamps feel like longtime companions and sidewalks morph into delightful mazes of clever turns.",
                    "You discover that every street hides a fresh layer of adventure: perhaps you host a kinetic geocaching tour with friends or draw your paths on a digital map, sensing the city reshape itself around your imagination."],
            },
            "why": {
                ar: [
                    "لأنك تعشق الشعور بأن العالم مفتوح بلا قيود؛ تحب الحرية التي لا تحتاج تصريحًا، وتفرح حين يتحول الطريق اليومي إلى قصة أنت بطلها. هذا الأسلوب يمنحك صداقة مع المكان ويذكرك بأن الإلهام لا يعيش في قاعات مغلقة فقط." ,
                    "تفضل المغامرة التي تحمل معنى، لا مجرد حركة عشوائية. تستمتع بتوثيق اكتشافاتك ومشاركتها، وتشعر بأن الهوية الحركية تتوسع كلما أضفت تفاصيل جديدة إلى خارطة ذاكرتك."],
                en: [
                    "Because you love the sensation of a world without walls; you celebrate permissionless freedom and delight when daily routes become stories that star you. This approach befriends the city and reminds you that inspiration does not live solely in closed studios.",
                    "You prefer adventure with meaning, not random motion. You enjoy documenting discoveries and sharing them, feeling your movement identity grow whenever you add fresh details to your memory map."],
            },
            "real": {
                ar: [
                    "في التطبيق الواقعي ستعمل على مسح بصري للحي الذي تحبه، تدوّن النقاط التي يمكن القفز منها أو الالتفاف حولها، ثم تعود في أوقات مختلفة لتلاحظ تغيّر الإحساس. ربما تضيف عناصر فنية مثل خيوط قماش أو رسومات طباشير لتجعل المكان يتفاعل معك." ,
                    "قد تدمج بين الأسطح المرتفعة والجسور القصيرة والحدائق الصغيرة، لتخلق سلسلة مشاهد متتابعة. كل مشهد يشجعك على استخدام جسدك بأسلوب جديد، مثل التحرك جانبيًا أو الانحناء لالتقاط تفصيلة لم تلاحظها من قبل."],
                en: [
                    "In practice you visually survey a favourite district, noting points for vaults or sweeping turns, then revisit at different times to observe changing sensations. You might add artistic touches like fabric trails or chalk sketches so the space converses with you.",
                    "You may weave together raised platforms, short bridges, and pocket parks to craft sequential scenes. Each scene nudges you to use your body differently, perhaps moving sideways or bending to catch a detail you had never seen."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nاختر شارعًا قصيرًا تعرفه، وامشِ فيه ببطء مع التقاط ثلاث صور ذهنية لأماكن تجذبك. في اليوم التالي عد إلى أحد هذه الأماكن وابحث عن طريقة للتفاعل معه، كمحاولة لمس الحافة أو التحرك حوله بشكل فني. سجّل شعورك لتبني عليه مغامرة أطول." ,
                    "🔄 ابدأ من هنا\nاحمل معك خريطة ورقية صغيرة وارسم عليها مسارًا شاعريًا يربط بين نقطتين تحبهما. أثناء السير اتبع الخريطة وكأنك تمتلك سرًا، واستمتع بكل مفاجأة تظهر لك. استمع لقلبك حين يقترح انعطافة جديدة ولو للحظات."],
                en: [
                    "🔄 ابدأ من هنا\nPick a short street you know and walk it slowly while capturing three mental snapshots of spots that attract you. Return the next day to one location and find a way to interact with it—perhaps touching an edge or circling it artistically. Record the feeling and build a longer adventure from there.",
                    "🔄 ابدأ من هنا\nCarry a small paper map and sketch a poetic route connecting two places you adore. Follow it as if holding a secret, enjoying every surprise along the way. Listen to your heart whenever it suggests a new turn, even for a brief moment."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nحافظ على سلامتك باختيار مواقع مدروسة واستشارة صديق يرافقك في البداية. اصنع أرشيفًا بصريًا لما تكتشفه، فربما تلهم تجربتك آخرين يبحثون عن طريقة جديدة للتواصل مع المدينة." ,
                    "👁️‍🗨️ ملاحظات\nغيّر أوقاتك بين الصباح والمساء لترى كيف تتغير الشخصية الحسية للشارع. لا تستعجل توثيق كل شيء؛ دع بعض الأسرار محفوظة لك وحدك كي تظل الرحلة مدهشة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nStay safe by choosing thoughtful spots and inviting a friend for early explorations. Build a visual archive of what you discover; your journey may inspire others seeking a fresh relationship with the city.",
                    "👁️‍🗨️ ملاحظات\nSwap between morning and evening to feel how the street’s sensory character shifts. Do not rush to document everything; leave a few secrets for yourself so the journey keeps its sparkle."],
            },
        },
        "precision_duel": {
            "score": lambda ident: ident["tactical"] + 0.25 * ident["solo"],
            "titles": {
                ar: ["Precision Duel Sports", "منازلة الدقة الهادئة"],
                en: ["Precision Duel Sports", "Quiet Precision Duels"],
            },
            "silent": {
                ar: [
                    "{drivers}. تميل إلى اللحظة التي يتوقف فيها الزمن قبل الإطلاق، وتشعر بأن أعصابك تملك لغة خاصة لا يمكن سماعها. تحب أن تتذوق ثباتك الداخلي قبل أن تتحول الفكرة إلى حركة، وكأنك تكتب معادلة لا تُحل إلا عندما تنفذها." ,
                    "{drivers}. تنتظر لحظة اللمسة النهائية كما ينتظر الرسام ضربته الأخيرة، تراجع زوايا كتفك وتستمع للهدوء الذي يسبق اللقطة. يهمك أن يبقى الذكاء حاضرًا حتى في أهدأ لحظاتك."],
                en: [
                    "{drivers}. You linger in the moment when time halts before release, sensing that your nerves speak a private language. You savour inner steadiness before an idea becomes motion, as if writing an equation solved only in execution.",
                    "{drivers}. You await the finishing touch like a painter waits for the final stroke, reviewing shoulder angles and enjoying the hush preceding the cue. Keeping intellect active even during stillness matters to you."],
            },
            "what": {
                ar: [
                    "هذه الهوية تجمع الرماية الهادئة مع المبارزة المتزنة، وتمنحك فرصة لتشعر بأن جسدك آلة دقيقة تستجيب لأقل إشارة. تتحرك في مناطق تتخذ شكل مسار شرف، حيث تراقب الكتفين والقدمين كما لو كنت قائد فرقة موسيقية." ,
                    "ستجد أن أدواتك – سواء كانت قوسًا أو سيفًا أو مضربًا – تتحول إلى امتداد لفكرك. تتعلم كيف تطلق الحركة من دون تشنج، وتحتفي بكل ضربة متقنة كأنها توقيع خاص بك."],
                en: [
                    "This identity merges quiet archery with balanced duelling, letting your body behave like a precision instrument responding to the slightest cue. You move in spaces shaped like honour lanes, observing shoulders and feet as if conducting an orchestra.",
                    "You discover that your tools—be it bow, blade, or paddle—become extensions of thought. You learn to release motion without tension and celebrate every accurate strike as a personal signature."],
            },
            "why": {
                ar: [
                    "لأنك تفضل الإنجاز الصامت الذي يترك أثرًا عميقًا دون ضوضاء، وتؤمن بأن الأناقة الحركية جزء من هويتك. هذا المسار يتيح لك سكب ذكائك في كل ضربة بدقة غير متكلفة." ,
                    "تنتمي لهذا النمط لأنك توازن بين الحماس الداخلي والحضور الخارجي. تحب أن ترى النتيجة تظهر كوميض، لا كصراخ، وتشعر بالرضا حين يصفق قلبك قبل أي شخص آخر."],
                en: [
                    "Because you prefer quiet accomplishments leaving deep traces without noise and believe kinetic elegance defines you. This path lets you pour your intellect into each strike with effortless precision.",
                    "You belong here because you balance internal fire with composed presence. Seeing results appear as a flicker rather than a shout pleases you, and you relish the moment your heart applauds before anyone else."],
            },
            "real": {
                ar: [
                    "ستمر بجلسات تدريجية تبدأ بتمارين توازن وتنفس، ثم تنتقل إلى إطلاقات مركزة تُراجع بعدها تسجيلاتك أو ملاحظاتك. تتعلم قراءة أصابعك قبل الحركة، وضبط إيقاعك على نبض داخلي ثابت." ,
                    "قد يطلب منك أن تستبدل الأداة كل فترة كي تشعر بالفروق الدقيقة، أو أن تجرب المواجهة من زوايا متعددة. كل تجربة تعلّمك كيف تحافظ على أناقتك حتى عندما ترتفع حرارة المنافسة."],
                en: [
                    "You’ll progress through sessions starting with balance and breath work, then move to focused releases followed by reviewing footage or notes. You learn to read your fingers before movement and sync your tempo with a steady inner beat.",
                    "You may be asked to switch equipment occasionally to feel subtle differences or to duel from various angles. Each experience teaches you to keep elegance alive even when competition heats up."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nقف أمام مرآة وتخيل أنك تستعد لضربة حاسمة، ثم راقب كتفيك وراحة يديك. كرر التخيل مع تغيير بسيط في زاوية القدم أو زاوية الرأس، ولاحظ كيف يتغير الإحساس الداخلي. دوّن ما يمنحك شعور الاتزان." ,
                    "🔄 ابدأ من هنا\nاختر غرضًا بسيطًا في منزلك وتعامل معه كهدف دقيق: وجه نظرك نحوه، ثم حرر الحركة ببطء المخرجة التي تقود مشهدًا صامتًا. ركز على الشهيق والزفير قبل وبعد الحركة لتعرف كيف تستدعي الثقة وقت الحاجة."],
                en: [
                    "🔄 ابدأ من هنا\nStand before a mirror imagining a decisive strike, observing your shoulders and palms. Repeat the imagination while slightly altering foot or head angles, noticing how inner sensation changes. Record what gifts you that balanced feeling.",
                    "🔄 ابدأ من هنا\nPick a simple object at home and treat it as a precise target: direct your gaze, then release the move like a director guiding a silent scene. Track inhalation and exhalation before and after motion to learn how to summon confidence on demand."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nحافظ على طقوس صغيرة قبل كل حصة مثل ترتيب الأدوات أو لمس الأرض بأطراف أصابعك. إذا شعرت بأن الإيقاع أصبح ميكانيكيًا، استعن بسرد قصصي قصير لتعيد الحيوية وتسأل نفسك ماذا تعني هذه الضربة لشخصيتك." ,
                    "👁️‍🗨️ ملاحظات\nلا تقارن سرعتك بالآخرين؛ ركز على وضوح نيتك. احتفل بكل مرة تشعر فيها بأن الحركة خرجت كما تخيلتها، ولو كانت بسيطة. سجّل تلك اللحظات كي تبني أرشيفًا للثقة."],
                en: [
                    "👁️‍🗨️ ملاحظات\nKeep small rituals before each session—aligning equipment or grounding fingertips—to anchor your mind. If the rhythm turns mechanical, weave a short narrative to revive excitement and ask what the strike means to your character.",
                    "👁️‍🗨️ ملاحظات\nDo not compare your pace with others; focus on clarity of intent. Celebrate whenever a move unfolds exactly as imagined, even if it’s subtle, and archive those moments to build confidence."],
            },
        },
        "creative_teamplay": {
            "score": lambda ident: ident["social"] + 0.2 * ident["tactical"],
            "titles": {
                ar: ["Creative Teamplay", "مختبر الفريق الإبداعي"],
                en: ["Creative Teamplay", "Creative Team Lab"],
            },
            "silent": {
                ar: [
                    "{drivers}. تلتقط شرارة المجموعة بسرعة وتشعر أن الحوارات غير المنطوقة بينكم هي الوقود الحقيقي. تحب أن تراقب كيف تتدفق الأفكار من نظرة أو إيماءة لتتحول فورًا إلى حركة جماعية مليئة بالابتكار." ,
                    "{drivers}. ترى في الفريق لوحة فنية دائمة التغير، وكل عضو يضيف ضربته الخاصة. المحرك الصامت لديك هو تلك القدرة على دمج الأفكار بسرعة مع الحفاظ على متعة اللعب."],
                en: [
                    "{drivers}. You catch the team’s spark instantly and feel that unspoken dialogues are the true fuel. You enjoy watching ideas flow from a glance or gesture and transform into inventive group motion.",
                    "{drivers}. You see the team as an ever-changing art piece where each member adds a unique stroke. Your silent driver is the ability to merge ideas swiftly while preserving the delight of play."],
            },
            "what": {
                ar: [
                    "تشمل التجربة فوتسال تكتيكي، كرة سلة نصف ملعب، أو ألعابًا تعاونية تعتمد على إشارات سريعة وخطى مبتكرة. تمتد الفكرة إلى جلسات تبادل أدوار حيث يتحول اللاعبون إلى مخرجين للحظة، يبتكرون خدعًا عاطفية تبقي الملعب حيًا وتضيف طبقات من المرح." ,
                    "ستعيش في بيئة تشجع على السرد الجماعي؛ كل تمريرة تحمل قصة صغيرة وكل حركة مرتجلة تُستقبل بابتسامة. يتم تشجيعكم على تصميم مجموعات فنية، واستبدال المراكز الحركية في منتصف الجلسة، لتبقى الطاقة نابضة."],
                en: [
                    "Experiences include tactical futsal, half-court basketball, or cooperative games relying on quick signals and inventive steps. Role-switch sessions turn players into momentary directors crafting emotional feints that keep the court vibrant and playful.",
                    "You inhabit an environment that celebrates collective storytelling; every pass carries a tiny tale and every improvisation earns a smile. You are encouraged to choreograph artistic clusters and swap positions mid-session so the energy keeps humming."],
            },
            "why": {
                ar: [
                    "لأنك تؤمن بأن المتعة تنبع من التشارك، وترى أن الحوار الحركي أجمل من التعليمات الجامدة. تحتاج إلى مساحة تسمح لك بأن تكون قائدًا ومتلقيًا في اللحظة نفسها، وهذا المسار يمنحك ذلك بحرية." ,
                    "تحب أن تبني كيمياء حقيقية مع الآخرين، وتفرح حين ترى فكرة بسيطة تتحول إلى لعبة كاملة. هذا الأسلوب يجعلك شريكًا في صناعة الذكريات وليس مجرد متفرج."],
                en: [
                    "Because you believe joy springs from collaboration and kinetic dialogue beats rigid instructions. You need a space that lets you lead and receive simultaneously, and this path grants that freedom.",
                    "You adore forging real chemistry with others and rejoice when a simple idea evolves into a full game. This style turns you into a co-creator of memories rather than a spectator."],
            },
            "real": {
                ar: [
                    "في الواقع ستشارك في جلسات يتم فيها تبديل الأدوار بسرعة: مرة تكون صانع اللعب، ومرة تكون من يختتم المشهد. تُستخدم أدوات بسيطة مثل أشرطة ملونة أو بطاقات أفكار لضخ جرعات من الإبداع طوال الوقت." ,
                    "قد تدمجون بين مساحات داخلية وخارجية، وتبتكرون تحديات صغيرة تحفز الحوار بينكم. كل جلسة تنتهي بجلسة تقييم لطيفة حيث يشارك كل فرد شعوره الشخصي بدون حكم."],
                en: [
                    "In practice you join sessions where roles shift quickly—one moment you craft the play, the next you close the scene. Simple props like coloured bands or idea cards feed creativity throughout.",
                    "You may blend indoor and outdoor spots, designing mini challenges that spark conversation. Each session ends with a gentle debrief where everyone shares personal feelings without judgment."],
            },
            "start": {
                ar: [
                    "🔄 ابدأ من هنا\nادعُ أصدقاءك لجلسة قصيرة تقسمون فيها الأدوار عشوائيًا، ثم اختر شخصًا واحدًا يقدّم فكرة مفاجئة. اتفقوا على رفع أيديكم كلما خطرت فكرة جديدة، ليصبح جسدكم لوحة إشارات مضيئة. في النهاية تحدثوا عن أكثر لحظة لمعت في قلوبكم." ,
                    "🔄 ابدأ من هنا\nحضّر بطاقة ملاحظات لكل فرد يكتب فيها شعورًا حركيًا يرغب في عيشه (مثل الدهشة أو الثقة). استخدموا هذه البطاقات كشرارة لبدء اللعب، وتذكروا أن تعطي كل شعور فرصته الكاملة قبل الانتقال لغيره."],
                en: [
                    "🔄 ابدأ من هنا\nInvite friends for a brief session where roles are assigned randomly, then pick one person to offer a surprise idea. Agree to raise your hands whenever a new spark arrives so your bodies become a board of luminous signals. Finish by sharing the moment that glowed in your hearts.",
                    "🔄 ابدأ من هنا\nPrepare note cards for each person to write a movement feeling they wish to live—wonder, trust, curiosity. Use these cards as sparks to kick off play and let every feeling enjoy its full spotlight before moving on."],
            },
            "notes": {
                ar: [
                    "👁️‍🗨️ ملاحظات\nإذا لاحظت أن الأدوار أصبحت ثابتة، أعد خلطها في منتصف الجلسة. شجع الجميع على التعبير الأولي قبل التفكير الطويل، واحتفظ بأرشيف صغير للفكاها والمواقف المدهشة." ,
                    "👁️‍🗨️ ملاحظات\nاحترم حدود كل فرد واستمع لطاقته اليومية كي لا يتحول اللعب إلى ضغط. استمر في تدوير الأماكن والأساليب، فالبيئة الجديدة تمنح أفكارًا جديدة دائمًا."],
                en: [
                    "👁️‍🗨️ ملاحظات\nIf roles become fixed, reshuffle them mid-session. Encourage instant expression before overthinking and maintain a tiny archive of funny or striking moments.",
                    "👁️‍🗨️ ملاحظات\nRespect everyone’s boundaries and energy so play never becomes pressure. Keep rotating venues and styles because new environments spark fresh ideas."],
            },
        },
    }
    return data


ARCHETYPES = _archetype_data()


def _select_archetype_keys(identity: Dict[str, float], rng: random.Random) -> List[str]:
    scored = []
    for key, data in ARCHETYPES.items():
        score_func = data["score"]
        scored.append((score_func(identity) + rng.random() * 0.05, key))
    scored.sort(reverse=True)
    keys = [key for _, key in scored[:3]]
    if len(keys) < 3:
        for key in ARCHETYPES.keys():
            if key not in keys:
                keys.append(key)
            if len(keys) == 3:
                break
    return keys[:3]


def _compose_card(key: str, identity: Dict[str, float], drivers: List[str], lang: str, rng: random.Random) -> str:
    data = ARCHETYPES[key]
    locale = "ar" if lang in ("العربية", "ar") else "en"
    drivers_sentence = _drivers_sentence(drivers, lang)

    title = rng.choice(data["titles"][locale])
    silent_t = rng.choice(data["silent"][locale]).format(drivers=drivers_sentence)
    what_t = rng.choice(data["what"][locale])
    why_t = rng.choice(data["why"][locale])
    real_t = rng.choice(data["real"][locale])
    start_t = rng.choice(data["start"][locale])
    notes_t = rng.choice(data["notes"][locale])

    sections = [
        f"🎯 {title}",
        "",
        "💠 المحرك الصامت:",
        silent_t,
        "",
        "💡 ما هي؟",
        what_t,
        "",
        "🎮 ليه تناسبك؟",
        why_t,
        "",
        "🔍 شكلها الواقعي",
        real_t,
        "",
        start_t,
        "",
        notes_t,
    ]
    card = "\n".join(sections)
    return card


def _postprocess_text(text: str) -> str:
    cleaned = text
    for word in BANNED_TERMS:
        if word in cleaned:
            cleaned = cleaned.replace(word, "هوية ممتعة")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r" +", " ", cleaned)
    return cleaned.strip()


def _dedupe(cards: List[str], keys: List[str], identity: Dict[str, float], drivers: List[str], lang: str, rng: random.Random) -> List[str]:
    for _ in range(6):
        changed = False
        for i in range(len(cards)):
            for j in range(i + 1, len(cards)):
                if _jaccard(cards[i], cards[j]) >= 0.6:
                    cards[j] = _compose_card(keys[j], identity, drivers, lang, rng)
                    cards[j] = _postprocess_text(cards[j])
                    changed = True
        if not changed:
            break
    return cards



def _clean_json_payload(text: str) -> str:
    text = (text or '').strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?', '', text, flags=re.IGNORECASE).strip()
        if text.endswith('```'):
            text = text[:text.rfind('```')].strip()
    return text


def _parse_llm_response(raw: str) -> Optional[List[Dict[str, str]]]:
    if not raw:
        return None
    cleaned = _clean_json_payload(raw)
    data: Any
    try:
        data = json.loads(cleaned)
    except Exception:
        match = re.search(r'(\{.*\}|\[.*\])', cleaned, flags=re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
        except Exception:
            return None
    if isinstance(data, dict):
        cards = data.get('cards') or data.get('recommendations')
    else:
        cards = data
    if not isinstance(cards, list):
        return None
    parsed: List[Dict[str, str]] = []
    for item in cards:
        if not isinstance(item, dict):
            continue
        lower = {str(k).lower(): str(v) for k, v in item.items()}
        title = lower.get('sport_label') or lower.get('title') or lower.get('heading') or ''
        what = lower.get('what') or lower.get('description') or ''
        why = lower.get('why') or lower.get('fit') or lower.get('reason') or ''
        real = lower.get('real') or lower.get('realistic') or lower.get('experience') or ''
        notes = lower.get('notes') or lower.get('tips') or lower.get('remarks') or ''
        if all(p.strip() for p in (title, what, why, real, notes)):
            parsed.append({
                'title': title.strip(),
                'what': what.strip(),
                'why': why.strip(),
                'real': real.strip(),
                'notes': notes.strip(),
            })
    return parsed if len(parsed) >= 3 else None


def _format_llm_card(data: Dict[str, str], lang: str) -> Dict[str, Any]:
    label = _mask_names(_scrub_forbidden(data.get('title', ''), lang))
    what_lines = [_mask_names(_scrub_forbidden(line, lang)) for line in _normalize_sentences(data.get('what', ''))][:3]
    if not what_lines:
        what_lines = [_mask_names(_scrub_forbidden(str(data.get('what', '')), lang))]
    why_lines = [_mask_names(_scrub_forbidden(line, lang)) for line in _normalize_sentences(data.get('why', ''))][:3]
    real_lines = [_mask_names(_scrub_forbidden(line, lang)) for line in _normalize_sentences(data.get('real', ''))][:3]
    notes_lines = [_mask_names(_scrub_forbidden(line, lang)) for line in _normalize_sentences(data.get('notes', ''))][:3]
    signature = hashlib.sha1((label or 'llm-card').encode('utf-8')).hexdigest()[:10]
    return {
        'sport_label': label or 'Identity Motion',
        'what_it_looks_like': what_lines,
        'why_you': why_lines,
        'real_world': real_lines,
        'notes': notes_lines,
        'signature': f"llm::{signature}",
        'signature_terms': [term for term in (label.lower().split() if label else ['llm'])],
    }


def _llm_cards_dual_model(
    answers: Dict[str, Any],
    identity: Dict[str, float],
    drivers: List[str],
    lang: str,
    traits: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    Dual-Model approach for sport recommendations:
    1. Reasoning Model (o1-mini): Analyzes user psychology deeply
    2. Intelligence Model (gpt-4o): Generates creative recommendations
    """
    if not DUAL_MODEL_ENABLED:
        return None
    
    print("[DUAL_MODEL] Starting dual-model recommendation pipeline...")
    
    # Step 1: Deep analysis with Reasoning Model
    print("[DUAL_MODEL] Phase 1: Analyzing user with Reasoning Model...")
    analysis = analyze_user_with_reasoning(answers, identity, traits or {}, lang)
    
    if not analysis:
        print("[DUAL_MODEL] Reasoning analysis failed, falling back...")
        return None
    
    # Step 2: Creative generation with Intelligence Model
    print("[DUAL_MODEL] Phase 2: Generating recommendations with Intelligence Model...")
    cards_raw = generate_recommendations_with_intelligence(analysis, drivers, lang)
    
    if not cards_raw:
        print("[DUAL_MODEL] Intelligence generation failed, falling back...")
        return None
    
    # Step 3: Format and validate cards
    cards: List[Dict[str, Any]] = []
    for item in cards_raw[:3]:
        if not isinstance(item, dict):
            continue
        
        card_struct = _format_llm_card({
            'title': str(item.get('sport_label') or item.get('title') or ''),
            'what': str(item.get('what') or item.get('description') or ''),
            'why': str(item.get('why') or item.get('fit') or ''),
            'real': str(item.get('real') or item.get('experience') or ''),
            'notes': str(item.get('notes') or item.get('tips') or ''),
        }, lang)
        
        if not _quality_filter(card_struct, lang):
            continue
        
        cards.append(card_struct)
    
    if len(cards) < 3:
        print(f"[DUAL_MODEL] Only {len(cards)} valid cards generated, falling back...")
        return None
    
    print(f"[DUAL_MODEL] Successfully generated {len(cards)} recommendations")
    return cards


def _llm_cards(
    answers: Dict[str, Any],
    identity: Dict[str, float],
    drivers: List[str],
    lang: str,
    traits: Optional[Dict[str, float]] = None,
) -> Optional[List[Dict[str, Any]]]:
    if chat_once is None or LLM_CLIENT is None:
        return None
    client = LLM_CLIENT
    main_model = CHAT_MODEL
    fallback_model = CHAT_MODEL_FALLBACK
    if not client or not main_model:
        return None

    driver_sentence = _drivers_sentence(drivers, lang)
    traits = traits or _derive_binary_traits(answers)
    try:
        answers_payload = json.loads(_stable_json(answers))
    except Exception:
        answers_payload = answers

    data = {
        'language': 'arabic' if lang in ('العربية', 'ar') else 'english',
        'identity_weights': identity,
        'traits': traits,
        'drivers': drivers,
        'drivers_sentence': driver_sentence,
        'requirements': {
            'sections': ['sport_label', 'what', 'why', 'real', 'notes'],
            'max_points': 3,
            'min_paragraphs': 2,
            'forbidden_terms': BANNED_TERMS + FORBIDDEN_TERMS_AR + FORBIDDEN_TERMS_EN,
            'style': 'tactical, sensory, imaginative, no time/cost/location/equipment, no cliché sport names',
        },
        'answers_hint': answers_payload,
    }

    if lang in ('العربية', 'ar'):
        system_prompt = (
            'أنت مساعد SportSync. أنشئ ثلاث بطاقات توصية متوازنة.'
            ' يجب أن تعيد استجابة بصيغة JSON تحتوي على قائمة باسم "cards".'
            ' كل بطاقة تضم الحقول sport_label, what, why, real, notes.'
            ' اجعل what فقرتين أو ثلاث جمل قصيرة، واجعل why/real/notes قوائم نقاط (2-3 عناصر).'
            ' تجنب ذكر الوقت أو التكلفة أو المواقع أو المعدات أو أسماء الرياضات الشائعة بشكل مباشر.'
            ' اجعل النبرة إنسانية وتكتيكية وتقدّر الخيال.'
        )
    else:
        system_prompt = (
            'You are the SportSync assistant. Produce three balanced recommendation cards.'
            ' Respond as JSON with a "cards" list where each card has sport_label, what, why, real, notes.'
            ' Ensure "what" contains two to three short sentences and why/real/notes are 2-3 bullet ideas.'
            ' Avoid mentioning time, cost, places, or equipment, and avoid generic sport names.'
            ' Keep the tone strategic, sensory, and imaginative.'
        )

    user_prompt = json.dumps(data, ensure_ascii=False)

    model_chain = main_model
    try:
        from core.llm_client import _split_models_csv as _split  # type: ignore
    except Exception:
        _split = None
    if fallback_model and _split:
        models_list = _split(main_model)
        if fallback_model not in models_list:
            model_chain = ','.join(models_list + [fallback_model]) if models_list else fallback_model
    try:
        raw = chat_once(
            client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model_chain or main_model,
            temperature=0.55,
            max_tokens=2200,
            top_p=0.9,
        )
    except Exception:
        return None

    parsed = _parse_llm_response(raw)
    if not parsed:
        return None

    cards: List[Dict[str, Any]] = []
    for item in parsed[:3]:
        if not isinstance(item, dict):
            return None
        card_struct = _format_llm_card({
            'title': str(item.get('sport_label') or item.get('title') or ''),
            'what': str(item.get('what') or item.get('description') or ''),
            'why': str(item.get('why') or item.get('fit') or ''),
            'real': str(item.get('real') or item.get('experience') or ''),
            'notes': str(item.get('notes') or item.get('tips') or ''),
        }, lang)
        if not _quality_filter(card_struct, lang):
            return None
        if any(_jaccard(_card_signature_text(existing), _card_signature_text(card_struct)) > 0.6 for existing in cards):
            return None
        cards.append(card_struct)
    return cards


def _parse_kb_card_to_dict(card_text: str, lang: str) -> Optional[Dict[str, Any]]:
    """
    تحويل نص بطاقة KB Ranker إلى dict structure
    يقرأ النص المنسق من kb_ranker.render_card ويحوله لـ dict
    """
    if not card_text or card_text == "—":
        return None
    
    lines = [l.strip() for l in card_text.split('\n') if l.strip()]
    
    card = {
        'sport_label': '',
        'what_it_looks_like': [],
        'why_you': [],
        'real_world': [],
        'notes': []
    }
    
    current_section = None
    
    for line in lines:
        # تجاهل الأسطر الفارغة والعناوين
        if not line or line.startswith(('🟢','🌿','🔮','---')):
            continue
        
        # تحديد القسم الحالي
        if '🎯' in line:
            # استخراج اسم الرياضة
            if ':' in line:
                card['sport_label'] = line.split(':')[-1].strip()
        elif any(marker in line for marker in ['💡','ما هي','What is it']):
            current_section = 'what'
        elif any(marker in line for marker in ['🎮','لماذا','ليه','Why','why']):
            current_section = 'why'
        elif any(marker in line for marker in ['⚙️','🚀','كيف تبدأ','How To Begin','First week']):
            current_section = 'start'
        elif any(marker in line for marker in ['🧠','✅','👁','ملاحظات','Notes']):
            current_section = 'notes'
        elif line.startswith('-') and current_section:
            # محتوى بنقاط
            text = line[1:].strip()
            if text:
                if current_section == 'what':
                    card['what_it_looks_like'].append(text)
                elif current_section == 'why':
                    card['why_you'].append(text)
                elif current_section == 'start':
                    card['real_world'].append(text)
                elif current_section == 'notes':
                    card['notes'].append(text)
        elif current_section and not any(marker in line for marker in ['🎯','💡','🎮','⚙️','🚀','🧠','✅','👁']):
            # سطر عادي ضمن القسم
            if current_section == 'what':
                card['what_it_looks_like'].append(line)
    
    # التأكد من وجود محتوى أساسي
    if not card['sport_label'] or not card['what_it_looks_like']:
        return None
    
    return card


def _generate_cards(
    answers: Dict[str, Any],
    lang: str,
    *,
    identity: Optional[Dict[str, float]] = None,
    drivers: Optional[List[str]] = None,
    traits: Optional[Dict[str, float]] = None,
    rng: Optional[random.Random] = None,
) -> List[Dict[str, Any]]:
    """
    توليد البطاقات باستخدام KB Ranker (يقرأ من data/identities/)
    مع fallback للـ blueprints لو فشل
    """
    # محاولة استخدام KB Ranker أولاً
    try:
        import core.kb_ranker as kb_ranker
        from pathlib import Path as _KBPath
        
        # ✅ دعم المسارات المطلقة والنسبية (محلي + Docker)
        ROOT = _KBPath(__file__).resolve().parent.parent
        kb_path = ROOT / "data" / "sportsync_knowledge.json"
        identities_dir = ROOT / "data" / "identities"
        
        # استخدام KB Ranker للحصول على identities مباشرة (dicts)
        kb_identities = kb_ranker.rank_and_get_identities(
            answers=answers,
            lang=lang,
            kb_path=kb_path,
            identities_dir=identities_dir,
            top_k=3
        )
        
        if len(kb_identities) >= 3:
            print(f"[REC] Using KB Ranker (identities files) - {len(kb_identities)} cards")
            return kb_identities
        else:
            print(f"[WARN] KB Ranker returned only {len(kb_identities)} cards, falling back to blueprints")
            
    except Exception as e:
        print(f"[WARN] KB Ranker failed: {e}, using fallback blueprints")
    
        if len(cards) >= 3:
            print(f"[REC] Using KB Ranker (identities files) - {len(cards)} cards")
            return cards[:3]
        else:
            print(f"[WARN] KB Ranker returned only {len(cards)} cards, falling back to blueprints")
            
    except Exception as e:
        print(f"[WARN] KB Ranker failed: {e}, using fallback blueprints")
    
    # Fallback: استخدام الكود القديم (blueprints)
    print("[REC] Using fallback blueprints")
    session_id = _session_id_from_answers(answers)
    seed_base = session_id + _stable_json(answers) + datetime.utcnow().strftime("%Y-%m-%d")
    local_rng = rng or random.Random(int(hashlib.sha256(seed_base.encode("utf-8")).hexdigest(), 16))

    identity = identity or _extract_identity(answers)
    drivers = drivers or _drivers(identity, lang)
    traits = traits or _derive_binary_traits(answers)

    blueprint_order = _egate_fallback(identity, traits, local_rng)
    primary_cards = []
    for blueprint in blueprint_order[:3]:
        primary_cards.append(_fallback_identity(blueprint, lang, identity, traits, drivers, local_rng))

    cards = _hard_dedupe_and_fill(primary_cards, blueprint_order, lang, identity, traits, drivers, local_rng)
    return cards


def _format_kb_card(card: Dict[str, Any], lang: str, index: int = 0) -> str:
    """
    تنسيق خاص لبطاقات KB التي تحتوي على سرد قصصي كامل
    يحترم النصوص الطويلة ولا يقصها
    """
    is_ar = lang in ('العربية', 'ar')
    
    # العناوين حسب الترتيب
    headers_ar = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Innovative)"]
    header = (headers_ar if is_ar else headers_en)[min(index, 2)]
    
    # استخراج البيانات
    sport_label = card.get('sport_label', '')
    what = card.get('what_it_looks_like', '')
    why = card.get('why_you', '')
    first_week = card.get('first_week', '')
    progress = card.get('progress_markers', '')
    win = card.get('win_condition', '')
    skills = card.get('core_skills', [])
    mode = card.get('mode', '')
    vr = card.get('variant_vr', '')
    no_vr = card.get('variant_no_vr', '')
    real_examples = card.get('real_world_examples', '')
    psych_hook = card.get('psychological_hook', '')
    
    # بناء البطاقة
    sections = [header, ""]
    
    if sport_label:
        sections.append(f"🎯 {'الرياضة المثالية لك' if is_ar else 'Your Ideal Sport'}: **{sport_label}**")
        sections.append("")
    
    if what:
        sections.append(f"💡 {'ما هي؟' if is_ar else 'What is it?'}")
        sections.append(what)
        sections.append("")
    
    if why:
        sections.append(f"🎮 {'ليه تناسبك؟' if is_ar else 'Why does it fit you?'}")
        sections.append(why)
        sections.append("")
    
    if skills:
        sections.append(f"🧩 {'مهارات أساسية' if is_ar else 'Core Skills'}:")
        for skill in skills[:6]:  # نحد عند 6 مهارات
            sections.append(f"• {skill}")
        sections.append("")
    
    if win:
        sections.append(f"🏁 {'كيف تفوز؟' if is_ar else 'How to win?'}")
        sections.append(win)
        sections.append("")
    
    if first_week:
        sections.append(f"🚀 {'أول أسبوع' if is_ar else 'First Week'}:")
        sections.append(first_week)
        sections.append("")
    
    if progress:
        sections.append(f"✅ {'علامات التقدم' if is_ar else 'Progress Markers'}:")
        sections.append(progress)
        sections.append("")
    
    # ملاحظات إضافية
    notes = []
    if mode:
        notes.append(f"{'وضع اللعب' if is_ar else 'Mode'}: {mode}")
    if no_vr:
        notes.append(f"{'بدون VR' if is_ar else 'Non-VR'}: {no_vr}")
    if vr:
        notes.append(f"VR: {vr}")
    
    if notes:
        sections.append(f"👁️‍🗨️ {'ملاحظات' if is_ar else 'Notes'}:")
        sections.append("\n".join(notes))
        sections.append("")
    
    if real_examples:
        sections.append(f"📍 {'أماكن حقيقية' if is_ar else 'Real Places'}:")
        sections.append(real_examples)
        sections.append("")
    
    if psych_hook:
        hook_title = 'ليش راح تدمن عليها' if is_ar else "Why You'll Get Hooked"
        sections.append(f"🧠 {hook_title}:")
        sections.append(psych_hook)
        sections.append("")
    
    return "\n".join(sections).strip()


def _format_card_strict(card: Dict[str, Any], lang: str) -> str:
    is_ar = lang in ('العربية', 'ar')
    label = card.get('sport_label') or ('هوية متوازنة' if is_ar else 'Balanced Identity')
    label = _mask_names(_scrub_forbidden(label, lang))

    def _clean_lines(value: Any, limit: int = 3) -> List[str]:
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
        else:
            parts = _normalize_sentences(value)
        cleaned: List[str] = []
        for part in parts:
            sanitized = _mask_names(_scrub_forbidden(part, lang))
            if sanitized:
                cleaned.append(sanitized)
            if len(cleaned) == limit:
                break
        return cleaned

    def _join_lines(lines: List[str], *, bullet: bool = False) -> str:
        if not lines:
            return ""
        if bullet:
            return "\n".join(f"- {line}" for line in lines)
        return "\n".join(lines)

    what_lines = _clean_lines(card.get('what_it_looks_like'))
    why_lines = _clean_lines(card.get('why_you'))
    real_lines = _clean_lines(card.get('real_world'))
    notes_lines = _clean_lines(card.get('notes'))

    if is_ar:
        default_personality = 'تميل إلى فضول تحليلي هادئ.'
        default_sport_desc = 'تجربة حركية تتشكل حسب خيالك وتقديرك للتفاصيل.'
        default_why_lines = ['تحتاج لمساحة تحترم ذكاءك العاطفي.', 'تفضّل بناء القرارات بهدوء قبل الاندفاع.']
        default_real_lines = ['ابدأ بخطوات قصيرة تراقب فيها الإشارات الصغيرة.', 'دوّن إحساسك بعد كل تجربة لتضبط المسار.']
        default_ai_lines = ['تحليل سريع من البيانات المتوفرة.']
        headings = {
            'personality': '🧩 **الشخصية الرياضية باختصار:**',
            'sport': '🏅 **الرياضة المثالية لك:**',
            'what': '💡 **ما هي؟**',
            'why': '🎮 **لماذا تناسبك؟**',
            'start': '⚙️ **كيف تبدأ؟**',
            'ai': '🧠 **تفسير الذكاء:**',
        }
    else:
        default_personality = 'You lean toward a calm, analytical curiosity.'
        default_sport_desc = 'A movement space that adapts to your imagination and eye for detail.'
        default_why_lines = ['You need a setting that respects your emotional intelligence.', 'You prefer to layer decisions quietly before moving.']
        default_real_lines = ['Start with short sessions where you watch for subtle cues.', 'Capture how each run feels so you can adjust your flow.']
        default_ai_lines = ['Quick analysis based on the signals you shared.']
        headings = {
            'personality': '🧩 **Sport Personality Snapshot:**',
            'sport': '🏅 **Your Ideal Sport:**',
            'what': '💡 **What Is It?**',
            'why': '🎮 **Why It Fits You?**',
            'start': '⚙️ **How To Begin?**',
            'ai': '🧠 **AI Insight:**',
        }

    personality_summary = '؛ '.join(why_lines[:2]) if is_ar else '; '.join(why_lines[:2])
    if not personality_summary:
        personality_summary = default_personality

    sport_description = ' '.join(what_lines) if what_lines else default_sport_desc

    why_reasoning_lines = why_lines if why_lines else default_why_lines
    why_reasoning = _join_lines(why_reasoning_lines, bullet=True)

    how_lines = real_lines if real_lines else default_real_lines
    how_to_start = _join_lines(how_lines, bullet=True)

    ai_lines = notes_lines if notes_lines else default_ai_lines
    ai_explanation = _join_lines(ai_lines, bullet=len(ai_lines) > 1)

    personality_section = f"{headings['personality']}\n{personality_summary}\n"
    sport_section = f"{headings['sport']} {label}\n{headings['what']} {sport_description}\n"
    why_section = f"{headings['why']}\n{why_reasoning}\n"
    how_section = f"{headings['start']}\n{how_to_start}\n"
    explanation_section = f"{headings['ai']}\n{ai_explanation}\n"

    recommendation_output = (
        personality_section + "\n---\n" +
        sport_section + "\n---\n" +
        why_section + "\n---\n" +
        how_section + "\n---\n" +
        explanation_section
    )

    return recommendation_output.strip()

def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    """Return three recommendation cards formatted with the strict SportSync layout."""
    global LAST_RECOMMENDER_SOURCE

    start_ts = time.time()
    answers_copy: Dict[str, Any] = dict(answers or {})
    force_flag = bool(answers_copy.pop("_force_fallback", False))
    env_force = os.getenv("FORCE_ANALYTICAL_FALLBACK", "").strip().lower() == "true"
    disable_flag = os.getenv("DISABLE_LLM", "").strip().lower() == "true"
    session_id = _session_id_from_answers(answers_copy)

    identity = _extract_identity(answers_copy)
    drivers = _drivers(identity, lang)
    traits = _derive_binary_traits(answers_copy)

    cards_struct: Optional[List[Dict[str, Any]]] = None
    source = "fallback"

    llm_possible = bool(LLM_CLIENT and CHAT_MODEL)
    llm_attempted = False

    if not disable_flag and not force_flag and not env_force and llm_possible:
        print(f"[REC] llm_path=ON model={CHAT_MODEL} fb={CHAT_MODEL_FALLBACK or 'none'}")
        try:
            cards_struct = _llm_cards(answers_copy, identity, drivers, lang, traits)
        except Exception as e:
            print(f"[REC] ❌ LLM failed: {e}")
            cards_struct = None
        llm_attempted = True
        if cards_struct:
            source = "llm"
            print(f"[REC] ✅ LLM generated {len(cards_struct)} cards")
        else:
            print("[REC] ⚠️ LLM returned None, falling back to KB/Hybrid")
    else:
        print(f"[REC] llm_path=OFF - disable:{disable_flag} force:{force_flag} env:{env_force} possible:{llm_possible}")

    if not cards_struct:
        cards_struct = _generate_cards(
            answers_copy,
            lang,
            identity=identity,
            drivers=drivers,
            traits=traits,
        )
        source = "fallback"

    # اختيار الـ formatter المناسب حسب المصدر
    # KB cards تحتوي على 'psychological_hook' بينما blueprint cards لا تحتوي عليها
    is_kb_card = any(card.get('psychological_hook') or card.get('real_world_examples') for card in cards_struct)
    
    if is_kb_card:
        # استخدام formatter خاص بـ KB الذي يحترم السرد القصصي
        formatted_cards = [_format_kb_card(card, lang, i) for i, card in enumerate(cards_struct)]
        if source == "fallback":
            source = "kb"  # تصحيح المصدر
    else:
        # استخدام formatter التقليدي للـ blueprints
        formatted_cards = [_format_card_strict(card, lang) for card in cards_struct]

    LAST_RECOMMENDER_SOURCE = source

    models_info = {
        "chat_model": CHAT_MODEL,
        "chat_model_fallback": CHAT_MODEL_FALLBACK,
        "source": source,
        "llm_attempted": llm_attempted,
        "llm_possible": llm_possible,
    }

    try:
        log_event(
            user_id=str(answers_copy.get("_user_id", "unknown")),
            session_id=session_id,
            name="generate_recommendation",
            payload=models_info,
            lang=lang,
        )
    except Exception:
        pass

    snapshot = {
        "answers": answers_copy,
        "z_signals": {
            "identity": identity,
            "drivers": drivers,
            "traits": traits,
        },
        "final_cards": cards_struct,
        "models": models_info,
        "timings": {
            "elapsed_s": round(time.time() - start_ts, 3),
            "generated_at": datetime.utcnow().isoformat(),
        },
    }

    try:
        log_recommendation_result(session_id, snapshot)
    except Exception:
        pass

    return formatted_cards


def get_last_rec_source() -> str:
    return LAST_RECOMMENDER_SOURCE


if __name__ == "__main__":
    sample_answers = {"q1": {"answer": ["أحب الذكاء والتخطيط"]}, "_session_id": "demo-session"}
    recs = generate_sport_recommendation(sample_answers, "العربية")
    assert len(recs) == 3
    assert all(card.startswith('🧩') and card.count('\n---\n') == 4 for card in recs)
    print("OK")
