# -- coding: utf-8 --
from __future__ import annotations

import os
import random
from typing import Any, Dict, List

try:
    from core.llm_client import make_llm_client, pick_models, chat_once
except Exception:  # pragma: no cover - client not available
    make_llm_client = None
    pick_models = None
    chat_once = None


def _extract_identity(answers: Dict[str, Any], lang: str) -> Dict[str, float]:
    text = (str(answers) or "").lower()
    weights = {
        "tactical": 0.55 if any(k in text for k in ("strategy", "استراتيجية", "تكتي", "ذكاء")) else 0.45,
        "sensory": 0.55 if any(k in text for k in ("هدوء", "سكون", "breath", "تنفس", "حواس")) else 0.45,
        "adventure": 0.55 if any(k in text for k in ("مغام", "explore", "اكتشاف", "طبيعة")) else 0.45,
        "achievement": 0.55 if any(k in text for k in ("تحدي", "تفوق", "win", "انجاز")) else 0.45,
        "social": 0.55 if any(k in text for k in ("فريق", "جماعي", "group", "friends")) else 0.45,
        "solo": 0.55 if any(k in text for k in ("فردي", "alone", "عزل")) else 0.45,
        "indoor": 0.55 if any(k in text for k in ("داخل", "indoor", "صالة")) else 0.45,
        "outdoor": 0.55 if any(k in text for k in ("هواء", "outdoor", "خارجي", "طبيعة")) else 0.45,
    }
    return {k: round(v, 3) for k, v in weights.items()}


_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "tactical_immersive": {
        "title": {"ar": "Tactical Immersive Combat", "en": "Tactical Immersive Combat"},
        "why": {
            "ar": "هذا المسار ينسج مواجهة ذهنية وجسدية متواصلة، حيث يعمل الفضول التحليلي لديك مع شغف الإنجاز الهادئ في خلفية المشهد.",
            "en": "This path weaves a constant mental-and-body duel, letting your analytical curiosity dance with a quiet hunger for achievement.",
        },
        "what": {
            "ar": "تدخل عالمًا يشبه رواية تشويق: ساحات تتبدل، زوايا تُفتح، وحواس تلتقط إشارات متقنة قبل أن تتحول إلى حركة رشيقة." \
                   " تتسع التجربة لتشمل محاكاة واقع افتراضي، مبارزات سيف، أو حتى جلسات تحاكي مطاردة تكتيكية في فضاءات مغلقة، وكلها مصممة لخدمة شغفك بالتفكير الحاد.",
            "en": "You step into a thriller-like world: shifting arenas, opening angles, and senses capturing fine cues before they turn into agile motion." \
                   " The experience stretches from immersive VR simulations to sabre duels or chase scenarios inside curated spaces, all crafted to serve your love for sharp thinking.",
        },
        "shape": {
            "ar": "في التطبيق الواقعي ستشعر بارتفاع التركيز دون الحاجة لضوضاء صالات تقليدية؛ شبكة ضوء خافت، مدرب يهمس بالتوجيهات، ومسارات قصيرة تقيس مدى براعتك في اتخاذ القرار." \
                     " يتحول كل تمرين إلى لوحة قصصية تعيشها من الداخل." ,
            "en": "In practice you feel focus rising without the buzz of traditional gyms; soft lighting, a coach offering low whispers, and short arcs that measure your decision craft." \
                   " Every drill becomes a narrative scene you inhabit from the inside.",
        },
        "notes": {
            "ar": "دع إحساس السيطرة يقودك: اختر خصمًا أو سيناريو يوقظ ذكاءك، ثم بدّل الإيقاع عندما تلمح الفكرة التالية. الهوية هنا أسبق من النتائج." \
                     " إذا شعرت أن الصراع صار خانقًا، أعد هندسة المهمة وامنح نفسك دورًا مختلفًا دون أي تعليمات جامدة.",
            "en": "Let the feeling of control guide you: pick an opponent or scenario that wakes your intellect, then shift pace when the next idea flashes." \
                   " If the duel feels tight, redesign the mission and give yourself a different role—no rigid instructions needed.",
        },
    },
    "stealth_flow": {
        "title": {"ar": "Stealth-Flow Missions", "en": "Stealth-Flow Missions"},
        "why": {
            "ar": "هويتك تهوى السكون الممزوج بالترقب؛ تحب سماع نبضك الداخلي وهو يتزامن مع حركة لينة تتيح لك التقدم من دون إثارة أي ضجيج بصري أو اجتماعي.",
            "en": "Your identity delights in calm blended with anticipation; you enjoy hearing your inner pulse sync with gentle movement that lets you advance without visual or social noise.",
        },
        "what": {
            "ar": "هذه المهمات تنقلك إلى ممرات مظللة، غرف استوديو مهيأة خصيصًا، أو بيئات VR تتلاعب بالضوء والصوت لتمنحك حسًا سينمائيًا." \
                   " تستكشف التوازن، التمدد، والانسياب المخملي الذي يجعل كل خطوة وكأنها حوار سري بينك وبين العالم." ,
            "en": "These missions move you through shaded corridors, curated studio rooms, or VR worlds that play with light and audio to give a cinematic feel." \
                   " You explore balance, reach, and velvet-like flow that turns each step into a private dialogue between you and the world.",
        },
        "shape": {
            "ar": "في الواقع قد تبدأ بجلسات صغيرة تركز على الاستشعار، ثم تتدرج نحو مسارات أكثر تعقيدًا تدمج التتبع البصري، الخطو الخفيف، والانعطافات المحسوبة." \
                     " لا توجد صفارات أو تعليمات حادة؛ فقط عقل يهدأ كلما اكتشف تفاصيل جديدة." ,
            "en": "In practice you might open with sensory decks, then progress to layered paths combining visual tracking, light footwork, and measured pivots." \
                   " No whistles or sharp orders—only a mind that softens as it notices new detail.",
        },
        "notes": {
            "ar": "إذا لاحظت أن الانسياب صار آليًا، أطفئ الإضاءة، بدّل الخلفية الصوتية، أو أضف عنصرًا يحفز الفضول من جديد." \
                     " المهم أن يبقى المشهد مساحة تلوّنها بحدسك دون الالتزام بأي قوالب جامدة." ,
            "en": "When the flow starts feeling automatic, dim the light, change the soundscape, or add an element that rekindles curiosity." \
                   " The key is keeping the scene as a canvas you colour with instinct, free from rigid molds.",
        },
    },
    "urban_exploration": {
        "title": {"ar": "Urban Exploration Athletics", "en": "Urban Exploration Athletics"},
        "why": {
            "ar": "روحك تميل للمغامرة الحرة، تبحث عن زوايا المدينة التي لم تُكتشف، وتستمتع حين يتحول الطريق اليومي إلى مساحة سرد جديدة." ,
            "en": "Your spirit leans toward open adventure, hunting for undiscovered urban corners and turning a daily path into a narrative playground.",
        },
        "what": {
            "ar": "التجربة تمتد من الباركور المخطط على أسطح وأزقة آمنة إلى جولات جيوكاشينغ حركية تربط الجسد بالخرائط." \
                   " كل محطة تضيف طبقة قصة: قفزة صغيرة فوق سور قديم، توازن على حافة، أو انعطافة مخفية لا يعرفها سوى القلائل." ,
            "en": "The experience ranges from choreographed parkour across safe rooftops and alleys to kinetic geocaching adventures that bind body with maps." \
                   " Each stop adds a story layer: a small leap over an old wall, a balance walk on a ledge, or a hidden turn known by only a few.",
        },
        "shape": {
            "ar": "تمزج الجلسات بين التنقل العمودي والأفقي، استخدام معالم المدينة كأدوات، والتفاعل مع الضوء الطبيعي المتغير." \
                     " تتحول المدينة إلى صديق، ويصير كل ممر اختبارًا لفضولك." ,
            "en": "Sessions blend vertical and horizontal travel, using city landmarks as tools and playing with ever-changing natural light." \
                   " The city becomes your companion, each passage a test of curiosity.",
        },
        "notes": {
            "ar": "اختر رفيقًا يتقبل التجربة الإبداعية أو انطلق منفردًا مع كاميرا توثق التفاصيل التي تلمع." \
                     " استمع للحدس؛ إذا شعرت أن المسار يكرر نفسه فابحث عن حي جديد أو زاوية مختلفة." ,
            "en": "Bring a partner who embraces creative exploration or roam solo with a camera that captures bright details." \
                   " Listen to instinct; when the route repeats, scout a new district or angle.",
        },
    },
    "precision_duel": {
        "title": {"ar": "Precision Duel Sports", "en": "Precision Duel Sports"},
        "why": {
            "ar": "تحب المواجهة الهادئة التي تكافئ الصبر والدقة، وتمنحك نشوة تفوق تحافظ فيه على أناقتك الذهنية." ,
            "en": "You savour measured contests that reward patience and precision, delivering a subtle rush while keeping mental poise.",
        },
        "what": {
            "ar": "من المبارزة بالسيف إلى الرماية بالقوس، كل مشهد يركز على حركة محسوبة يتبعها إحساس بالانتصار الداخلي." \
                   " الهدوء الذي يسبق اللمسة النهائية أهم من نتيجة اللوحة." ,
            "en": "From sabre fencing to recurve archery, each scene focuses on deliberate motion followed by an inner sense of triumph." \
                   " The calm before the finishing touch matters more than the scoreboard.",
        },
        "shape": {
            "ar": "تجد نفسك في مساحات أنيقة، إضاءة متوازنة، وتعليمات خفيفة تساعدك على ضبط التنفس والحفاظ على صفاء التفكير." \
                     " كل جولة تشبه مقطع موسيقي تعزفه أنت وحدك." ,
            "en": "You’re in refined arenas with balanced lighting and gentle coaching helping you steady breath and keep thoughts clear." \
                   " Every round feels like a musical piece performed solo.",
        },
        "notes": {
            "ar": "ركّز على الطقوس الصغيرة: ترتيب العتاد، لمس الأرض بأطراف أصابعك، وتخيل مسارك قبل البدء." \
                     " إن بدا الإيقاع جامدًا، جرّب أسلوبًا آخر أو خصمًا بطابع مختلف." ,
            "en": "Lean into small rituals: aligning gear, grounding fingertips, envisioning the path before you start." \
                   " If the rhythm stiffens, switch style or pick an opponent with a different aura.",
        },
    },
    "creative_teamplay": {
        "title": {"ar": "Creative Teamplay", "en": "Creative Teamplay"},
        "why": {
            "ar": "تلتقط شرارة المجموعة بسرعة، وتستمتع عندما تتحول المباراة إلى ورشة أفكار وحوار حركي." ,
            "en": "You absorb team sparks instantly and relish when a match turns into a workshop of ideas and kinetic dialogue.",
        },
        "what": {
            "ar": "تشمل التجربة فوتسال تكتيكي، كرة سلة نصف ملعب، أو ألعابًا تعاونية تعتمد على إشارات سريعة وخطط مفاجئة." \
                   " كل مشاركة تفتح بابًا للتعبير والضحك المشترك." ,
            "en": "Experiences include tactical futsal, half-court basketball, or cooperative games relying on quick cues and inventive twists." \
                   " Every play opens room for expression and shared laughter.",
        },
        "shape": {
            "ar": "يمتزج التواصل اللفظي والتمرير السريع مع حركات مرتجلة تجعل المجموعة تشبه فرقة فنية. أحيانًا تنقسمون إلى ثنائيات صغيرة تبتكر مسارات قصيرة، وأحيانًا تتجمعون كحلقة واحدة تلتقط الفكرة ثم تعيد تشكيلها براحة. تتغير الإضاءة والموسيقى والملعب المصغر بحسب المزاج، فيبقى الإيقاع نابضًا دون الحاجة لأي أوامر جامدة." ,
            "en": "Verbal cues and swift passes blend with improvised movement, turning the crew into an art collective. Sometimes you split into tiny duos to create short patterns, and other times you gather as one circle that catches an idea then reshapes it gently. Lighting, music, and even micro-court layouts shift with the mood, keeping the pulse vibrant without rigid commands.",
        },
        "notes": {
            "ar": "اختر شريكات وشركاء يحتفون بالابتكار ولا يطاردون النقاط المجردة." \
                     " غيّر مكان اللعب كل فترة لتحافظ على دهشة التجربة." ,
            "en": "Invite teammates who celebrate creativity instead of chasing plain scores." \
                   "Rotate venues frequently to keep the experience surprising.",
        },
    },
}

_TRAIT_LINES = {
    "ar": {
        "tactical": "تفكيرك التحليلي يقرأ اللقطات قبل حدوثها وينتظر اللحظة التي يلتمع فيها الحدس.",
        "sensory": "جسدك يلين عندما تراقب همسة الضوء وتستمع إلى أنفاسك وكأنها نوتة موسيقية.",
        "adventure": "تحب أن تحوّل الطريق العادي إلى مسرح اكتشاف جديد في كل مرة.",
        "achievement": "تشعر بالرضا حين ترى أثر توقيعك على النتيجة دون ضجيج أو مبالغة.",
        "social": "الطاقة الجماعية تشحنك وتمنحك إحساسًا بأن الفريق قصيدة تتغير كل لحظة.",
        "solo": "الهدوء المنعزل يمنحك الفرصة لصقل مهاراتك وكأنك تنحت منحوتة شخصية.",
        "indoor": "تحب الأماكن التي يمكن تشكيلها لتناسب مزاجك دون مقاطعات مفاجئة.",
        "outdoor": "الأفق المفتوح يشعل الخيال ويمنحك إحساسًا بالانطلاق الحر.",
    },
    "en": {
        "tactical": "Your analytic lens reads the scene ahead and waits for intuition to flash.",
        "sensory": "Your body softens when you watch subtle light and hear your breath like a melody.",
        "adventure": "You enjoy turning an ordinary route into a fresh discovery stage every time.",
        "achievement": "Satisfaction arrives when your imprint appears on the outcome without noise or fuss.",
        "social": "Collective energy fuels you and makes the crew feel like a poem shifting every heartbeat.",
        "solo": "Quiet solitude lets you sculpt skills as if crafting a personal statue.",
        "indoor": "You appreciate spaces that can be shaped to your mood without surprise intrusions.",
        "outdoor": "An open horizon sparks imagination and gifts you with freer motion.",
    },
}


def _summarise_traits(identity: Dict[str, float], lang: str) -> List[str]:
    mapping = _TRAIT_LINES["ar" if lang in ("العربية", "ar") else "en"]
    lines: List[str] = []
    for trait, _value in sorted(identity.items(), key=lambda item: item[1], reverse=True):
        if trait in mapping and mapping[trait] not in lines:
            lines.append(mapping[trait])
        if len(lines) >= 2:
            break
    return lines or (["هويتك تتطور مع كل تجربة جديدة." ] if lang.startswith("ar") else ["Your identity grows with every new exploration."])


def _select_archetype_keys(identity: Dict[str, float]) -> List[str]:
    order: List[str] = []
    if identity["tactical"] >= identity["sensory"]:
        order.append("tactical_immersive")
        order.append("stealth_flow")
    else:
        order.append("stealth_flow")
        order.append("tactical_immersive")

    adventure_score = identity["adventure"]
    social_score = identity["social"]
    solo_score = identity["solo"]
    tactical_score = identity["tactical"]

    if adventure_score >= max(social_score, tactical_score):
        third = "urban_exploration"
    elif social_score >= solo_score:
        third = "creative_teamplay"
    else:
        third = "precision_duel"

    if third not in order:
        order.append(third)
    else:
        for fallback in ("urban_exploration", "precision_duel", "creative_teamplay"):
            if fallback not in order:
                order.append(fallback)
                break
    return order[:3]


def _build_card_text(archetype_key: str, identity: Dict[str, float], lang: str) -> str:
    data = _ARCHETYPES[archetype_key]
    locale = "ar" if lang in ("العربية", "ar") else "en"
    title = data["title"][locale]
    trait_lines = _summarise_traits(identity, lang)

    sections = [
        f"🎯 **{title}**",
        "",
        "💡 **ما هي؟**" if locale == "ar" else "💡 **What is it?**",
        data["what"][locale],
        "",
        "🎮 **ليه تناسبك؟**" if locale == "ar" else "🎮 **Why it fits you**",
        data["why"][locale] + " " + " ".join(trait_lines),
        "",
        "🔍 **شكلها الواقعي**" if locale == "ar" else "🔍 **How it feels in real life**",
        data["shape"][locale],
        "",
        "👁️‍🗨️ **ملاحظات مهمة**" if locale == "ar" else "👁️‍🗨️ **Important notes**",
        data["notes"][locale],
    ]

    text = "\n".join(sections)
    if len(text.split()) < 150:
        padding_sentence = "استمر في الإصغاء لهويتك الداخلية ودعها تقودك لاختيار التفاصيل التي تضيفها." if locale == "ar" else "Keep listening to your inner identity and let it guide the details you add."  # ensure minimum length
        sections.insert(-1, padding_sentence)
        text = "\n".join(sections)
    return text


def _fallback_cards(answers: Dict[str, Any], lang: str, n: int = 3) -> List[str]:
    identity = _extract_identity(answers, lang)
    keys = _select_archetype_keys(identity)
    cards = [_build_card_text(key, identity, lang) for key in keys]
    return cards[:n]


def _llm_available() -> bool:
    if not (make_llm_client and pick_models and chat_once):
        return False
    if os.getenv("DISABLE_LLM", "").strip().lower() == "true":
        return False
    return True


def _llm_polish(cards: List[str], lang: str) -> List[str]:
    if not _llm_available():
        return cards

    client = make_llm_client()
    if not client:
        return cards

    try:
        main_model, fallback_model = pick_models()
    except Exception:  # pragma: no cover - pick failure
        main_model, fallback_model = ("gpt-4o", "gpt-4o-mini")

    system_prompt = (
        "أعد صياغة بطاقة الهوية الرياضية التالية بأسلوب إنساني غني يركز على المتعة والانغماس." \
        " لا تضف أزمنة أو خطط أو قياسات أو كلمات عن السعرات أو الوزن. حافظ على نفس العناوين، وأعد النص في صورة Markdown فقط."
    ) if lang in ("العربية", "ar") else (
        "Rewrite the following sport identity card with a rich human tone that celebrates enjoyment and immersion." \
        " Do not add times, schedules, measurements, or words about calories or weight. Keep the headings and return Markdown only."
    )

    polished: List[str] = []
    for card in cards:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": card},
        ]
        try:
            response = chat_once(client, messages, model=main_model, temperature=0.5, max_tokens=900)
            if response and len(response.split()) >= 150:
                polished.append(response)
            elif fallback_model:
                response_fb = chat_once(client, messages, model=fallback_model, temperature=0.4, max_tokens=900)
                polished.append(response_fb if response_fb and len(response_fb.split()) >= 150 else card)
            else:
                polished.append(card)
        except Exception:
            polished.append(card)
    return polished


def generate_sport_recommendation(answers: Dict[str, Any], lang: str = "العربية") -> List[str]:
    fallback_cards = _fallback_cards(answers, lang, n=3)
    return _llm_polish(fallback_cards, lang)


def quick_diagnose() -> Dict[str, Any]:
    sample = {"intent": {"answer": ["تجربة تكتيكية هادئة مع مغامرة" ]}}
    identity = _extract_identity(sample, "العربية")
    selected = _select_archetype_keys(identity)
    return {
        "llm_available": _llm_available(),
        "identity_weights": identity,
        "selected_archetypes": selected,
    }
