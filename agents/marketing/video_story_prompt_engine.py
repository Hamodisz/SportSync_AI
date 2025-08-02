# agents/marketing/video_story_prompt_engine.py

import json
import os
from strategy.strategic_moat_plan import MOAT_PLAN

TONE_PATH = "agents/marketing/tone_templates/"


def load_tone_template(tone: str) -> dict:
    file_path = os.path.join(TONE_PATH, f"{tone}.json")
    if not os.path.exists(file_path):
        return {
            "tone_name": tone,
            "style_description": "Default emotional tone.",
            "sample_opening": "Let’s explore this together.",
            "transition_phrases": []
        }
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def build_story_prompt(topic: str, user_traits: dict, tone: str, moat_source: str) -> dict:
    """
    يبني برومبت سردي عاطفي بناءً على الموضوع، السمات، النبرة، والحصانة.
    """

    # 1. تحميل نبرة الكتابة المختارة
    tone_data = load_tone_template(tone)

    # 2. بناء Hook ذكي
    base_hook = tone_data.get("sample_opening", f"What if {topic} is not what we think it is?")

    # 3. تحليل المحركات النفسية
    emotional_drivers = []
    if user_traits.get("prefers_solitude"):
        emotional_drivers.append("deep introspection")
    if user_traits.get("forgets_time_when_drawing"):
        emotional_drivers.append("flow-state driven")
    if user_traits.get("rebels_against_rules"):
        emotional_drivers.append("resistance to external control")
    if user_traits.get("trauma_linked_to_sports"):
        emotional_drivers.append("unprocessed physical pain")
    if not emotional_drivers:
        emotional_drivers.append("curiosity for inner movement")

    # 4. الحصانة
    moat = MOAT_PLAN.get(moat_source, {})
    moat_phrase = moat.get("why_irreplaceable", [""]).pop(0) if moat.get("why_irreplaceable") else ""

    return {
        "hook": base_hook,
        "emotional_drivers": emotional_drivers,
        "base_perspective": f"This story is not just about '{topic}' — it's about your hidden relationship with it.",
        "moat_inspiration": moat_phrase,
        "tone_description": tone_data.get("style_description", ""),
        "transitions": tone_data.get("transition_phrases", [])
    }
