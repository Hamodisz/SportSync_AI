# content_studio/generators/script_templates.py
# -- coding: utf-8 --
from _future_ import annotations
import os
from typing import Dict

TEMPLATES = {
    ("running","energetic"): """Title: Your first run today
Scene 1: Lacing shoes — "Every finish line starts with this."
Scene 2: First breath outside — "Fresh air. Fresh start."
Scene 3: Steps finding rhythm — "Consistency beats perfection."
Outro: 10 minutes. Start now.""",
    ("running","calm"): """Title: A quiet run
Scene 1: Sunrise path — "Breathe. Begin."
Scene 2: Footsteps soft — "Small steps. Big change."
Scene 3: Heart steady — "You’re doing great."
Outro: Give it 10 minutes today.""",
    ("football","energetic"): """Title: Join the game
Scene 1: Passing the ball — "Teamwork builds momentum."
Scene 2: Quick sprint — "Push. Laugh. Repeat."
Scene 3: Net shaking — "You belong on the field."
Outro: Grab a friend and play 10 minutes."""
}

def _openai_rewrite(text: str) -> str:
    """تحسين اختياري عبر OpenAI إن توفر المفتاح."""
    try:
        from openai import OpenAI
        api = os.getenv("OPENAI_API_KEY")
        if not api: return text
        client = OpenAI(api_key=api)
        prompt = f"Rewrite this short video script in 4 scenes, keep meaning, keep it motivational and concise:\n{text}"
        r = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return text

def build_script(profile: Dict, lang: str="en", use_ai: bool=True) -> str:
    sport = profile.get("sport","running")
    tone  = profile.get("tone","energetic")
    txt = TEMPLATES.get((sport, tone))
    if not txt:
        txt = TEMPLATES[("running","energetic")]
    if use_ai:
        txt = _openai_rewrite(txt)
    # ترجمة بسيطة للعربية لاحقاً (نقدر نضيف قوالب AR)
    return txt if lang=="en" else txt
