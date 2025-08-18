# -- coding: utf-8 --
"""
core/answers_encoder.py
-----------------------
طبقة ترميز تحول إجابات نموذج الأسئلة إلى بروفايل منظّم يُسهّل على الذكاء
اختيار التوصيات. لا تعتمد على شكل أسئلة ثابت 100% — تعمل باللغتين وعبر
مطابقة كلمات مفتاحية + قواعد بسيطة.

الاستخدام السريع:
    from core.answers_encoder import encode_answers
    profile = encode_answers(answers, lang="العربية")
    # ضعه مع الإجابات ليمر إلى الباكند:
    answers["_profile_"] = profile
"""

from _future_ import annotations
import re
from typing import Dict, List, Any, Tuple

# كلمات مفتاحية → تصنيفات (عربي/إنجليزي)
KEYWORDS: Dict[str, List[str]] = {
    "adrenaline": [
        "خطر","مخاطرة","اندفاع","سرعة","قتال","قتالي","اشتباك","قفز","طيران","باركور",
        "adrenaline","risk","danger","fast","speed","combat","fight","mma","parkour","extreme"
    ],
    "tactical": [
        "تكتيك","تخطيط","خطة","كمين","تحليل","استراتيجية",
        "tactic","tactical","strategy","strategic","analyze","plan"
    ],
    "mindful": [
        "هدوء","تنفس","تأمل","انتباه","وعي","صفاء","استرخاء",
        "calm","breath","breathing","meditation","mindful","focus","relax"
    ],
    "social": [
        "فريق","مجموعة","ناس","شريك","تنافس جماعي",
        "team","group","people","partner","club","league"
    ],
    "solo": [
        "لوحدي","انفرادي","فردي","خصوصية",
        "solo","alone","individual","privacy"
    ],
    "novelty": [
        "جديد","غريب","اكتشاف","تجربة","تجارب","ابتكار",
        "new","novel","explore","discovery","experiment","innovate","weird"
    ],
    "routine": [
        "روتين","ثابت","عادة","انضباط","تكرار",
        "routine","discipline","habit","repeat","consistency"
    ],
    "competition": [
        "تنافس","بطولة","نقاط","فوز","خسارة","خصم",
        "compete","competitive","tournament","rank","score","win","lose","opponent"
    ],
    "outdoor": [
        "خارجي","خارج","هواء طلق","طبيعة","جبل","بحر","شاطئ","مضمار",
        "outdoor","outside","trail","mountain","beach","park","track","nature"
    ],
    "indoor": [
        "داخلي","بيت","منزل","صالة","نادي","غرفة",
        "indoor","home","gym","room","hall"
    ],
    "strength": [
        "قوة","رفع","مقاومة","عضلات","أثقال","بار",
        "strength","lift","resistance","muscle","weights","barbell","dumbbell"
    ],
    "endurance": [
        "تحمل","إيقاع","نَفَس","مسافة","زمن طويل",
        "endurance","aerobic","long","pace","cardio","distance"
    ],
    "mobility": [
        "مرونة","إطالة","مفاصل","توازن","حركة واعية",
        "mobility","flexibility","stretch","joint","balance","range"
    ],
    "creativity": [
        "إبداع","تصميم","ارتجال","فن","تعبير",
        "creative","creativity","improv","design","art","express"
    ],
    "risk_high": [
        "خطر","مخاطرة","قفز","قتال","سلاح","high risk","danger","extreme","combat"
    ],
    "risk_low": [
        "آمن","بدون خطر","خفيف","low risk","safe","safety","gentle"
    ],
    "time_short": [
        "10","١٠","15","١٥","20","٢٠","قصير","سريع","دقائق قليلة",
        "short","10min","15min","20min","quick"
    ],
    "budget_low": [
        "صفر","مجاني","بدون تكلفة","بسيط","منزل",
        "free","zero","cheap","low budget","no equipment","home"
    ],
}

# بعض الترجيحات الافتراضية لفهم الميول
DEFAULT_WEIGHTS: Dict[str, float] = {
    "adrenaline": 1.3,
    "tactical": 1.2,
    "mindful": 1.1,
    "social": 1.0,
    "solo": 1.0,
    "novelty": 1.1,
    "routine": 1.0,
    "competition": 1.1,
    "outdoor": 1.0,
    "indoor": 1.0,
    "strength": 1.0,
    "endurance": 1.0,
    "mobility": 1.0,
    "creativity": 1.0,
    "risk_high": 1.0,
    "risk_low": 1.0,
    "time_short": 1.0,
    "budget_low": 1.0,
}

def _norm_text(x: Any) -> str:
    return str(x or "").strip().lower()

def _token_hits(text: str) -> List[str]:
    hits: List[str] = []
    for cat, words in KEYWORDS.items():
        for w in words:
            # مطابقة كلمة ضمنية (غير متشددة)
            if re.search(rf"\b{re.escape(w.lower())}\b", text, flags=re.IGNORECASE):
                hits.append(cat); break
    return hits

def _score_answers(answers: Dict[str, Any]) -> Dict[str, float]:
    scores: Dict[str, float] = {k: 0.0 for k in DEFAULT_WEIGHTS}
    for qk, payload in (answers or {}).items():
        if not isinstance(payload, dict):
            # صيغة قديمة: answers[q] = "text" أو ["a","b"]
            vals = payload if isinstance(payload, list) else [payload]
            texts = [_norm_text(v) for v in vals]
        else:
            a = payload.get("answer", "")
            if isinstance(a, list):
                texts = [_norm_text(v) for v in a]
            else:
                texts = [_norm_text(a)]

        for t in texts:
            if not t: 
                continue
            cats = _token_hits(t)
            # موازنة بسيطة: جملة أطول بقليل = أثر أعلى
            length_boost = min(len(t)/60.0, 1.0)  # سقف 1.0
            for c in cats:
                scores[c] += (1.0 + 0.3*length_boost) * DEFAULT_WEIGHTS.get(c, 1.0)

        # استدلالات خفيفة من صياغة السؤال (إن وُجدت)
        q_txt = _norm_text(payload.get("question", qk)) if isinstance(payload, dict) else _norm_text(qk)
        if "لوحد" in q_txt or "alone" in q_txt or "solo" in q_txt:
            # سؤال تفضيل اجتماعي — لو الإجابة تحتوي "لوحدي" أو "solo"
            if any(x in " ".join(texts) for x in ["لوحدي","solo","alone","فردي","individ"]):
                scores["solo"] += 0.8
            if any(x in " ".join(texts) for x in ["مجموعة","فريق","group","team","ناس"]):
                scores["social"] += 0.8

    return scores

def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
    mx = max(scores.values()) if scores else 0.0
    if mx <= 0: 
        return {k: 0.0 for k in scores}
    return {k: round(v / mx, 3) for k, v in scores.items()}

def _derive_preferences(scores: Dict[str, float]) -> Dict[str, Any]:
    # اشتقاقات مبسطة تعطي معنى مباشر للبروفايل
    def tri(c: str) -> str:
        v = scores.get(c, 0.0)
        return "high" if v >= 0.66 else "medium" if v >= 0.33 else "low"

    env = "outdoor" if scores.get("outdoor",0)>scores.get("indoor",0) else "indoor" if scores.get("indoor",0)>0 else "mixed"
    group_pref = "solo" if scores.get("solo",0)>scores.get("social",0) else "group" if scores.get("social",0)>0 else "mixed"
    intensity = "high" if max(scores.get("adrenaline",0), scores.get("endurance",0), scores.get("strength",0))>=0.66 else "medium" if max(scores.get("adrenaline",0), scores.get("endurance",0), scores.get("strength",0))>=0.33 else "low"
    risk = "high" if scores.get("risk_high",0) > scores.get("risk_low",0) else "low" if scores.get("risk_low",0) > 0 else "medium"
    novelty = tri("novelty")
    routine = tri("routine")
    comp = tri("competition")
    focus = "tactical" if scores.get("tactical",0)>=max(scores.get("mindful",0), scores.get("creativity",0)) else "mindful" if scores.get("mindful",0)>=scores.get("creativity",0) else "creative"

    time_slot = "short" if scores.get("time_short",0)>=0.33 else "flexible"
    budget = "low" if scores.get("budget_low",0)>=0.33 else "flexible"

    top5 = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:5]
    primary_modes = [k for k,v in top5 if v>0]

    return {
        "environment": env,
        "group_preference": group_pref,
        "intensity": intensity,
        "risk_tolerance": risk,
        "novelty_seek": novelty,
        "routine_tolerance": routine,
        "competitiveness": comp,
        "cognitive_focus": focus,
        "time_per_session": time_slot,
        "budget": budget,
        "primary_modes": primary_modes,
    }

def _hints_for_prompt(scores: Dict[str,float], prefs: Dict[str,Any], lang: str) -> str:
    # نص مختصر يُمرَّر للباكند لتوجيه التوصيات بشكل أدق
    if lang == "العربية":
        return (
            f"بيئة: {prefs['environment']} | جماعية: {prefs['group_preference']} | شدة: {prefs['intensity']} | مجازفة: {prefs['risk_tolerance']} | "
            f"حداثة: {prefs['novelty_seek']} | روتين: {prefs['routine_tolerance']} | تنافسيّة: {prefs['competitiveness']} | تركيز: {prefs['cognitive_focus']} | "
            f"زمن الجلسة: {prefs['time_per_session']} | الميزانية: {prefs['budget']} | أنماط أساسية: {', '.join(prefs['primary_modes'])}"
        )
    else:
        return (
            f"Env: {prefs['environment']} | Group: {prefs['group_preference']} | Intensity: {prefs['intensity']} | Risk: {prefs['risk_tolerance']} | "
            f"Novelty: {prefs['novelty_seek']} | Routine: {prefs['routine_tolerance']} | Competitive: {prefs['competitiveness']} | Focus: {prefs['cognitive_focus']} | "
            f"Session time: {prefs['time_per_session']} | Budget: {prefs['budget']} | Primary modes: {', '.join(prefs['primary_modes'])}"
        )

def encode_answers(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    """
    تُرجع بروفايل منظّم:
      - vector: الدرجات الخام
      - scores: مُطبَّعة 0..1
      - preferences: استنتاجات مباشرة (بيئة، شدة، مجازفة..)
      - hints_for_prompt: جملة موجزة تُساعد الباكند
    """
    raw_scores = _score_answers(answers)
    scores = _normalize(raw_scores)
    prefs = _derive_preferences(scores)
    hints = _hints_for_prompt(scores, prefs, lang)

    return {
        "lang": lang,
        "vector": raw_scores,
        "scores": scores,
        "preferences": prefs,
        "hints_for_prompt": hints,
    }
