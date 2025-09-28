# tools/project_script_builder.py
import os, json, re, pathlib, random
from typing import Dict, Any, List
from tools.deepseek_client import chat

# ---- Safe loaders ----------------------------------------------------------
def load_json(p: str, default):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def pick_first_file(folder: str, name_starts: str, fallback: str = "") -> str:
    try:
        path = pathlib.Path(folder)
        for fp in path.glob("*.json"):
            if fp.name.lower().startswith(name_starts.lower()):
                return str(fp)
    except Exception:
        pass
    return fallback

# ---- Context collectors (use your existing project structure) --------------
def collect_analysis(answers: Dict[str, Any], lang: str = "العربية") -> Dict[str, Any]:
    analysis = {}
    # 1) Layer-Z + user analysis if available
    try:
        from analysis.user_analysis import analyze_user_from_answers
        try:
            analysis.update(analyze_user_from_answers(user_id=answers.get("user_id","N/A"),
                                                      answers=answers, lang=lang) or {})
        except TypeError:
            analysis.update(analyze_user_from_answers(answers) or {})
    except Exception:
        pass

    try:
        from analysis.layer_z_engine import analyze_silent_drivers, analyze_user_intent
        try:
            analysis["silent_drivers"] = analyze_silent_drivers(answers, lang=lang) or []
        except Exception:
            analysis["silent_drivers"] = []
        try:
            analysis["z_intent"] = analyze_user_intent(answers, lang=lang) or []
        except Exception:
            analysis.setdefault("z_intent", [])
    except Exception:
        analysis.setdefault("silent_drivers", [])
        analysis.setdefault("z_intent", [])

    # encoded profile if your encoder exists
    try:
        from core.answers_encoder import encode_answers
        enc = encode_answers(answers, lang=lang)
        analysis["encoded_profile"] = enc
        if isinstance(enc, dict) and "axes" in enc:
            analysis["z_axes"] = enc["axes"]
    except Exception:
        pass
    return analysis

def load_client_profile(client_id: str) -> Dict[str, Any]:
    # You can add more client files later
    p = f"data/clients/{client_id}.json"
    profile = load_json(p, {})
    # tone template file if provided by name
    tone_file = profile.get("tone_template_file")
    if not tone_file:
        # Try one of your existing tone templates
        # e.g. agents/marketing/tone_templates/raw_rebellion.json
        maybe = pick_first_file("agents/marketing/tone_templates", profile.get("tone","") or "raw_rebellion")
        tone_file = maybe or "agents/marketing/tone_templates/raw_rebellion.json"
    profile["tone_template"] = load_json(tone_file, {})
    return profile

def load_facts() -> List[str]:
    facts = load_json("data/facts/sportsync_facts.json", [])
    if isinstance(facts, dict) and "facts" in facts:
        facts = facts["facts"]
    facts = [str(x) for x in facts][:10]  # keep it short
    return facts

def load_answers_for_client(client_id: str) -> Dict[str, Any]:
    # Hook in the future: read from your CRM or user_sessions.csv
    # For now a minimal stub:
    return {
        "user_id": client_id,
        "goals": "grow YouTube via sport-identity insights",
        "style": "calm-technical with stealth flow"
    }

# ---- Prompt builder --------------------------------------------------------
def build_prompts(context: Dict[str, Any], topic: str, vid_type: str, n_scenes: int) -> (str, str):
    tone = context.get("client", {}).get("tone_template", {})
    brand_rules = context.get("client", {}).get("hard_rules", [])
    z_axes = context.get("analysis", {}).get("z_axes", {})
    silent = context.get("analysis", {}).get("silent_drivers", [])
    z_intent = context.get("analysis", {}).get("z_intent", [])
    facts = context.get("facts", [])[:8]

    # System prompt
    sys_p = (
        "You are SportSync's senior scriptwriter. "
        "Write YouTube scripts that are original, concrete, and sensory. "
        "Avoid explicit time/cost/tool/venue details. "
        "Output strict JSON only."
    )

    # Derive tone hints
    tone_name = tone.get("name","Raw Rebellion")
    tone_keys = ", ".join(tone.get("keywords", [])[:6])

    user_p = f"""
Compose a {vid_type} YouTube video script about: "{topic}".

Brand tone: {tone_name}; keys: {tone_keys}
Z-axes: {json.dumps(z_axes, ensure_ascii=False)}
Silent drivers: {", ".join(map(str, silent)) or "-"}
Z-intent: {", ".join(map(str, z_intent)) or "-"}
Facts: {facts if facts else "-"}

Rules:
- No mentions of time/cost/sets/reps/venue/gear.
- Keep each scene 'line' <= 14 words, catchy and specific.
- Use sensory words when possible (breath, balance, angle, flow…).
- Must return EXACT JSON with keys: title, scenes[]. Each scene: visual, line.
- scenes length must be {n_scenes}

Return JSON only.
"""
    return sys_p, user_p

# ---- Public API ------------------------------------------------------------
def generate_script(topic: str, vid_type: str, client_id: str = "default") -> Dict[str, Any]:
    n_scenes = 12 if vid_type == "long" else 6
    answers = load_answers_for_client(client_id)
    analysis = collect_analysis(answers, lang="العربية")
    client = load_client_profile(client_id)
    facts = load_facts()
    context = {"client": client, "analysis": analysis, "facts": facts}

    sys_p, user_p = build_prompts(context, topic, vid_type, n_scenes)
    raw = chat(system_prompt=sys_p, user_prompt=user_p, temperature=0.7, max_tokens=1600)

    # Extract JSON
    m = re.search(r"\{[\s\S]*\}", raw)
    data = json.loads(m.group(0)) if m else json.loads(raw)
    scenes = (data.get("scenes") or [])[:n_scenes]
    if len(scenes) < n_scenes:
        # pad simple lines if needed
        for i in range(len(scenes), n_scenes):
            scenes.append({"visual": f"{topic} — atmospheric cut {i+1}", "line":"Calm control • clear angle"})
    data["scenes"] = scenes
    data["title"] = data.get("title") or f"{topic} — SportSync cut"
    return data
