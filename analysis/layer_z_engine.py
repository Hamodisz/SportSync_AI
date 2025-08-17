# analysis/layer_z_engine.py
# ------------------------------------------------------------
# Layer Z (Silent Engine) – أقوى طبقة تحليل للمحركات الصامتة
# يقرأ إجابات المستخدم (عربي/إنجليزي)، يستخرج الدوافع العميقة،
# يقيّم الأوزان والثقة، يكتشف التناقضات، ويولّد سردية وهوية رياضية.
# ------------------------------------------------------------

from _future_ import annotations
from typing import Any, Dict, List, Tuple
import re
import math

# ========= Utilities =========

_ARABIC_TRUE = {"نعم", "اي", "ايه", "اوافق", "أوافق", "تمام", "احس", "أحس", "احب", "أحب"}
_ARABIC_FALSE = {"لا", "مو", "مش", "ما", "ارفض", "أرفض", "ما أحب", "مااحس"}

def _to_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (list, tuple, set)):
        return " | ".join(map(str, x))
    if isinstance(x, dict):
        # حاول نقرأ answer/question إن وجدت
        a = x.get("answer")
        q = x.get("question")
        if a is not None:
            return _to_text(a)
        return f"{q} :: {list(x.values())}"
    return str(x)

def _norm(s: str) -> str:
    s = _to_text(s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ","ا")
    s = s.replace("ة","ه").replace("ى","ي").replace("ؤ","و").replace("ئ","ي")
    return s.lower().strip()

def _has_any(s: str, kws: List[str]) -> bool:
    s = _norm(s)
    return any(kw in s for kw in kws)

def _score_add(bucket: Dict[str, float], k: str, w: float):
    bucket[k] = bucket.get(k, 0.0) + w

def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))

def _conf_from_evidence(weights: Dict[str, float]) -> float:
    # ثقة تقريبية = دالة لوجستية على مجموع الأوزان المطلقة
    total = sum(abs(v) for v in weights.values())
    return _clip01(1 / (1 + math.exp(-0.9 * (total - 2.0))))  # يزيد مع شدة الدلائل

# ========= Core Extraction =========

def _extract_signals(answers: Dict[str, Any]) -> Dict[str, str]:
    """
    نبسّط مدخلات الأسئلة إلى قاموس نصوص قابلة للبحث.
    يدعم شكل: {Q1: "..."} أو {Q1: {"question":..., "answer":...}} أو قوائم.
    """
    signals = {}
    for k, v in (answers or {}).items():
        key = str(k)
        signals[key] = _norm(v)
    return signals

# ========= Driver Rules =========

def _apply_driver_rules(sig: Dict[str, str]) -> Dict[str, float]:
    """
    يوزّع أوزان على المحركات الصامتة. كل وزن ∈ [-1..+1].
    """
    w: Dict[str, float] = {}

    s1 = sig.get("Q1","")  # ما يذيب الوعي (flow)
    if _has_any(s1, ["time", "forget", "deep", "flow", "تركيز", "انسى", "يمر الوقت", "غمر", "اندماج"]):
        _score_add(w, "flow_depth", 0.8)
    if _has_any(s1, ["اصوات", "طبيعه", "هواء", "شمس", "خارج", "outdoor"]):
        _score_add(w, "nature_pull", 0.5)
    if _has_any(s1, ["منافس", "فريق", "اصدقاء", "social", "team"]):
        _score_add(w, "social_charge", 0.6)
    if _has_any(s1, ["وحدي", "alone", "solo", "انعزال", "هدوء"]):
        _score_add(w, "solo_focus", 0.6)

    s2 = sig.get("Q2","")  # لحظة القوة بلا تصفيق
    if _has_any(s2, ["تحدي", "challenge", "اكسر", "حدودي", "limits"]):
        _score_add(w, "limit_break", 0.9)
    if _has_any(s2, ["اتقان", "mastery", "ضبط", "تحكم", "control", "precision"]):
        _score_add(w, "skill_mastery", 0.8)
    if _has_any(s2, ["جمال", "تناغم", "rhythm", "جسد", "سلاسه", "grace"]):
        _score_add(w, "aesthetic_motion", 0.6)

    s3 = sig.get("Q3","")  # أول ما تلمسه في بيئة غنية
    if _has_any(s3, ["جدار", "تسلق", "climb", "عائق", "park", "bar", "حرك"]):
        _score_add(w, "impulse_move", 0.7)
    if _has_any(s3, ["كره", "ball", "اداه", "equipment", "ادوات"]):
        _score_add(w, "object_curiosity", 0.6)
    if _has_any(s3, ["استكشف", "observe", "اشوف", "اناظر"]):
        _score_add(w, "scanner_mind", 0.4)

    s4 = sig.get("Q4","")  # تفهم قبل التجربة أم العكس؟
    if _has_any(s4, ["اجرب ثم افهم", "try then understand", "اجرب وبعدين"]):
        _score_add(w, "kinesthetic_learning", 0.7)
    if _has_any(s4, ["افهم قبل", "read", "افهم ثم", "planning", "خطه"]):
        _score_add(w, "cognitive_planning", 0.6)

    s5 = sig.get("Q5","")  # ما الذي يجعلك تترك؟
    if _has_any(s5, ["ملل", "routine", "bored", "تكرار"]):
        _score_add(w, "novelty_need", 0.8)
    if _has_any(s5, ["اصابه", "وجع", "الم", "injury", "pain"]):
        _score_add(w, "pain_avoidance", 0.7)
    if _has_any(s5, ["وقت", "time", "ازدحام", "مسافه", "تكلفه"]):
        _score_add(w, "friction_sensitivity", 0.6)

    s6 = sig.get("Q6","")  # متعة خاصة لا أحد يدري
    if _has_any(s6, ["سري", "secret", "لحالي", "بدون احد", "no one knows"]):
        _score_add(w, "private_pride", 0.7)
    if _has_any(s6, ["اصنع", "ابني", "create", "ابتكار", "نمزج"]):
        _score_add(w, "maker_drive", 0.7)
    if _has_any(s6, ["انجاز", "accomplish", "اكمل", "finish"]):
        _score_add(w, "closure_reward", 0.5)

    # إشارات إضافية إن وُجدت
    profile_all = " ".join(sig.values())
    if _has_any(profile_all, ["بحر", "ماء", "موج", "sea", "ocean", "water"]):
        _score_add(w, "water_pull", 0.5)
    if _has_any(profile_all, ["ارتفاع", "هايت", "قمه", "peak", "height", "fear"]):
        _score_add(w, "height_arousal", 0.4)

    return w

# ========= Contradictions & Archetypes =========

_ARCHETYPES = [
    ("Flow-Seeker",            ["flow_depth", "solo_focus"],            ["social_charge"]),
    ("Precision Artisan",      ["skill_mastery", "cognitive_planning"], ["novelty_need"]),
    ("Edge-Pusher",            ["limit_break", "impulse_move"],         ["pain_avoidance"]),
    ("Rhythmic Naturalist",    ["nature_pull", "kinesthetic_learning"], ["friction_sensitivity"]),
    ("Social Catalyst",        ["social_charge", "object_curiosity"],   ["solo_focus"]),
    ("Maker-Explorer",         ["maker_drive", "novelty_need"],         []),
]

def _pick_archetype(weights: Dict[str, float]) -> Tuple[str, float]:
    best_name = "Undetermined"
    best_score = -1.0
    for name, plus, minus in _ARCHETYPES:
        s = sum(weights.get(p, 0) for p in plus) - 0.5 * sum(weights.get(m, 0) for m in minus)
        if s > best_score:
            best_score, best_name = s, name
    # تحويله لنسبة 0..1 تقريبية
    return best_name, _clip01(0.5 + best_score / 4.0)

def _detect_conflicts(weights: Dict[str, float]) -> List[str]:
    flags = []
    if weights.get("novelty_need", 0) > 0.7 and weights.get("skill_mastery", 0) > 0.7:
        flags.append("تريد تجديدًا مستمرًا لكنك في نفس الوقت تطلب مسار إتقان طويل.")
    if weights.get("social_charge", 0) > 0.7 and weights.get("solo_focus", 0) > 0.7:
        flags.append("تتغذى اجتماعيًا وتتماهى مع العزلة؛ نحتاج بيئة هجينة.")
    if weights.get("limit_break", 0) > 0.7 and weights.get("pain_avoidance", 0) > 0.7:
        flags.append("تحب دفع الحدود لكنك حساس للألم/الإصابة؛ يلزم تصعيد آمن محسوب.")
    return flags

# ========= Narrative =========

def _build_narrative(weights: Dict[str, float], arche: str, lang: str) -> str:
    def yes(k): return weights.get(k, 0) > 0.55

    if lang == "العربية":
        lines = []
        if yes("flow_depth"):      lines.append("تنجذب لإيقاع يذيب وعيك ويعيد ترتيب ذهنك.")
        if yes("nature_pull"):     lines.append("الطبيعة والهواء الطلق يفتحان صدرك ويضبطان مزاجك.")
        if yes("social_charge"):   lines.append("تشتعل بوجود الآخرين وتتغذى على التفاعل.")
        if yes("solo_focus"):      lines.append("تعشق الصمت والتركيز الفردي عندما يكون الهدف واضحًا.")
        if yes("limit_break"):     lines.append("هناك لذّة خاصة في اختبار الحدود وصنع قفزة صغيرة يوميًا.")
        if yes("skill_mastery"):   lines.append("تحترم الإتقان والضبط الدقيق للحركة.")
        if yes("impulse_move"):    lines.append("جسدك يبدأ بالتحرك بمجرد رؤية مساحة قابلة للتحدي.")
        if yes("object_curiosity"):lines.append("تثيرك الأدوات والأغراض كأنها مفاتيح لأبواب جديدة.")
        if yes("kinesthetic_learning"): lines.append("تتعلم بجسدك أولًا ثم تصوغ الفهم بالكلمات.")
        if yes("cognitive_planning"):   lines.append("تحب إطارًا ذكيًا يسبق الفعل ويقيس التقدم.")
        if yes("novelty_need"):    lines.append("الرتابة عدوّة لك؛ تحتاج تجديدًا محسوبًا.")
        if yes("private_pride"):   lines.append("تقدّر المتعة الخاصة بعيدًا عن أعين الناس.")
        if yes("maker_drive"):     lines.append("عندك نزعة صانع: تمزج وتبتكر وتعيد تشكيل التجربة.")
        if yes("water_pull"):      lines.append("عنصر الماء يهدئ جهازك العصبي ويخلق تدفقًا سلسًا.")
        if yes("height_arousal"):  lines.append("الارتفاعات تمنحك يقظة عميقة إذا ضُبط الأمان.")
        if not lines:
            lines.append("تميل إلى تجربة تعيدك لذاتك بتركيز هادئ ومسار تقدّم محسوس.")
        lines.append(f"\n🧬 نمط الهوية المكتشف: *{arche}*")
        return " ".join(lines)
    else:
        lines = []
        if yes("flow_depth"):      lines.append("You crave rhythms that dissolve awareness and reset the mind.")
        if yes("nature_pull"):     lines.append("Nature/air open your chest and tune mood.")
        if yes("social_charge"):   lines.append("You ignite around others and feed on interaction.")
        if yes("solo_focus"):      lines.append("You love quiet solo focus when the target is clear.")
        if yes("limit_break"):     lines.append("Pushing limits brings a special reward.")
        if yes("skill_mastery"):   lines.append("You respect precise control and craftsmanship.")
        if yes("impulse_move"):    lines.append("Your body starts moving when a challengeable space appears.")
        if yes("object_curiosity"):lines.append("Objects/tools intrigue you as keys to new doors.")
        if yes("kinesthetic_learning"): lines.append("You learn through the body first, then verbalize.")
        if yes("cognitive_planning"):   lines.append("You like a smart frame that precedes action and measures progress.")
        if yes("novelty_need"):    lines.append("Routine drains you; you need structured novelty.")
        if yes("private_pride"):   lines.append("You value private pride away from eyes.")
        if yes("maker_drive"):     lines.append("You’re a maker: blending, inventing, reshaping experience.")
        if yes("water_pull"):      lines.append("Water calms your nervous system and smooths flow.")
        if yes("height_arousal"):  lines.append("Heights sharpen your alertness when safety is tuned.")
        if not lines:
            lines.append("You lean toward experiences that return you to yourself with calm focus and tangible progress.")
        lines.append(f"\n🧬 Identity Archetype: *{arche}*")
        return " ".join(lines)

# ========= Public API =========

def analyze_silent_drivers_combined(user_data: Dict[str, Any], questions: Dict[str, Any] = None, lang: str = "العربية") -> Dict[str, Any]:
    """
    تحليل Layer Z النهائي.
    المدخل:
        - user_data: قد يحتوي answers أو full_text
        - questions: بديل مباشر لـ answers إن تم تمريره
        - lang: 'العربية' أو 'English'
    الخرج:
        {
          "weights": {driver: weight},
          "drivers_sorted": [(driver, weight), ...],
          "archetype": {"name": str, "confidence": 0..1},
          "conflicts": [str],
          "narrative": str,
          "top_drivers": [str],
          "confidence": 0..1
        }
    """
    answers = (questions or user_data.get("answers") or {})
    signals = _extract_signals(answers)
    weights = _apply_driver_rules(signals)

    # ثقة كلية
    confidence = _conf_from_evidence(weights)

    # التناقضات + الأركتايب
    arche_name, arche_conf = _pick_archetype(weights)
    conflicts = _detect_conflicts(weights)

    # ترتيب السائقين
    drivers_sorted = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    top_drivers = [k for k, v in drivers_sorted if v > 0.55][:4]

    # سردية
    narrative = _build_narrative(weights, arche_name, lang)

    return {
        "weights": weights,
        "drivers_sorted": drivers_sorted,
        "archetype": {"name": arche_name, "confidence": arche_conf},
        "conflicts": conflicts,
        "narrative": narrative,
        "top_drivers": top_drivers,
        "confidence": confidence
    }

# ================= Integration Notes =================
# - يوصى بتمرير مخرجات هذه الدالة إلى backend لتوليد توصيات بلا أسماء.
# - استخدم 'top_drivers' و 'narrative' مباشرة داخل البرومبت.
# - إن أردت طبقة إضافية: اجعل الواجهة تعرض conflicts كتنبيهات دقيقة.
