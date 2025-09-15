# -- coding: utf-8 --
"""
core/kb_ranker.py
محرك توصيات "معرفية" بدون توليد حر:
- يستخرج سمات المستخدم من الإجابات (AR/EN).
- يرتب الهويات بناءً على priors + trait_links + guards من sportsync_knowledge.json.
- يقرأ قوالب الهويات من data/identities/*.json ويرجع 3 بطاقات فورًا.
"""

from __future__ import annotations
import json, re
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ---------- نص عربي: إزالة التشكيل وتطبيع بسيط ----------
_AR_DIAC = r"[ًٌٍَُِّْـ]"
def _normalize_ar(t: str) -> str:
    if not t: return ""
    import re
    t = re.sub(_AR_DIAC, "", t)
    t = t.replace("أ","ا").replace("إ","ا").replace("آ","ا")
    t = t.replace("ؤ","و").replace("ئ","ي").replace("ة","ه").replace("ى","ي")
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()

def _canon(label: str) -> str:
    if not label: return ""
    t = _normalize_ar(label)
    t = re.sub(r"[^a-z0-9\u0600-\u06FF]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -—:،")
    return t

# ---------- تحميل KB ----------
def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def load_kb(kb_path: Path) -> dict:
    kb = _load_json(kb_path)
    kb.setdefault("priors", {})
    kb.setdefault("trait_links", {})
    kb.setdefault("guards", {})
    kb.setdefault("label_aliases", {})
    kb.setdefault("z_intent_keywords", {"ar":{}, "en":{}})
    # خرائط alias -> canonical
    alias_map = {}
    for canon, aliases in kb.get("label_aliases", {}).items():
        ccanon = _canon(canon)
        for a in aliases or []:
            alias_map[_canon(a)] = ccanon or canon
        alias_map[ccanon] = ccanon
    kb["_alias_map"] = alias_map
    return kb

def resolve_label(label: str, kb: dict) -> str:
    a = _canon(label)
    return kb.get("_alias_map", {}).get(a, a)

# ---------- استخراج سمات من الإجابات ----------
def _blob_from_answers(answers: Dict[str, Any]) -> str:
    parts = []
    for v in (answers or {}).values():
        if isinstance(v, dict):
            if "answer" in v: parts.append(str(v.get("answer") or ""))
            else: parts.append(json.dumps(v, ensure_ascii=False))
        elif isinstance(v, list):
            parts.append(", ".join(map(str, v)))
        else:
            parts.append(str(v))
    return " ".join(str(x) for x in parts)

KW = {
    "ar": {
        "introvert": ["انطوائي","هادي","احب لوحدي","فردي","مااحب الزحمه","قليل كلام"],
        "extrovert": ["اجتماعي","احب الفريق","احب الناس","زحمه","اختلاط","تجمع"],
        "precision": ["دقه","تصويب","نشان","محكم","ضبط","متقن"],
        "sustained_attention": ["تركيز طويل","صبر","تفكير عميق","جلوس طويل","شطرنج"],
        "sensation_seeking": ["مغامره","ادرينالين","سرعه","خطر","قفز","قويه"],
        "calm_regulation": ["هدوء","تنفس","تنفّس","صفاء","يوغا","تنظيم نفس"],
        "tactical_mindset": ["تكتيك","خطة","كمين","خدع","استراتيجي"],
        "likes_puzzles": ["لغز","الغاز","خدعه بصريه","puzzle","احاجي"],
        "prefers_solo": ["فردي","لوحدي","بدون فريق"],
        "prefers_team": ["فريق","جماعي","مع ناس","co-op"],
        "anxious": ["قلق","خائف","رهبه","فوبيا","توتر عالي"],
        "low_repetition_tolerance": ["امل بسرعة","ملل","اكره التكرار","روتين"],
        "needs_quick_wins": ["نتيجه سريعه","نتيجه فوريه","احب الانجاز السريع"],
        "vr_inclination": ["vr","واقع افتراضي","نظاره","افتراضي"],
    },
    "en": {
        "introvert": ["introvert","quiet","alone","solo"],
        "extrovert": ["extrovert","social","team","group","crowd"],
        "precision": ["precision","aim","mark","accurate","steady"],
        "sustained_attention": ["deep focus","long focus","patience","think long"],
        "sensation_seeking": ["adrenaline","thrill","risk","fast","jump"],
        "calm_regulation": ["calm","breath","breathing","yoga","relax"],
        "tactical_mindset": ["tactic","strategic","ambush","plan"],
        "likes_puzzles": ["puzzle","riddle","feint","trick"],
        "prefers_solo": ["solo","alone","individual"],
        "prefers_team": ["team","group","co-op","squad"],
        "anxious": ["anxious","anxiety","fear","phobia","tense"],
        "low_repetition_tolerance": ["bored quickly","hate repetition","monotony"],
        "needs_quick_wins": ["quick win","fast result","immediate"],
        "vr_inclination": ["vr","virtual reality","headset"],
    }
}

def _score_kw(blob: str, words: List[str]) -> float:
    if not words: return 0.0
    hits = 0
    blob_l = blob.lower()
    blob_ar = _normalize_ar(blob)
    for w in words:
        w_l = w.lower()
        if w_l in blob_l or _normalize_ar(w_l) in blob_ar:
            hits += 1
    # تحويل لمدى 0..1 مع حد أقصى بسيط
    return min(1.0, hits / max(2.0, len(words)/2.0))

def extract_traits(answers: Dict[str, Any], lang: str, kb: dict) -> Dict[str, float]:
    # ندمج AR و EN للكشف ثنائي اللغة
    blob = _blob_from_answers(answers)
    traits = {}
    for tname, words in KW["ar"].items():
        traits[tname] = max(_score_kw(blob, words), _score_kw(blob, KW["en"].get(tname, [])))
    # موازنة الثنائيات: introvert/extrovert و solo/team
    if traits["introvert"] > traits["extrovert"]:
        traits["extrovert"] *= 0.5
    elif traits["extrovert"] > traits["introvert"]:
        traits["introvert"] *= 0.5

    if traits["prefers_solo"] > traits["prefers_team"]:
        traits["prefers_team"] *= 0.5
    elif traits["prefers_team"] > traits["prefers_solo"]:
        traits["prefers_solo"] *= 0.5

    return traits

# ---------- ترتيب الأنشطة ----------
def score_labels(traits: Dict[str,float], kb: dict, candidate_labels: List[str]) -> List[Tuple[str,float]]:
    priors: Dict[str,float] = kb.get("priors", {})
    links: Dict[str,Dict[str,float]] = kb.get("trait_links", {})
    guards: Dict[str,Any] = kb.get("guards", {})

    scores = {}
    for raw in candidate_labels:
        lab = resolve_label(raw, kb)
        base = float(priors.get(lab, 0.03))
        s = base
        for t, tscore in traits.items():
            w = float(links.get(t, {}).get(lab, 0.0))
            if w != 0.0 and tscore > 0:
                s += tscore * w
        scores[lab] = s

    # حرس: القلق العالي ورياضات عالية المخاطر
    anxious = traits.get("anxious", 0.0)
    if guards.get("no_high_risk_for_anxiety", True) and anxious >= 0.5:
        for hr in guards.get("high_risk_sports", []):
            lab = resolve_label(hr, kb)
            if lab in scores:
                scores[lab] = max(0.0, scores[lab] - 1.5)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ranked

# ---------- قراءة هوية + توليد بطاقة ----------
def _pick_lang(val: Any, lang: str) -> Any:
    # يدعم { "ar": "...", "en": "..." } أو نص مباشر
    if isinstance(val, dict):
        return val.get("ar") if lang == "العربية" else val.get("en")
    return val

def _to_list(val: Any, lang: str) -> List[str]:
    v = _pick_lang(val, lang)
    if isinstance(v, list): return v
    if isinstance(v, str):  # يفصل على السطر أو الفواصل
        parts = re.split(r"[,\n،]+", v)
        return [p.strip(" -•\t") for p in parts if p.strip()]
    return []

def load_identity(label: str, lang: str, identities_dir: Path, kb: dict) -> Dict[str, Any]:
    lab = resolve_label(label, kb)
    path = (identities_dir / f"{lab}.json")
    data = _load_json(path)
    if not data:
        return {}
    # حزم الحقول باللّغة المطلوبة
    out = {
        "sport_label": _pick_lang(data.get("sport_label",""), lang) or "",
        "what_it_looks_like": _pick_lang(data.get("what_it_looks_like",""), lang) or "",
        "inner_sensation": _pick_lang(data.get("inner_sensation",""), lang) or "",
        "why_you": _pick_lang(data.get("why_you",""), lang) or "",
        "first_week": _pick_lang(data.get("first_week",""), lang) or "",
        "progress_markers": _pick_lang(data.get("progress_markers",""), lang) or "",
        "win_condition": _pick_lang(data.get("win_condition",""), lang) or "",
        "core_skills": _to_list(data.get("core_skills",[]), lang),
        "mode": _pick_lang(data.get("mode","Solo"), lang) or "Solo",
        "variant_vr": _pick_lang(data.get("variant_vr",""), lang) or "",
        "variant_no_vr": _pick_lang(data.get("variant_no_vr",""), lang) or "",
        "difficulty": int(data.get("difficulty", 3)),
    }
    return out

def _one_liner(*parts: str, max_len: int = 140) -> str:
    s = " — ".join(str(p).strip() for p in parts if p and str(p).strip())
    return s[:max_len]

def _bullets(text: str, max_items: int = 6) -> List[str]:
    items = _to_list(text, "العربية") if isinstance(text, dict) else _to_list(text, "en")
    if not items and isinstance(text, str):
        items = [text.strip()]
    return items[:max_items] if items else []

def render_card(rec: Dict[str,Any], idx: int, lang: str) -> str:
    head_ar = ["🟢 التوصية رقم 1","🌿 التوصية رقم 2","🔮 التوصية رقم 3 (ابتكارية)"]
    head_en = ["🟢 Recommendation 1","🌿 Recommendation 2","🔮 Recommendation 3 (Creative)"]
    head = (head_ar if lang == "العربية" else head_en)[idx]

    label = rec.get("sport_label","").strip()
    scene = rec.get("what_it_looks_like","").strip()
    inner = rec.get("inner_sensation","").strip()
    why   = rec.get("why_you","").strip()
    week  = _bullets(rec.get("first_week",""), 6)
    prog  = _bullets(rec.get("progress_markers",""), 4)
    win   = rec.get("win_condition","").strip()
    skills= rec.get("core_skills", [])[:5]
    diff  = rec.get("difficulty", 3)
    mode  = (rec.get("mode") or "").strip()
    vr    = (rec.get("variant_vr") or "").strip()
    novr  = (rec.get("variant_no_vr") or "").strip()

    intro = _one_liner(scene, inner)

    if lang == "العربية":
        out = [head, ""]
        if label: out.append(f"🎯 الهوية المثالية لك: {label}")
        if intro: out += ["\n💡 ما هي؟", f"- {intro}"]
        if why:
            out += ["\n🎮 ليه تناسبك؟"]
            for b in _bullets(why, 4) or [why]: out.append(f"- {b}")
        if skills:
            out += ["\n🧩 مهارات أساسية:"] + [f"- {s}" for s in skills]
        if win: out += ["\n🏁 كيف تفوز؟", f"- {win}"]
        if week: out += ["\n🚀 أول أسبوع (نوعي):"] + [f"- {b}" for b in week]
        if prog: out += ["\n✅ علامات تقدم محسوسة:"] + [f"- {b}" for b in prog]
        notes = []
        if mode: notes.append(("وضع اللعب: " + mode))
        if novr: notes.append("بدون VR: " + novr)
        if vr: notes.append("VR (اختياري): " + vr)
        if notes: out += ["\n👁‍🗨 ملاحظات:", f"- " + "\n- ".join(str(x) for x in notes)]
        out.append(f"\nالمستوى التقريبي: {diff}/5")
        return "\n".join(str(x) for x in out)
    else:
        out = [head, ""]
        if label: out.append(f"🎯 Ideal identity: {label}")
        if intro: out += ["\n💡 What is it?", f"- {intro}"]
        if why:
            out += ["\n🎮 Why you"]
            for b in _bullets(why, 4) or [why]: out.append(f"- {b}")
        if skills:
            out += ["\n🧩 Core skills:"] + [f"- {s}" for s in skills]
        if win: out += ["\n🏁 Win condition", f"- {win}"]
        if week: out += ["\n🚀 First week (qualitative)"] + [f"- {b}" for b in week]
        if prog: out += ["\n✅ Progress cues"] + [f"- {b}" for b in prog]
        notes = []
        if mode: notes.append(("Mode: " + mode))
        if novr: notes.append("No-VR: " + novr)
        if vr: notes.append("VR (optional): " + vr)
        if notes: out += ["\n👁‍🗨 Notes:", f"- " + "\n- ".join(str(x) for x in notes)]
        out.append(f"\nApprox level: {diff}/5")
        return "\n".join(str(x) for x in out)

# ---------- نقطة الدخول ----------
def rank_and_render(answers: Dict[str,Any], lang: str,
                    kb_path: Path, identities_dir: Path,
                    top_k: int = 3) -> List[str]:
    kb = load_kb(kb_path)
    traits = extract_traits(answers, lang, kb)

    # نرشّح المرشحين إلى الموجودين فعليًا في identities_dir
    available = []
    for p in identities_dir.glob("*.json"):
        available.append(p.stem)

    ranked = score_labels(traits, kb, available)
    if not ranked:
        return ["—","—","—"]

    # نختار أعلى 3 موجودة ونبني بطاقات
    cards: List[str] = []
    picked = 0
    for lab, _ in ranked:
        rec = load_identity(lab, lang, identities_dir, kb)
        if not rec: continue
        cards.append(render_card(rec, picked, lang))
        picked += 1
        if picked >= top_k:
            break

    # لو ما كفت، نكمّل بأي قوالب متاحة
    while picked < top_k and available:
        rec = load_identity(available[picked % len(available)], lang, identities_dir, kb)
        if rec:
            cards.append(render_card(rec, picked, lang))
            picked += 1
        else:
            break

    # ضمان 3 عناصر
    while len(cards) < 3: cards.append("—")
    return cards
