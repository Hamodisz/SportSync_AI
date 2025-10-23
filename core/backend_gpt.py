# -- coding: utf-8 --
import os, json, math, random, time
from typing import Dict, Any, List, Tuple

try:
    from core.llm_client import make_llm_client, pick_models, chat_once
except Exception:
    make_llm_client = lambda: None
    pick_models = lambda: ("", "")
    chat_once = None  # type: ignore

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    def analyze_silent_drivers(answers: Dict[str, Any], lang: str = "العربية"):
        return ["محفّز تكتيكي", "استكشاف حسي", "متعة تحدّي سريعة"]

def _flags():
    def _t(x): return str(os.getenv(x, "")).strip().lower() in ("1","true","yes","on")
    return {
        "FORCE_LOCAL_FALLBACK": _t("FORCE_LOCAL_FALLBACK"),
        "DISABLE_LLM": _t("DISABLE_LLM"),
        "CHAT_MODEL": os.getenv("CHAT_MODEL", ""),
        "OPENAI_BASE_URL": os.getenv("OPENAI_BASE_URL", ""),
        "GROQ_API_KEY_set": bool(os.getenv("GROQ_API_KEY")),
        "OPENAI_API_KEY_set": bool(os.getenv("OPENAI_API_KEY")),
        "OPENROUTER_API_KEY_set": bool(os.getenv("OPENROUTER_API_KEY")),
    }

def _should_use_local(client):
    f = _flags()
    if f["FORCE_LOCAL_FALLBACK"] or f["DISABLE_LLM"]:
        return True, "env_flag"
    if client is None:
        return True, "no_client"
    return False, "llm_available"

def _diagnose():
    client = make_llm_client() if callable(make_llm_client) else None
    use_local, reason = _should_use_local(client)
    try: main, fb = pick_models()
    except Exception: main, fb = ("","")
    return {"mode": "local" if use_local else "llm", "reason": reason, "env": _flags(), "models":{"main":main,"fallback":fb}, "ts": time.time()}

def _pull(answers: Dict[str, Any], key: str):
    cell = answers.get(key, {})
    val = cell.get("answer", cell) if isinstance(cell, dict) else cell
    out = []
    if isinstance(val, str): out = [val.strip()]
    elif isinstance(val, list): out = [str(x).strip() for x in val if str(x).strip()]
    return [x.lower() for x in out if x]

def _score_axis(answers: Dict[str, Any]):
    intent = set(_pull(answers, "intent") + _pull(answers, "q_1") + _pull(answers, "goal"))
    likes  = set(_pull(answers, "likes") + _pull(answers, "q_2"))
    hates  = set(_pull(answers, "hates") + _pull(answers, "q_3"))
    txt = (" ".join(list(intent | likes)) + " ").lower()
    novelty_seek   = 0.2 + 0.6*any(k in txt for k in ["جديد","غامر","vr","تقنية","تجربة","غير تقليدي","مهمات","missions","stealth","parkour"])
    sensory_depth  = 0.2 + 0.6*any(k in txt for k in ["إحساس","صوت","إيقاع","تنفّس","تأمّل","mindful","حسي","flow"])
    tactical_drive = 0.2 + 0.6*any(k in txt for k in ["قرار","تكتيك","مناورة","ضغط","قتال","combat","مهمات"])
    flow_pref      = 0.2 + 0.6*any(k in txt for k in ["هدوء","انسجام","flow","تنفّس","يوغا","بيلاتس","تأمّل"])
    pace           = 3.0 + (1.0 if "سريع" in txt or "hiit" in txt else 0.0) - (1.0 if "هادئ" in txt or "خفيف" in txt else 0.0)
    pace           = max(1.0, min(5.0, pace))
    social = 0.0
    if any(k in txt for k in ["فريق","جماعي","team","خماسية","سلة"]): social += 0.8
    if any(k in txt for k in ["وحدي","فردي","solo"]):                   social -= 0.8
    social = max(-1.0, min(1.0, social))
    io = 0.0
    if any(k in txt for k in ["هواء طلق","outdoor","حديقة","ممشى"]): io += 0.7
    if any(k in txt for k in ["صالات","indoor","نادي"]):             io -= 0.7
    io = max(-1.0, min(1.0, io))
    if any(k in hates for k in ["ملل","روتين","تكرار"]): novelty_seek = max(novelty_seek, 0.7)
    if any(k in hates for k in ["ازدحام","زحمة"]): social = min(social, 0.0)
    return {k: float(round(v,2)) for k,v in dict(novelty_seek=novelty_seek, sensory_depth=sensory_depth, tactical_drive=tactical_drive, flow_pref=flow_pref, pace=pace, social=social, indoor_outdoor=io).items()}

def _compose_cards(ax, z_axes, lang):
    is_ar = (lang == "العربية")
    def _name1():
        if ax["tactical_drive"]>0.6 and ax["novelty_seek"]>0.6: return "قتال تكتيكي غامر" if is_ar else "Tactical Immersive Combat"
        if ax["flow_pref"]>0.6 and ax["sensory_depth"]>0.6:     return "مهمات تدفّق خفي" if is_ar else "Stealth-Flow Missions"
        return "عبور ميداني إيقاعي" if is_ar else "Rhythmic Field Traverse"
    def _name2():
        return ("حلقة باركور حضرية" if is_ar else "Urban Parkour Loop") if ax["indoor_outdoor"]>=0.4 else ("دائرة مرونة داخل الاستوديو" if is_ar else "Studio Mobility Circuit")
    def _name3():
        return ("مختبر حسّي بالواقع الافتراضي (بدون قتال)" if is_ar else "VR Sense-Lab (no-combat)") if ax["novelty_seek"]>0.5 else ("مزيج خفّة ذهني" if is_ar else "Mindful Agility Blend")
    def blurb(title):
        if is_ar:
            L=[f"• لماذا {title}: مواءمة لمحوري Z: {'، '.join(z_axes[:2])}.",
               f"• السرعة: {int(round(ax['pace']))}/5 — {'هواء طلق' if ax['indoor_outdoor']>0 else 'داخل الصالات'}.",
               f"• النمط الاجتماعي: {'فريق/ازدواج' if ax['social']>0.3 else ('فردي' if ax['social']<-0.3 else 'مختلط')}.",
               "• مؤشرات حسية: تنفّس/صوت/لمس مضبوطة للحفاظ على المتعة."]
            return "\n".join(L)
        else:
            L=[f"• Why {title}: maps to your Z-axes: {', '.join(z_axes[:2])}.",
               f"• Pace: {int(round(ax['pace']))}/5 — {'outdoor' if ax['indoor_outdoor']>0 else 'indoor'}.",
               f"• Social: {'team/duo' if ax['social']>0.3 else ('solo' if ax['social']<-0.3 else 'hybrid')}.",
               "• Sensory cues tuned for sustained enjoyment."]
            return "\n".join(L)
    titles=[_name1(),_name2(),_name3()]
    headers_ar=["🟢 التوصية رقم 1","🌿 التوصية رقم 2","🔮 التوصية رقم 3 (ابتكارية)"]
    headers_en=["🟢 Recommendation #1","🌿 Recommendation #2","🔮 Recommendation #3 (Creative)"]
    cards=[]
    for i,t in enumerate(titles,1):
        hdr=headers_ar[i-1] if is_ar else headers_en[i-1]
        body=blurb(t)
        plan="• نموذج جلسة: 25–35 دقيقة، 3 مرات/أسبوع. فترات 3–6 دقائق يليها دقيقة تهدئة حسّية." if is_ar else "• Session: 25–35 min, 3×/week. 3–6 min bouts + 1-min sensory downshift."
        cards.append(f"{hdr}\n\n{t}\n\n{body}\n{plan}\n— Sports Sync")
    return cards

def _local_generate(answers, lang):
    ax=_score_axis(answers)
    z=analyze_silent_drivers(answers, lang=lang) or []
    random.seed(json.dumps(ax, sort_keys=True))
    return _compose_cards(ax, z, lang)[:3]

def generate_sport_recommendation(answers, lang="العربية"):
    client = make_llm_client() if callable(make_llm_client) else None
    use_local, reason = _should_use_local(client)
    if use_local or not callable(chat_once):
        return _local_generate(answers, lang)
    try:
        main_chain, fb = pick_models()
    except Exception:
        main_chain, fb = "gpt-4o", "gpt-4o-mini"
    msgs=[{"role":"system","content":"You are SportSync recommender. Avoid weight/time/money. Use psycho-metric axes. Return 3 cards."},
          {"role":"user","content":json.dumps({"answers":answers,"lang":lang}, ensure_ascii=False)}]
    try:
        text=chat_once(client, msgs, model=main_chain, temperature=0.7, max_tokens=900)
        parts=[p.strip() for p in text.split("\n\n") if p.strip()]
        if len(parts)<3: return _local_generate(answers, lang)
        return parts[:3]
    except Exception:
        return _local_generate(answers, lang)

def quick_diagnose():
    d=_diagnose()
    d["sample_axes"]=_score_axis({"intent":{"answer":["sample"]}})
    return d
