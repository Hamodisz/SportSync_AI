# agents/marketing/emotional_flow_model.py

"""
يحوّل البرومبت إلى هيكل سردي عاطفي مكوّن من 5 مراحل:

1. Calm Opening – مدخل هادئ يفكك الجدار النفسي
2. Inner Friction – زرع التوتر الداخلي
3. Collapse Moment – لحظة الانهيار أو الإدراك
4. Realignment – تقديم منظور جديد
5. Emotional Closure – نهاية تحررية تبقى في القلب
"""

def apply_emotional_structure(story_prompt: dict) -> list:
    hook = story_prompt.get("hook", "")
    drivers = story_prompt.get("emotional_drivers", [])
    perspective = story_prompt.get("base_perspective", "")
    moat = story_prompt.get("moat_inspiration", "")

    return [
        # 1. Calm Opening
        f"{hook}\n\nWe often go through life accepting certain truths without question.\nBut sometimes… all it takes is one new idea to shatter the illusion.",

        # 2. Inner Friction
        f"Let’s go deeper.\nYou see, many of us feel disconnected — not because we're lazy, but because something in our environment misaligned with us.\nDrivers like {', '.join(drivers)} are often misunderstood — or ignored completely.",

        # 3. Collapse Moment
        f"What if the problem wasn’t you?\nWhat if the system — the culture, the expectations — was never built with someone like you in mind?\nThat moment of realization… can feel like collapse, but it’s actually clarity.",

        # 4. Realignment
        f"And that clarity?\nIt’s the beginning of a return — a reconnection to movement that feels like you.\n{perspective} Through this lens, sport is no longer a metric… it’s a mirror.",

        # 5. Emotional Closure
        f"This matters because of what’s at stake: your identity, your joy, your freedom.\n{moat}\nSo if this message spoke to you… maybe you're not broken. Maybe you’re finally seen.\nWelcome to Sport Sync AI."
    ]
