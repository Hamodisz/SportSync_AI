# agents/marketing/emotional_flow_model.py

"""
يحاكي التدرج العاطفي الكامل لأي سكربت.
يدمج الجمل الانتقالية من tone_templates لرفع جودة السرد.
"""

def apply_emotional_structure(story_prompt: dict) -> list:
    hook = story_prompt.get("hook", "")
    drivers = story_prompt.get("emotional_drivers", [])
    perspective = story_prompt.get("base_perspective", "")
    moat = story_prompt.get("moat_inspiration", "")
    transitions = story_prompt.get("transitions", [])

    def get_transition(index):
        return transitions[index] if index < len(transitions) else ""

    return [
        # 1. Calm Opening
        f"{hook}\n\n{get_transition(0)}\nWe often go through life accepting certain truths without question.\nBut sometimes… all it takes is one new idea to shatter the illusion.",

        # 2. Inner Friction
        f"{get_transition(1)}\nMany of us feel disconnected — not because we're lazy, but because something in our environment misaligned with us.\nDrivers like {', '.join(drivers)} are often misunderstood — or ignored completely.",

        # 3. Collapse Moment
        f"{get_transition(2)}\nWhat if the problem wasn’t you?\nWhat if the system — the culture, the expectations — was never built with someone like you in mind?\nThat realization can feel like collapse — but it’s actually clarity.",

        # 4. Realignment
        f"{get_transition(3)}\nAnd that clarity?\nIt’s the beginning of a return — a reconnection to movement that feels like you.\n{perspective} Through this lens, sport is no longer a metric… it’s a mirror.",

        # 5. Emotional Closure
        f"{get_transition(4)}\nThis matters because of what’s at stake: your identity, your joy, your freedom.\n{moat}\nSo if this message spoke to you… maybe you're not broken. Maybe you’re finally seen.\nWelcome to Sport Sync AI."
    ]
