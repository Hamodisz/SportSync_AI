# core/recs/engine.py
# -- coding: utf-8 --
"""
SportSync — Recommendations Engine (split version)
==================================================

هذا الملف هو "محرّك التوصيات" بعد تقسيم backend_gpt.py.
يعتمد على وحدات مساندة صغيرة تم فصلها لتخفيف الضغط عن المحرّك:

- core/recs/text_ops.py      : دوال النصوص والتنظيف والتطبيع
- core/recs/kb.py            : تحميل قاعدة المعرفة والثوابت المرتبطة بها (إن وُجدت)
- core/recs/rules.py         : الضوابط، الإعدادات، وثوابت التشغيل
- core/recs/templates.py     : قوالب الهوية + fill_defaults + fallback_identity
- core/recs/dedupe.py        : التوقيع، jaccard، dedupe محلي/عالمي + إدارة blacklist.json

المخرجات العامة:
- generate_sport_recommendation(...)
- start_recommendation_job(...)

الملاحظات:
- لا نختصر نصوص التوصيات.
- نفس القيود الجوهرية: لا وقت/تكلفة/عدّات/جولات/مكان مباشر.
- المسار الواقعي أولاً (Evidence Gate + KB + Templates)، ثم LLM كملاذ أخير.
"""

from __future__ import annotations

import os, json, re, hashlib, importlib
from time import perf_counter, sleep
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

# ========= تكوين البيئة / الإعدادات =========
# نحمل الضوابط والـ CFG من rules
try:
    from core.recs.rules import (
        CFG, CHAT_MODEL, CHAT_MODEL_FALLBACK, ALLOW_SPORT_NAMES,
        REC_BUDGET_S, REC_REPAIR_ENABLED, REC_FAST_MODE, REC_DEBUG,
        MAX_PROMPT_CHARS, MIN_CHARS as _MIN_CHARS, REQUIRE_WIN as _REQUIRE_WIN,
        MIN_CORE_SKILLS as _MIN_CORE_SKILLS,
        forbidden_sentence_re as _FORBIDDEN_SENT,
        blocklist_re as _name_re,
        axes_expectations as _axes_expectations,
        mismatch_with_axes as _mismatch_with_axes,
        debug as _dbg
    )
except Exception as e:
    raise RuntimeError("rules.py مفقود أو غير قابل للاستيراد، تأكّد من إنشاء core/recs/rules.py") from e

# ========= توصيل قاعدة المعرفة =========
try:
    from core.recs.kb import (
        KB, KB_PRIORS, TRAIT_LINKS, GUARDS, HIGH_RISK_SPORTS, KB_ZI
    )
except Exception as e:
    # التشغيل ممكن بدون KB، لكن سيفقد بعض الذكاء في الترشيح
    KB, KB_PRIORS, TRAIT_LINKS, GUARDS, HIGH_RISK_SPORTS, KB_ZI = {}, {}, {}, {}, set(), {}
    _dbg(f"[KB] ⚠️ Fallback (no KB): {e}")

# ========= أدوات نصوص / تنظيف =========
try:
    from core.recs.text_ops import (
        normalize_ar as _normalize_ar,
        norm_text as _norm_text,
        split_sentences as _split_sentences,
        scrub_forbidden as _scrub_forbidden,
        to_bullets as _to_bullets,
        strip_code_fence as _strip_code_fence,
        has_sensory as _has_sensory,
        too_generic as _too_generic,
        is_meaningful as _is_meaningful,
        clip as _clip
    )
except Exception as e:
    raise RuntimeError("text_ops.py مفقود أو غير قابل للاستيراد، تأكّد من إنشاء core/recs/text_ops.py") from e

# ========= قوالب / افتراضات =========
try:
    from core.recs.templates import (
        fallback_identity as _fallback_identity,
        fill_defaults as _fill_defaults,
        template_for_label as _template_for_label
    )
except Exception as e:
    raise RuntimeError("templates.py مفقود أو غير قابل للاستيراد، تأكّد من إنشاء core/recs/templates.py") from e

# ========= dedupe & blacklist =========
try:
    from core.recs.dedupe import (
        hard_dedupe_and_fill as _hard_dedupe_and_fill,
        ensure_unique_labels_v_global as _ensure_unique_labels_v_global,
        load_blacklist as _load_blacklist,
        persist_blacklist as _persist_blacklist,
        sig_for_rec as _sig_for_rec,
        jaccard as _jaccard
    )
except Exception as e:
    raise RuntimeError("dedupe.py مفقود أو غير قابل للاستيراد، تأكّد من إنشاء core/recs/dedupe.py") from e

# ========= Job Manager (اختياري) =========
try:
    from core.job_manager import create_job, read_job, update as job_update, run_in_thread
except Exception:
    def create_job(meta: Optional[dict] = None): return {"id": "nojob", "status": "error"}
    def read_job(job_id: str): return None
    def job_update(job_id: str, **kw): pass
    def run_in_thread(job_id: str, target, *args, **kwargs): return None

def _job_note(job_id: str,
              progress: Optional[int] = None,
              note: Optional[str] = None,
              status: Optional[str] = None) -> None:
    if not job_id:
        return
    try:
        payload: Dict[str, Any] = {}
        if progress is not None: payload["progress"] = int(progress)
        if note: payload["note"] = note
        if status: payload["status"] = status
        if payload:
            job_update(job_id, **payload)
    except Exception:
        pass

# ========= OpenAI =========
try:
    from openai import OpenAI
except Exception as e:
    raise RuntimeError("أضف الحزمة في requirements: openai>=1.6.1,<2") from e

OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENROUTER_API_KEY")
    or os.getenv("AZURE_OPENAI_API_KEY")
)
OPENAI_BASE_URL = (
    os.getenv("OPENAI_BASE_URL")
    or os.getenv("OPENROUTER_BASE_URL")
    or os.getenv("AZURE_OPENAI_ENDPOINT")
)
OPENAI_ORG = os.getenv("OPENAI_ORG")

OpenAI_CLIENT = None
if OPENAI_API_KEY:
    try:
        kwargs = {"api_key": OPENAI_API_KEY}
        if OPENAI_BASE_URL:
            kwargs["base_url"] = OPENAI_BASE_URL
        if OPENAI_ORG:
            kwargs["organization"] = OPENAI_ORG
        OpenAI_CLIENT = OpenAI(**kwargs)
    except Exception as e:
        _dbg(f"[ENV] ⚠️ فشل إنشاء عميل OpenAI: {e}")
        OpenAI_CLIENT = None
else:
    _dbg("[ENV] ⚠️ لا يوجد API key في المتغيرات البيئية.")

print(
    f"[BOOT] LLM READY? {'YES' if OpenAI_CLIENT else 'NO'} | "
    f"base={OPENAI_BASE_URL or 'default'} | "
    f"model={CHAT_MODEL}"
)

# ========= Data pipe / Security / Logs =========
try:
    from core.data_pipe import get_pipe
    _PIPE = get_pipe()
except Exception:
    _PIPE = None

try:
    from core.security import scrub_unknown_urls
except Exception:
    def scrub_unknown_urls(text_or_card: str, cfg: Dict[str, Any]) -> str:
        return text_or_card

try:
    from core.user_logger import log_user_insight
except Exception:
    def log_user_insight(user_id: str, content: Dict[str, Any], event_type: str = "event") -> None:
        print(f"[LOG:{event_type}] {user_id}: {list(content.keys())}")

# ========= Evidence Gate (خارجي + fallback) =========
try:
    from core.evidence_gate import evaluate as egate_evaluate
except Exception:
    egate_evaluate = None

_EGCFG = (CFG.get("analysis") or {}).get("egate", {}) if isinstance(CFG.get("analysis"), dict) else {}
_EG_MIN_ANSWERS = int(_EGCFG.get("min_answered", 3))
_EG_MIN_TOTAL_CHARS = int(_EGCFG.get("min_total_chars", 120))
_EG_REQUIRED_KEYS = list(_EGCFG.get("required_keys", []))

def _norm_answer_value(v: Any) -> str:
    if v is None: return ""
    if isinstance(v, dict):
        if "answer" in v: return str(v.get("answer") or "")
        if "value" in v: return str(v.get("value") or "")
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return ", ".join(map(str, v))
    return str(v)

def _egate_fallback(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    if not isinstance(answers, dict) or not answers:
        status = "fail"; total_chars = 0; answered = 0
    else:
        vals = [_norm_answer_value(v) for v in answers.values() if str(v).strip()]
        total_chars = sum(len(s.strip()) for s in vals)
        answered = sum(1 for s in vals if len(s.strip()) >= 3)
        if _EG_REQUIRED_KEYS:
            if any(not _norm_answer_value(answers.get(k, "")).strip() for k in _EG_REQUIRED_KEYS):
                status = "fail"
            else:
                status = "pass" if (answered >= _EG_MIN_ANSWERS and total_chars >= _EG_MIN_TOTAL_CHARS) else "borderline"
        else:
            if answered == 0 or total_chars < 40:
                status = "fail"
            elif answered < _EG_MIN_ANSWERS or total_chars < _EG_MIN_TOTAL_CHARS:
                status = "borderline"
            else:
                status = "pass"

    followups = (
        [
            "تفضّل اللعب: فردي أم جماعي؟ ولماذا بسطر واحد.",
            "تميل لهدوء وانسياب أم أدرينالين وقرارات خاطفة؟",
            "تحب دقّة/تصويب أم ألغاز/خداع بصري أثناء الحركة؟"
        ] if lang == "العربية" else [
            "Do you prefer solo or team play — and why, in one short line?",
            "Do you want calm/flow or adrenaline/snap decisions?",
            "Are you more into precision/aim or puzzles/visual feints in motion?"
        ]
    )
    return {
        "status": "fail" if answered == 0 or total_chars < 40 else status,
        "answered": int(answered),
        "total_chars": int(total_chars),
        "required_missing": [k for k in _EG_REQUIRED_KEYS if not _norm_answer_value((answers or {}).get(k, "")).strip() ],
        "followup_questions": followups[:3]
    }

def _run_egate(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    if callable(egate_evaluate):
        try:
            res = egate_evaluate(answers=answers, lang=lang, cfg=_EGCFG)
            if isinstance(res, dict) and "status" in res:
                return res
        except Exception:
            pass
    return _egate_fallback(answers, lang=lang)

def _format_followup_card(followups: List[str], lang: str) -> str:
    head = "🧭 نحتاج إجابات قصيرة قبل التوصية" if lang == "العربية" else "🧭 I need a few quick answers first"
    tips = "اكتب سطر واحد لكل سؤال." if lang == "العربية" else "One short line per question."
    lines = [head, "", tips, ""]
    for q in followups:
        lines.append(f"- {q}")
    lines.append("")
    lines.append("أرسل إجاباتك وسنقترح هوية رياضية واضحة فورًا." if lang == "العربية"
                 else "Send your answers and I’ll propose a clear sport-identity right away.")
    return "\n".join(lines)

# ========= أدوات إشارات / Intent =========
def _lang_key(lang: str) -> str:
    return "ar" if (lang or "").startswith("الع") else "en"

def _extract_signals(answers: Dict[str, Any], lang: str) -> Dict[str, int]:
    blob = " ".join(
        (v.get("answer") if isinstance(v, dict) and "answer" in v else str(v))
        for v in (answers or {}).values()
    )
    blob_l = blob.lower()
    blob_n = _normalize_ar(blob_l)
    res: Dict[str, int] = {}
    zi = KB_ZI.get(_lang_key(lang), {})

    def any_kw(keys: List[str]) -> bool:
        return any((k.lower() in blob_l) or (_normalize_ar(k).lower() in blob_n) for k in keys)

    if any_kw(zi.get("VR", ["vr","virtual reality","headset","واقع افتراضي","نظاره"])): res["vr"] = 1
    if any_kw(zi.get("دقة/تصويب", []) + zi.get("Precision", []) + ["precision","aim","نشان","دقه"]): res["precision"] = 1
    if any_kw(zi.get("تخفّي", []) + zi.get("Stealth", []) + ["stealth","ظل","تخفي"]): res["stealth"] = 1
    if any_kw(zi.get("قتالي", []) + zi.get("Combat", []) + ["قتال","مبارزه","اشتباك","combat"]): res["combat"] = 1
    if any_kw(zi.get("ألغاز/خداع", []) + zi.get("Puzzles/Feint", []) + ["puzzle","لغز","خدعه"]): res["puzzles"] = 1
    if any_kw(zi.get("فردي", []) + ["solo","وحيد","لوحدي"]): res["solo_pref"] = 1
    if any_kw(zi.get("جماعي", []) + ["team","group","فريق","جماعي"]): res["team_pref"] = 1
    if any_kw(zi.get("هدوء/تنفّس", []) + zi.get("Calm/Breath", []) + ["breath","calm","هدوء","تنفس"]):
        res["breath"] = 1; res["calm"] = 1
    if any_kw(zi.get("أدرينالين", []) + zi.get("Adrenaline", []) + ["fast","rush","اندفاع"]):
        res["high_agg"] = 1
    return res

def _call_analyze_intent(answers: Dict[str, Any], lang: str="العربية") -> List[str]:
    for modpath in ("core.layer_z_engine", "analysis.layer_z_engine"):
        try:
            mod = importlib.import_module(modpath)
            if hasattr(mod, "analyze_user_intent"):
                return list(mod.analyze_user_intent(answers, lang=lang) or [] )
        except Exception:
            pass
    intents = set()
    sig = _extract_signals(answers, lang)
    if sig.get("vr"): intents.add("VR")
    if sig.get("stealth"): intents.add("تخفّي")
    if sig.get("puzzles"): intents.add("ألغاز/خداع")
    if sig.get("precision"): intents.add("دقة/تصويب")
    if sig.get("combat"): intents.add("قتالي")
    if sig.get("solo_pref"): intents.add("فردي")
    if sig.get("team_pref"): intents.add("جماعي")
    if sig.get("breath"): intents.add("هدوء/تنفّس")
    if sig.get("high_agg"): intents.add("أدرينالين")
    return list(intents)

# ========= تحليل المستخدم =========
def _call_analyze_user_from_answers(user_id: str, answers: Dict[str, Any], lang: str) -> Dict[str, Any]:
    try:
        from analysis.user_analysis import analyze_user_from_answers as _ana
        try:
            out = _ana(user_id=user_id, answers=answers, lang=lang)
        except TypeError:
            out = _ana(answers)
        return {"traits": out} if isinstance(out, list) else (out or {})
    except Exception:
        try:
            from core.user_analysis import analyze_user_from_answers as _ana2
            try:
                out = _ana2(user_id=user_id, answers=answers, lang=lang)
            except TypeError:
                out = _ana2(answers)
            return {"traits": out} if isinstance(out, list) else (out or {})
        except Exception:
            return {"quick_profile": "fallback", "raw_answers": answers}

def _extract_profile(answers: Dict[str, Any], lang: str) -> Optional[Dict[str, Any]]:
    prof = answers.get("profile") if isinstance(answers, dict) else None
    if isinstance(prof, dict):
        return prof
    encode_answers = None
    try:
        from core.answers_encoder import encode_answers as _enc
        encode_answers = _enc
    except Exception:
        try:
            from analysis.answers_encoder import encode_answers as _enc
            encode_answers = _enc
        except Exception:
            encode_answers = None
    if encode_answers is None:
        return None
    try:
        enc = encode_answers(answers, lang=lang)
        preferences = enc.get("prefs", enc.get("preferences", {}))
        z_markers = enc.get("z_markers", [])
        signals   = enc.get("signals", [])
        hints = " | ".join([*z_markers, *signals])[:1000]
        return {
            "scores": enc.get("scores", {}),
            "axes": enc.get("axes", {}),
            "preferences": preferences,
            "hints_for_prompt": hints,
            "vr_inclination": enc.get("vr_inclination", 0),
            "confidence": enc.get("confidence", 0.0),
            "signals": signals,
            "z_markers": z_markers
        }
    except Exception:
        return None

# ========= أدوات عامّة =========
def _contains_blocked_name(t: str) -> bool:
    if not t: return False
    return bool(_name_re.search(t)) or bool(_name_re.search(_normalize_ar(t)))

def _mask_names(t: str) -> str:
    if ALLOW_SPORT_NAMES:
        return t or ""
    s = t or ""
    s = _name_re.sub("—", s)
    if s == (t or "") and _contains_blocked_name(t):
        s = "—"
    return s

def _sanitize_record(r: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(r or {})
    r.pop("practical_fit", None)
    for k in ("sport_label","scene","what_it_looks_like","inner_sensation","why_you",
              "first_week","progress_markers","win_condition","variant_vr","variant_no_vr","vr_idea","mode"):
        if k in r:
            r[k] = _scrub_forbidden(_mask_names(_norm_text(r.get(k))))
    cs = r.get("core_skills")
    if isinstance(cs, str):
        parts = [p.strip(" -•\t") for p in re.split(r"[,\n،]+", cs) if p.strip()]
        r["core_skills"] = parts[:6]
    elif isinstance(cs, (list, tuple)):
        skills = [_norm_text(x).strip() for x in cs if _norm_text(x).strip()]
        r["core_skills"] = skills[:6]
    else:
        r["core_skills"] = []
    try:
        d = int(r.get("difficulty", 3))
        r["difficulty"] = max(1, min(5, d))
    except Exception:
        r["difficulty"] = 3
    if r.get("mode") not in ("Solo","Team","Solo/Team","فردي","جماعي","فردي/جماعي"):
        r["mode"] = r.get("mode","Solo")
    return r

def _style_seed(user_id: str, profile: Optional[Dict[str, Any]]) -> int:
    base = user_id or "anon"
    axes = profile.get("axes", {}) if isinstance(profile, dict) else {}
    s = f"{base}:{json.dumps(axes, sort_keys=True, ensure_ascii=False)}"
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:8], 16)

def _answers_to_bullets(answers: Dict[str, Any]) -> str:
    lines: List[str] = []
    for k, v in (answers or {}).items():
        lines.append(f"- {k}: {_norm_answer_value(v)}")
    return "\n".join(lines)

def _compact_analysis_for_prompt(analysis: Dict[str, Any], profile: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    p_axes   = (profile or {}).get("axes", {})
    p_signals= (profile or {}).get("signals", [])
    hints    = (profile or {}).get("hints_for_prompt", "")
    out = {
        "silent_drivers": analysis.get("silent_drivers", []),
        "z_axes": analysis.get("z_axes", p_axes),
        "z_intent": analysis.get("z_intent", []),
        "encoded_profile": {"axes": p_axes, "signals": p_signals, "hints": _clip(str(hints), 300)},
    }
    blob = json.dumps(out, ensure_ascii=False)
    if len(blob) > MAX_PROMPT_CHARS // 2:
        out["encoded_profile"]["signals"] = out["encoded_profile"]["signals"][:10]
    return out

def _json_prompt(analysis: Dict[str, Any], answers: Dict[str, Any],
                 personality: Any, lang: str, style_seed: int) -> List[Dict[str, str]]:
    bullets = _answers_to_bullets(answers)
    persona = personality if isinstance(personality, str) else json.dumps(personality, ensure_ascii=False)
    profile = analysis.get("encoded_profile") or {}
    compact_analysis = _compact_analysis_for_prompt(analysis, profile)

    comp_blob = json.dumps(compact_analysis, ensure_ascii=False)
    if len(comp_blob) > MAX_PROMPT_CHARS:
        compact_analysis = {"z_axes": compact_analysis.get("z_axes", {}), "z_intent": compact_analysis.get("z_intent", [])}

    axis = compact_analysis.get("z_axes", {})
    exp = _axes_expectations(axis, lang)
    exp_lines = []
    if exp:
        title = {"calm_adrenaline":"هدوء/أدرينالين","solo_group":"فردي/جماعي","tech_intuition":"تقني/حدسي"} \
                if lang=="العربية" else \
                {"calm_adrenaline":"Calm/Adrenaline","solo_group":"Solo/Group","tech_intuition":"Technical/Intuitive"}
        for k, words in exp.items():
            if words:
                exp_lines.append(f"{title[k]}: {', '.join(words)}")
    axis_hint = ("\n".join(exp_lines)) if exp_lines else ""

    z_intent = compact_analysis.get("z_intent", [])
    intent_hint = ("، ".join(z_intent) if lang=="العربية" else ", ".join(z_intent)) if z_intent else ""

    if lang == "العربية":
        sys = (
            "أنت مدرّب SportSync AI بنبرة إنسانية لطيفة (صديق محترف).\n"
            "ممنوع ذكر (الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر).\n"
            "سَمِّ 'هوية/رياضة' واضحة عند الحاجة.\n"
            "أعِد JSON فقط."
        )
        usr = (
            "حوّل بيانات المستخدم إلى ثلاث توصيات «هوية رياضية واضحة». "
            "أعِد JSON بالمفاتيح: "
            "{\"recommendations\":[{"
            "\"sport_label\":\"...\",\"what_it_looks_like\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\"," 
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"win_condition\":\"...\"," 
            "\"core_skills\":[\"...\",\"...\"],\"mode\":\"Solo/Team\",\"variant_vr\":\"...\",\"variant_no_vr\":\"...\",\"difficulty\":1-5"
            "}]} "
            "قواعد إلزامية: اذكر win_condition و 3–5 core_skills على الأقل. "
            "حاذِ Z-axes بالكلمات التالية إن أمكن:\n" + axis_hint +
            ("\n\n— نوايا Z المحتملة: " + intent_hint if intent_hint else "") + "\n\n"
            f"— شخصية المدرب:\n{persona}\n\n"
            "— تحليل موجز:\n" + json.dumps(compact_analysis, ensure_ascii=False) + "\n\n"
            "— إجابات موجزة:\n" + bullets + "\n\n"
            f"— style_seed: {style_seed}\n"
            "أعِد JSON فقط."
        )
    else:
        sys = (
            "You are a warm, human SportSync coach. "
            "No time/cost/reps/sets/minutes/place. Name the sport/identity if clarity needs it. JSON only."
        )
        usr = (
            "Create THREE clear sport-like identities with required keys: "
            "{\"recommendations\":[{\"sport_label\":\"...\",\"what_it_looks_like\":\"...\",\"inner_sensation\":\"...\",\"why_you\":\"...\"," 
            "\"first_week\":\"...\",\"progress_markers\":\"...\",\"win_condition\":\"...\",\"core_skills\":[\"...\"]," 
            "\"mode\":\"Solo/Team\",\"variant_vr\":\"...\",\"variant_no_vr\":\"...\",\"difficulty\":1-5}]} "
            "Align with Z-axes using words:\n" + axis_hint +
            ( "\n\n— Z intents: " + intent_hint if intent_hint else "" ) + "\n\n"
            f"— Coach persona:\n{persona}\n— Compact analysis:\n" + json.dumps(compact_analysis, ensure_ascii=False) + "\n"
            "— Bulleted answers:\n" + bullets + f"\n— style_seed: {style_seed}\nJSON only."
        )
    return [{"role": "system", "content": sys}, {"role": "user", "content": usr}]

def _parse_json(text: str) -> Optional[List[Dict[str, Any]]]:
    if not text:
        return None
    text = _strip_code_fence(text)
    try:
        obj = json.loads(text)
        recs = obj.get("recommendations", [])
        if isinstance(recs, list) and recs:
            return recs
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text or "")
    if m:
        try:
            obj = json.loads(m.group(0))
            recs = obj.get("recommendations", [])
            if isinstance(recs, list) and recs:
                return recs
        except Exception:
            pass
    return None

def _format_card(rec: Dict[str, Any], i: int, lang: str) -> str:
    head_ar = ["🟢 التوصية رقم 1","🌿 التوصية رقم 2","🔮 التوصية رقم 3 (ابتكارية)"]
    head_en = ["🟢 Recommendation 1","🌿 Recommendation 2","🔮 Recommendation 3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[i]

    _s = _norm_text
    label = _s(rec.get("sport_label") or "").strip()
    scene = _s(rec.get("what_it_looks_like") or rec.get("scene") or "")
    inner = _s(rec.get("inner_sensation") or "")
    why   = _s(rec.get("why_you") or "")
    week  = _to_bullets(rec.get("first_week") or "", max_items=5)
    prog  = _to_bullets(rec.get("progress_markers") or "", max_items=4)
    win   = _s(rec.get("win_condition") or "")
    skills = _to_bullets(rec.get("core_skills") or [], max_items=5)
    try:
        diff  = int(rec.get("difficulty", 3))
    except Exception:
        diff = 3
    mode  = _s(rec.get("mode") or "Solo")
    vr    = _s(rec.get("variant_vr") or rec.get("vr_idea") or "")
    novr  = _s(rec.get("variant_no_vr") or "")

    intro = " — ".join([p for p in [scene.strip(), inner.strip()] if p])

    out: List[str] = [head, ""]
    if lang == "العربية":
        if label: out.append("🎯 الهوية المثالية لك: " + label)
        if intro:
            out += ["\n💡 ما هي؟", "- " + intro]
        if why:
            out.append("\n🎮 ليه تناسبك؟")
            for b in (_to_bullets(why, 4) or [why]):
                out.append("- " + _s(b))
        if skills:
            out.append("\n🧩 مهارات أساسية:")
            for s in skills:
                out.append("- " + _s(s))
        if win:
            out += ["\n🏁 كيف تفوز؟", "- " + win]
        if week:
            out.append("\n🚀 أول أسبوع (نوعي):")
            for b in week:
                out.append("- " + _s(b))
        if prog:
            out.append("\n✅ علامات تقدم محسوسة:")
            for b in prog:
                out.append("- " + _s(b))
        notes: List[str] = []
        if mode: notes.append("وضع اللعب: " + mode)
        if novr: notes.append("بدون VR: " + novr)
        if vr:   notes.append("VR (اختياري): " + vr)
        if notes:
            out.append("\n👁‍🗨 ملاحظات:")
            out.append("- " + "\n- ".join([_s(n) for n in notes]))
        out.append("\nالمستوى التقريبي: " + f"{max(1,min(5,diff))}/5")
    else:
        if label: out.append("🎯 Ideal identity: " + label)
        if intro:
            out += ["\n💡 What is it?", "- " + intro]
        if why:
            out.append("\n🎮 Why you")
            for b in (_to_bullets(why, 4) or [why]):
                out.append("- " + _s(b))
        if skills:
            out.append("\n🧩 Core skills:")
            for s in skills:
                out.append("- " + _s(s))
        if win:
            out += ["\n🏁 Win condition", "- " + win]
        if week:
            out.append("\n🚀 First week (qualitative)")
            for b in week:
                out.append("- " + _s(b))
        if prog:
            out.append("\n✅ Progress cues")
            for b in prog:
                out.append("- " + _s(b))
        notes: List[str] = []
        if mode: notes.append("Mode: " + mode)
        if novr: notes.append("No-VR: " + novr)
        if vr:   notes.append("VR (optional): " + vr)
        if notes:
            out.append("\n👁‍🗨 Notes:")
            out.append("- " + "\n- ".join([_s(n) for n in notes]))
        out.append("\nApprox level: " + f"{max(1,min(5,diff))}/5")

    return "\n".join([_s(x) for x in out])

def _sanitize_fill(recs: List[Dict[str, Any]], lang: str) -> List[Dict[str, Any]]:
    temp: List[Dict[str, Any]] = []
    for i in range(3):
        r = recs[i] if i < len(recs) else {}
        r = _fill_defaults(_sanitize_record(r), lang)

        vals = [
            _norm_text(r.get("sport_label","")),
            _norm_text(r.get("what_it_looks_like","")),
            _norm_text(r.get("why_you","")),
            _norm_text(r.get("first_week","")),
            _norm_text(r.get("progress_markers","")),
            _norm_text(r.get("win_condition","")),
        ]
        blob = " ".join(vals)

        if _too_generic(blob, _MIN_CHARS) or not _has_sensory(blob) or not _is_meaningful(r) \
           or (_REQUIRE_WIN and not r.get("win_condition")) \
           or len(r.get("core_skills") or []) < _MIN_CORE_SKILLS:
            r = _fallback_identity(i, lang)

        temp.append(r)

    return _hard_dedupe_and_fill(temp, lang)

# ========= LLM helper =========
def _chat_with_retry(messages: List[Dict[str, str]], max_tokens: int, temperature: float) -> str:
    if OpenAI_CLIENT is None:
        raise RuntimeError("OPENAI_API_KEY غير مضبوط")

    attempts = 4 if not REC_FAST_MODE else 3
    last_err = None
    model_local = CHAT_MODEL
    max_tokens_local = max_tokens

    timeout_s = max(4.0, min(REC_BUDGET_S, 26.0))
    client = OpenAI_CLIENT.with_options(timeout=timeout_s)

    for i in range(1, attempts + 1):
        try:
            resp = client.chat.completions.create(
                model=model_local,
                messages=messages,
                temperature=temperature,
                top_p=0.9,
                presence_penalty=0.15,
                frequency_penalty=0.1,
                max_tokens=max_tokens_local
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            es = (str(e) or "").lower()
            if any(t in es for t in ["timeout", "rate limit", "overloaded", "503", "504", "gateway", "temporar"]):
                sleep(min(1.2 * i, 2.5))
                max_tokens_local = max(256, int(max_tokens_local * 0.75))
                if i == attempts - 1 and model_local != CHAT_MODEL_FALLBACK:
                    model_local = CHAT_MODEL_FALLBACK
                continue
            break
    raise RuntimeError(f"LLM call failed after retries: {last_err}")

# ========= PUBLIC API =========
def generate_sport_recommendation(answers: Dict[str, Any],
                                  lang: str = "العربية",
                                  user_id: str = "N/A",
                                  job_id: str = "") -> List[str]:
    t0 = perf_counter()

    # ✅ كاش (اختياري) — من memory_cache إن وُجد
    try:
        from core.memory_cache import get_cached_recommendation, save_cached_recommendation
    except Exception:
        get_cached_recommendation = None
        save_cached_recommendation = None

    if callable(get_cached_recommendation):
        try:
            cached_cards = get_cached_recommendation(user_id, answers, lang)
            if cached_cards:
                _dbg("cache HIT for recommendations")
                _job_note(job_id, 100, "جاهزة ✅ (من الكاش)", "done")
                return cached_cards
        except Exception:
            pass

    _dbg("cache MISS for recommendations")
    _job_note(job_id, 10, "جمع الإشارات الأولية…", "running")

    # Evidence Gate
    eg = _run_egate(answers or {}, lang=lang)
    if _PIPE:
        try:
            _PIPE.send(
                event_type="egate_decision",
                payload={
                    "status": eg.get("status"),
                    "answered": eg.get("answered"),
                    "total_chars": eg.get("total_chars"),
                    "required_missing": eg.get("required_keys", []) or eg.get("required_missing", []),
                    "job_id": job_id
                },
                user_id=user_id, lang=("العربية" if lang=="العربية" else "English"),
                model=CHAT_MODEL
            )
        except Exception:
            pass

    if eg.get("status") != "pass":
        card = _format_followup_card(eg.get("followup_questions", []), lang=lang)
        try:
            sec = (CFG.get("security") or {})
            if sec.get("scrub_urls", True):
                card = scrub_unknown_urls(card, CFG)
        except Exception:
            pass
        _job_note(job_id, 100, "نحتاج إجابات إضافية", "done")
        return [_norm_text(card), "—", "—"]

    _job_note(job_id, 20, "تحليل الإجابات وبناء المحاور…")

    # تحليل المستخدم + طبقة Z + Intent + profile
    analysis: Dict[str, Any] = _call_analyze_user_from_answers(user_id, answers, lang)
    try:
        # silent drivers
        for modpath in ("core.layer_z_engine", "analysis.layer_z_engine"):
            try:
                mod = importlib.import_module(modpath)
                if hasattr(mod, "analyze_silent_drivers_combined"):
                    analysis["silent_drivers"] = mod.analyze_silent_drivers_combined(answers, lang=lang) or []
                    break
            except Exception:
                pass
        if "silent_drivers" not in analysis:
            analysis["silent_drivers"] = []
    except Exception:
        analysis["silent_drivers"] = []

    try:
        z_intent = _call_analyze_intent(answers, lang=lang) or []
        if z_intent:
            analysis["z_intent"] = z_intent
    except Exception:
        pass

    profile = _extract_profile(answers, lang)
    if profile:
        analysis["encoded_profile"] = profile
        if "axes" in profile: analysis["z_axes"] = profile["axes"]
        if "scores" in profile: analysis["z_scores"] = profile["scores"]

    # ======== KB-first (priors + trait_links + guards + templates) ========
    user_axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    user_signals = _extract_signals(answers, lang)

    def _derive_binary_traits(analysis: Dict[str, Any], answers: Dict[str, Any], lang: str) -> Dict[str, float]:
        traits: Dict[str, float] = {}
        prof = (analysis or {}).get("encoded_profile") or {}
        axes = (prof or {}).get("axes") or {}
        silent = set(map(str, (analysis or {}).get("silent_drivers") or []))

        sig = _extract_signals(answers, lang)

        sg = float(axes.get("solo_group", 0.0)) if isinstance(axes, dict) else 0.0
        if sg <= -0.35: traits["introvert"] = 1.0; traits["prefers_solo"] = 1.0
        if sg >=  0.35: traits["extrovert"] = 1.0; traits["prefers_team"] = 1.0
        if sig.get("solo_pref"): traits["prefers_solo"] = max(1.0, traits.get("prefers_solo", 0))
        if sig.get("team_pref"): traits["prefers_team"] = max(1.0, traits.get("prefers_team", 0))

        ca = float(axes.get("calm_adrenaline", 0.0)) if isinstance(axes, dict) else 0.0
        if ca <= -0.35 or sig.get("breath"):
            traits["calm_regulation"] = max(traits.get("calm_regulation", 0.0), 0.8)
        if ca >= 0.35 or sig.get("high_agg"):
            traits["sensation_seeking"] = max(traits.get("sensation_seeking", 0.0), 0.8)

        ti = float(axes.get("tech_intuition", 0.0)) if isinstance(axes, dict) else 0.0
        if ti <= -0.35 or sig.get("precision"):
            traits["precision"] = max(traits.get("precision", 0.0), 0.8)

        if sig.get("stealth"):
            traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
        if sig.get("puzzles"): traits["likes_puzzles"] = 1.0
        if sig.get("combat"): traits["tactical_mindset"] = max(1.0, traits.get("tactical_mindset", 0))
        vr_i = float((prof or {}).get("vr_inclination", 0.0))
        if sig.get("vr") or vr_i >= 0.4:
            traits["vr_inclination"] = max(traits.get("vr_inclination", 0.0), max(vr_i, 0.8))

        if traits.get("calm_regulation", 0) >= 0.8 or traits.get("likes_puzzles", 0) >= 1.0:
            traits["sustained_attention"] = max(traits.get("sustained_attention", 0.0), 0.6)

        ar_blob = _normalize_ar(" ".join(_norm_answer_value(v) for v in (answers or {}).values()).lower())
        if any(w in ar_blob for w in ["قلق","مخاوف","توتر شديد","رهاب","خوف"]):
            traits["anxious"] = 1.0
        if any("نفور" in s or "تكرار" in s for s in silent):
            traits["low_repetition_tolerance"] = 1.0
        if any("انجازات قصيره" in _normalize_ar(s) for s in silent):
            traits["needs_quick_wins"] = 1.0

        return traits

    def _score_candidates_from_links(traits: Dict[str, float]) -> List[Tuple[float, str]]:
        anxious = traits.get("anxious", 0.0) >= 0.8 and GUARDS.get("no_high_risk_for_anxiety", True)

        labels = set(KB_PRIORS.keys())
        for t, mapping in (TRAIT_LINKS or {}).items():
            labels.update(mapping.keys())

        scored: List[Tuple[float, str]] = []
        for label in labels:
            if anxious and label in HIGH_RISK_SPORTS:
                scored.append((-1e9, label))
                continue
            s = float(KB_PRIORS.get(label, 0.0))
            for t_name, strength in traits.items():
                link = (TRAIT_LINKS.get(t_name) or {}).get(label, 0.0)
                if link:
                    s += float(strength) * float(link)
            scored.append((s, label))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def _pick_kb_recommendations(user_axes: Dict[str, Any], user_signals: Dict[str, int], lang: str) -> List[Dict[str, Any]]:
        identities = KB.get("identities")
        if not isinstance(identities, list) or not identities:
            return []
        scored: List[Tuple[float, Dict[str, Any]]] = []
        exp = _axes_expectations(user_axes or {}, lang)
        for rec in identities:
            r = _sanitize_record(rec)
            blob = " ".join([_norm_text(r.get("what_it_looks_like","")),
                             _norm_text(r.get("why_you","")),
                             _norm_text(r.get("first_week",""))]).lower()
            hit = 0
            for words in exp.values():
                if words and any(w.lower() in blob for w in words):
                    hit += 1
            if user_signals.get("precision") and ("precision" in blob or "دقه" in blob): hit += 1
            if user_signals.get("stealth") and ("stealth" in blob or "تخفي" in blob): hit += 1
            scored.append((hit, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scored[:3]]

    # (A) identities من KB إن وجدت
    kb_recs = _pick_kb_recommendations(user_axes, user_signals, lang)

    # (ب) إن لم تكفِ، استخدم trait_links
    if len(kb_recs) < 3 and (KB_PRIORS or TRAIT_LINKS):
        trait_strengths = _derive_binary_traits(analysis, answers, lang)
        ranked = _score_candidates_from_links(trait_strengths)

        picked: List[Dict[str, Any]] = []
        used = set()
        for _, lbl in ranked:
            if len(picked) >= 3: break
            # حاول جلب قالب محدّد لهذا الـ label، وإلا فالـ fallback
            tpl = _template_for_label(lbl, lang)
            if not tpl:
                tpl = _fallback_identity(len(picked), lang)
            # dedupe على مستوى الاختيار المحلي
            sig = _sig_for_rec(tpl)
            if any(_jaccard(sig, _sig_for_rec(x)) > 0.6 for x in picked):
                continue
            picked.append(tpl)
            used.add(lbl)
        kb_recs.extend(picked)
        kb_recs = kb_recs[:3]

    # ======== مسار KB مكتمل ========
    if len(kb_recs) >= 3:
        kb_recs = _sanitize_fill(kb_recs, lang)
        bl = _load_blacklist()
        kb_recs = _ensure_unique_labels_v_global(kb_recs, lang, bl)
        _persist_blacklist(kb_recs, bl)

        cards = [_format_card(kb_recs[i], i, lang) for i in range(3)]

        # تنظيف الروابط غير المعروفة إن طُلِب
        try:
            sec = (CFG.get("security") or {})
            if sec.get("scrub_urls", True):
                cards = [scrub_unknown_urls(c, CFG) for c in cards]
        except Exception:
            pass

        # إحفظ بالكاش إن متاح
        if callable(get_cached_recommendation) and callable(save_cached_recommendation):
            try:
                save_cached_recommendation(user_id, answers, lang, cards)
            except Exception:
                pass

        _job_note(job_id, 100, "جاهزة ✅", "done")
        return cards

    # ======== LLM كآخر خيار ========
    if OpenAI_CLIENT is None:
        _job_note(job_id, 100, "تعذّر استدعاء النموذج", "error")
        return [
            "❌ لا يمكن استدعاء النموذج الآن. ثبّت OPENAI_API_KEY (أو OPENROUTER_API_KEY/AZURE_OPENAI_API_KEY) على الخادم وأعد التشغيل.",
            "—",
            "—"
        ]

    # شخصية المدرب (كاش خفيف)
    try:
        from core.memory_cache import get_cached_personality, save_cached_personality
    except Exception:
        get_cached_personality = None
        save_cached_personality = None

    persona = None
    if callable(get_cached_personality):
        try:
            persona = get_cached_personality(analysis, lang=lang)
        except Exception:
            persona = None
    if not persona:
        persona = {
            "name":"SportSync Coach",
            "tone":"حازم-هادئ" if lang=="العربية" else "calm-firm",
            "style":"حسّي واقعي إنساني" if lang=="العربية" else "sensory, grounded, human",
            "philosophy":"هوية حركة بلا أسماء مع وضوح هويّة" if lang=="العربية" else "clear movement identity, minimal labels"
        }
        if callable(save_cached_personality):
            try:
                save_cached_personality(analysis, persona, lang=lang)
            except Exception:
                pass

    seed = _style_seed(user_id, analysis.get("encoded_profile") or {})
    msgs = _json_prompt(analysis, answers, persona, lang, seed)
    max_toks_1 = 800 if REC_FAST_MODE else 1200

    _job_note(job_id, 40, "جولة النموذج الأولى…")
    try:
        _dbg("calling LLM - round #1")
        raw1 = _chat_with_retry(messages=msgs, max_tokens=max_toks_1, temperature=0.5)
        _dbg(f"round #1 ok, len={len(raw1)}")
    except Exception as e:
        err = f"❌ خطأ اتصال النموذج: {e}"
        _job_note(job_id, 100, "خطأ في الاتصال بالنموذج", "error")
        if _PIPE:
            try:
                _PIPE.send("model_error", {"error": str(e), "job_id": job_id},
                           user_id=user_id, lang=lang, model=CHAT_MODEL)
            except Exception:
                pass
        return [err, "—", "—"]

    raw1 = _strip_code_fence(raw1)
    if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw1):
        raw1 = _mask_names(raw1)
    parsed = _parse_json(raw1) or []
    cleaned = _sanitize_fill(parsed, lang)

    elapsed = perf_counter() - t0
    time_left = REC_BUDGET_S - elapsed
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}

    mismatch_axes = any(_mismatch_with_axes(rec, axes, lang) for rec in cleaned)
    need_repair_generic = any(
        _too_generic(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("why_you",""))]),
            _MIN_CHARS
        ) for c in cleaned
    )
    missing_fields = any(
        ((_REQUIRE_WIN and not c.get("win_condition"))
         or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS)
        for c in cleaned
    )
    need_repair = (mismatch_axes or need_repair_generic or missing_fields) \
                  and REC_REPAIR_ENABLED and (time_left >= (6 if not REC_FAST_MODE else 4))

    if need_repair:
        exp = _axes_expectations(axes or {}, lang)
        align_hint = ""
        if exp:
            if lang == "العربية":
                align_hint = (
                    "حاذِ التوصيات مع محاور Z:\n"
                    f"- هدوء/أدرينالين: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- فردي/جماعي: {', '.join(exp.get('solo_group', []))}\n"
                    f"- تقني/حدسي: {', '.join(exp.get('tech_intuition', []))}\n"
                )
            else:
                align_hint = (
                    "Align with Z-axes:\n"
                    f"- Calm/Adrenaline: {', '.join(exp.get('calm_adrenaline', []))}\n"
                    f"- Solo/Group: {', '.join(exp.get('solo_group', []))}\n"
                    f"- Technical/Intuitive: {', '.join(exp.get('tech_intuition', []))}\n"
                )
        repair_prompt = {
            "role":"user",
            "content":(
                ("أعد صياغة التوصيات بنبرة إنسانية وواضحة (اسم رياضة مسموح). " if lang=="العربية"
                 else "Rewrite with a warm, human tone (sport names allowed). ")
                + "تأكد من وجود: sport_label, what_it_looks_like, win_condition, 3–5 core_skills, mode, variant_vr, variant_no_vr. "
                + "ممنوع الوقت/التكلفة/العدّات/الجولات/الدقائق/المكان المباشر. "
                + "حسّن محاذاة Z-axes. JSON فقط.\n\n" + align_hint
            )
        }
        _job_note(job_id, 70, "تحسين وضبط الهوية…")
        try:
            _dbg("calling LLM - round #2 (repair)")
            raw2 = _chat_with_retry(
                messages=msgs + [{"role":"assistant","content":raw1}, repair_prompt],
                max_tokens=(650 if REC_FAST_MODE else 950),
                temperature=0.55
            )
            raw2 = _strip_code_fence(raw2)
            if not ALLOW_SPORT_NAMES and _contains_blocked_name(raw2):
                raw2 = _mask_names(raw2)
            parsed2 = _parse_json(raw2) or []
            cleaned2 = _sanitize_fill(parsed2, lang)

            def score(r: Dict[str,Any]) -> int:
                txt = " ".join([
                    _norm_text(r.get("sport_label","")),
                    _norm_text(r.get("what_it_looks_like","")),
                    _norm_text(r.get("inner_sensation","")),
                    _norm_text(r.get("why_you","")),
                    _norm_text(r.get("first_week","")),
                    _norm_text(r.get("win_condition",""))
                ])
                bonus = 5 * len(r.get("core_skills") or [])
                return len(txt) + bonus

            if sum(map(score, cleaned2)) > sum(map(score, cleaned)):
                cleaned = cleaned2
                _dbg("repair improved result")
        except Exception as e:
            _dbg(f"repair skipped due to error: {e}")

    bl = _load_blacklist()
    cleaned = _ensure_unique_labels_v_global(cleaned, lang, bl)
    _persist_blacklist(cleaned, bl)

    # تحويلها لبطاقات نصية
    cards = [_format_card(cleaned[i], i, lang) for i in range(3)]

    # تنظيف أي روابط غير معروفة (حسب الإعدادات)
    try:
        sec = (CFG.get("security") or {})
        if sec.get("scrub_urls", True):
            cards = [scrub_unknown_urls(c, CFG) for c in cards]
    except Exception:
        pass

    # حفظ الكاش (إن متاح)
    if callable(get_cached_recommendation) and callable(save_cached_recommendation):
        try:
            save_cached_recommendation(user_id, answers, lang, cards)
        except Exception:
            pass

    # لوج جودة داخلي (يعتمد على cleaned)
    axes = (analysis.get("z_axes") or {}) if isinstance(analysis, dict) else {}
    quality_flags = {
        "generic": any(_too_generic(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("why_you",""))]),
            _MIN_CHARS) for c in cleaned),
        "low_sensory": any(not _has_sensory(
            " ".join([_norm_text(c.get("what_it_looks_like","")),
                      _norm_text(c.get("inner_sensation",""))])) for c in cleaned),
        "mismatch_axes": any(_mismatch_with_axes(c, axes, lang) for c in cleaned),
        "missing_fields": any(((_REQUIRE_WIN and not c.get("win_condition"))
                               or len(c.get("core_skills") or []) < _MIN_CORE_SKILLS) for c in cleaned)
    }

    try:
        log_user_insight(
            user_id=user_id,
            content={
                "language": lang,
                "answers": {k: v for k, v in (answers or {}).items() if k != "profile"},
                "analysis": analysis,
                "recommendations": cleaned,
                "quality_flags": quality_flags,
                "seed": seed,
                "elapsed_s": round(perf_counter() - t0, 3),
                "fast_mode": REC_FAST_MODE,
                "job_id": job_id
            },
            event_type="initial_recommendation"
        )
    except Exception:
        pass

    _job_note(job_id, 100, "جاهزة ✅", "done")
    return cards


# ========= واجهة بناء مهمّة + رابط متابعة =========
def start_recommendation_job(answers: Dict[str, Any],
                             lang: str = "العربية",
                             user_id: str = "N/A") -> Dict[str, str]:
    """
    ينشئ Job ويشغّل generate_sport_recommendation في خيط منفصل.
    يعيد: {"job_id": "...", "status_url": "..."}
    """
    job = create_job({"user_id": user_id, "lang": lang})
    jid = job.get("id", "")
    # شغّل المهمة بالخلفية
    run_in_thread(jid, generate_sport_recommendation, answers, lang, user_id, job_id=jid)
    # ابني رابط المتابعة
    base = (os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/") or "https://sportsync-ai-quiz.onrender.com"
    return {"job_id": jid, "status_url": f"{base}?job={jid}"}
