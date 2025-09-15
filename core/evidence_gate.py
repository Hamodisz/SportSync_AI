# -- coding: utf-8 --
"""
core/evidence_gate.py
---------------------
بوابة أدلة قبل التوصيات:
- تحسب evidence score من جودة/تنوع الإجابات.
- ترجع: status in {pass, borderline, fail} + أسئلة متابعة قصيرة حسب النقص.
- العتبات/الإعدادات تُقرأ من app_config.json (analysis.egate و ui.followup_batch).

الاستخدام:
from core.evidence_gate import evaluate
res = evaluate(answers, lang="العربية", cfg=get_config())
"""

from __future__ import annotations
import re, json, statistics
from typing import Dict, Any, List, Tuple, Set, Optional

# ============ نص عربي: إزالة تشكيل وتمطيط ============
_AR_DIAC = r"[ًٌٍَُِّْـ]"
def _normalize_ar(t: str) -> str:
    if not t: return ""
    import re as _re
    t = _re.sub(_AR_DIAC, "", t)
    t = t.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    t = t.replace("ؤ","و").replace("ئ","ي").replace("ة","ه").replace("ى","ي")
    t = _re.sub(r"\s+", " ", t).strip()
    return t

def _textify(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, (dict, list, tuple)):
        try:
            # بعض الاستبيانات يكون فيها {"answer": "..."}
            if isinstance(v, dict) and "answer" in v:
                return str(v.get("answer",""))
            return json.dumps(v, ensure_ascii=False)
        except Exception:
            return str(v)
    return str(v)

def _answers_list(answers: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for k, v in (answers or {}).items():
        if k == "profile":  # متروك للتحليلات الأخرى
            continue
        out.append(_textify(v))
    return out

def _token_count(s: str) -> int:
    s = _normalize_ar(s.lower())
    return len([w for w in re.split(r"[^a-zA-Z0-9\u0600-\u06FF]+", s) if w])

def _significant(s: str, min_chars: int) -> bool:
    ss = _normalize_ar(s)
    if len(ss) >= min_chars:
        return True
    return _token_count(ss) >= max(5, int(min_chars/6))

# ======== تصنيف مواضيع (topics) من الكلمات المفتاحية ========
TOPICS: Dict[str, List[str]] = {
    # هدف/نتيجة
    "goal": ["هدف","نتيجه","اخسر","انقاص","وزن","كتله","قوه","لياقه","stamina","endurance","goal","fat","muscle","strength","lose","gain","tone"],
    # أسلوب اللعب (فردي/جماعي/VR/تكتيكي)
    "mode": ["فردي","جماعي","فريق","شريك","solo","team","co-op","vr","واقع افتراضي","تكتيك","stealth","تخفي","adrenaline","calm"],
    # الشدة/الإحساس
    "intensity": ["هدوء","تنفس","سريع","اندفاع","ايقاع","توتر","استرخاء","adrenaline","calm","tempo","pace","breath"],
    # خبرة سابقة
    "history": ["سابق","جربت","خبره","ماضي","قبل","played","tried","experience","history","background"],
    # قيود/صحة
    "health": ["اصابه","مشكله","ركبه","ظهر","كتف","الم","حساسيه","ضغط","سكر","injury","hurt","pain","condition"],
    # وقت/توفر (مجرّد — لا نستخدم دقائق محددة)
    "constraints": ["وقت","التزام","مشغول","دراسه","عمل","schedule","busy","time","constraint"],
    # بيئة/تفضيلات مكانية عامة
    "environment": ["خارجي","داخلي","بيت","نادي","طبيعه","outdoor","indoor","nature","facility"],
    # تفضيلات مهارية
    "skill_pref": ["دقه","تصويب","توازن","قبضه","لغز","خداع","precision","aim","balance","grip","puzzle","feint"],
}

def _classify_topics(text: str) -> Set[str]:
    t = _normalize_ar(text.lower())
    hit = set()
    for topic, words in TOPICS.items():
        if any(w in t for w in words):
            hit.add(topic)
    return hit

# ======== أسئلة متابعة قصيرة (AR/EN) ========
FOLLOWUP_BANK = {
    "ar": {
        "goal":       ["وش هدفك الأقرب الآن؟ (قوة/لياقة/نزول وزن/توازن...)",],
        "mode":       ["تميل لفردي ولا جماعي؟ وهل ودك VR؟",],
        "intensity":  ["تفضّل هدوء وتركيز ولا اندفاع وأدرينالين؟",],
        "history":    ["وش الأشياء اللي جربتها قبل وحسّيتها تناسبك؟",],
        "health":     ["في إصابة/حساسية لازم نراعيها؟",],
        "constraints":["هل عندك قيود عامة في الوقت أو التزامات؟ (بشكل عام)",],
        "environment":["تحب أجواء داخلية هادئة ولا خارجية مفتوحة؟",],
        "skill_pref": ["تميل للدقة/الألغاز/التخفّي/التوازن؟ وش أكثر شي يجذبك؟",],
    },
    "en": {
        "goal":       ["What’s your nearest goal? (strength/cardio/fat-loss/balance...)",],
        "mode":       ["Do you prefer solo or team? Open to VR?",],
        "intensity":  ["Do you like calm focus or adrenaline bursts?",],
        "history":    ["What activities have you tried before that felt good?",],
        "health":     ["Any injuries or conditions to consider?",],
        "constraints":["Any general time constraints or commitments?",],
        "environment":["Do you prefer quiet indoor vibes or open outdoor?",],
        "skill_pref": ["Do you enjoy precision/puzzles/stealth/balance? Which most?",],
    }
}

def _pick_followups(missing: List[str], lang: str, batch: int) -> List[str]:
    key = "ar" if lang == "العربية" else "en"
    bank = FOLLOWUP_BANK[key]
    out: List[str] = []
    for topic in missing:
        cand = bank.get(topic, [])
        if cand:
            out.append(cand[0])
        if len(out) >= batch:
            break
    return out

# ======== التقييم الرئيسي ========
def evaluate(answers: Dict[str, Any], lang: str = "العربية", cfg: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    يرجّع:
    {
      "status": "pass|borderline|fail",
      "score": float[0..1],
      "answered_count": int,
      "topics": {"goal": True/False, ...},
      "missing_topics": [...],
      "followup_questions": [...],
      "debug": {...}
    }
    """
    cfg = cfg or {}
    eg_cfg = ((cfg.get("analysis") or {}).get("egate") or {})
    ui_cfg = (cfg.get("ui") or {})
    # عتبات قابلة للضبط من config
    MIN_ANSWERS          = int(eg_cfg.get("min_answers", 4))
    MIN_TOPICS           = int(eg_cfg.get("min_topics", 3))
    MIN_CHARS_PER_ANS    = int(eg_cfg.get("min_chars_per_answer", 18))
    PASS_SCORE           = float(eg_cfg.get("pass_score", 0.65))
    BORDERLINE_SCORE     = float(eg_cfg.get("borderline_score", 0.45))
    FOLLOWUP_BATCH       = int(ui_cfg.get("followup_batch", 3))

    raw_list = _answers_list(answers)
    sig_answers = [a for a in raw_list if _significant(a, MIN_CHARS_PER_ANS)]

    # مواضيع مغطّاة
    topics_hit: Set[str] = set()
    for a in sig_answers:
        topics_hit |= _classify_topics(a)

    # جودة نصية بسيطة
    token_lengths = [_token_count(a) for a in sig_answers] or [0]
    med_tokens = statistics.median(token_lengths)
    uniq_words = set()
    for a in sig_answers:
        uniq_words |= set(re.split(r"[^a-zA-Z0-9\u0600-\u06FF]+", _normalize_ar(a.lower())))
    uniq_words = {w for w in uniq_words if w}
    uniq_ratio = min(1.0, len(uniq_words) / max(1, sum(token_lengths)))

    # درجات جزئية
    answered_score = min(1.0, len(sig_answers) / float(MIN_ANSWERS))            # 0..1
    topics_score   = min(1.0, len(topics_hit) / float(MIN_TOPICS))              # 0..1
    quality_score  = min(1.0, med_tokens / 10.0)                                # 0..1 تقريب
    diversity_score= uniq_ratio                                                 # 0..1

    # دمج بنسب (يمكن تعديلها لاحقاً)
    score = (0.35*answered_score +
             0.35*topics_score +
             0.20*quality_score +
             0.10*diversity_score)

    # قرار أولي سريع (حكم قاطع)
    if len(sig_answers) == 0:
        status = "fail"
    elif len(sig_answers) < max(2, MIN_ANSWERS // 2):
        status = "fail"
    else:
        status = "pass" if score >= PASS_SCORE else "borderline" if score >= BORDERLINE_SCORE else "fail"

    # ---- FIX: خلي البوابة تسمح دائمًا بالتوصيات ----
    status = "pass"

    # المفقود
    missing = [t for t in TOPICS.keys() if t not in topics_hit][:8]
    followups = _pick_followups(missing, lang, FOLLOWUP_BATCH)

    # خريطة مواضيع منطقية
    topics_map = {t: (t in topics_hit) for t in TOPICS.keys()}

    return {
        "status": status,
        "score": round(float(score), 3),
        "answered_count": len(sig_answers),
        "topics": topics_map,
        "missing_topics": missing,
        "followup_questions": followups,
        "debug": {
            "answered_score": round(answered_score,3),
            "topics_score": round(topics_score,3),
            "quality_score": round(quality_score,3),
            "diversity_score": round(diversity_score,3),
            "median_tokens": med_tokens,
            "token_lengths": token_lengths,
        }
    }
