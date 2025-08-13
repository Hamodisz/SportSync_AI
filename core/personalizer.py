# core/personalizer.py
# -- coding: utf-8 --
from _future_ import annotations
from typing import Dict, List

# أسئلة مبسطة (EN)؛ نقدر نضيف نسخة عربية لاحقاً
INTENT_QUESTIONS: List[Dict] = [
    {"key": "goal", "q": "Your primary goal?", "choices": ["Lose weight", "Build muscle", "Stress relief", "Discipline/consistency"]},
    {"key": "env",  "q": "Preferred environment?", "choices": ["Outdoors", "Indoors", "Team-based", "Solo"]},
    {"key": "impact","q":"Impact level you’re ok with?", "choices": ["Low", "Moderate", "High"]},
    {"key": "time", "q":"Time per session?", "choices": ["10–20m", "20–40m", "40–60m"]},
    {"key": "vibe", "q":"What vibe motivates you?", "choices": ["Calm", "Energetic", "Competitive", "Mindful"]},
]

def score_answers(ans: Dict[str, str]) -> Dict[str, float]:
    """طبقة Z مبسطة: نحول الإجابات لإشارات (vectors)"""
    s = dict(cardio=0.0, strength=0.0, mindfulness=0.0, teamplay=0.0, outdoor=0.0, low_impact=0.0)
    if ans.get("goal") == "Lose weight": s["cardio"] += 1.0
    if ans.get("goal") == "Build muscle": s["strength"] += 1.0
    if ans.get("goal") == "Stress relief": s["mindfulness"] += 1.0
    if ans.get("goal") == "Discipline/consistency": s["mindfulness"] += 0.5

    if ans.get("env") == "Outdoors": s["outdoor"] += 1.0
    if ans.get("env") == "Team-based": s["teamplay"] += 1.0

    if ans.get("impact") == "Low": s["low_impact"] += 1.0
    if ans.get("impact") == "High": s["cardio"] += 0.5; s["strength"] += 0.5

    if ans.get("vibe") == "Calm": s["mindfulness"] += 0.5
    if ans.get("vibe") == "Energetic": s["cardio"] += 0.5
    if ans.get("vibe") == "Competitive": s["teamplay"] += 0.5

    return s

def pick_sport(scores: Dict[str, float]) -> str:
    """اختيار رياضة مرشحة"""
    # قواعد بسيطة
    if scores["teamplay"] > 0.6 and scores["cardio"] >= 0.5: return "football"
    if scores["cardio"] >= scores["strength"] and scores["outdoor"] >= 0.5: return "running"
    if scores["low_impact"] >= 0.8: return "swimming"
    if scores["strength"] > scores["cardio"]: return "weightlifting"
    if scores["mindfulness"] >= 1.0: return "yoga"
    return "running"

def build_profile(ans: Dict[str, str]) -> Dict:
    sc = score_answers(ans)
    sport = pick_sport(sc)
    tone = "calm" if ans.get("vibe") in ["Calm","Mindful"] else "energetic"
    return {"scores": sc, "sport": sport, "tone": tone}
