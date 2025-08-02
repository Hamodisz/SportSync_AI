# agents/marketing/video_story_prompt_engine.py

"""
يبني البرومبت القصصي العاطفي الكامل بناءً على:
- موضوع الفيديو
- سمات المستخدم (user_traits)
- نبرة الأسلوب (tone)
- مصدر الحصانة (moat)
"""

from strategy.strategic_moat_plan import MOAT_PLAN


def build_story_prompt(topic: str, user_traits: dict, tone: str, moat_source: str) -> dict:
    """
    يولد برومبت أساسي يُستخدم لاحقًا لتوليد السكربت داخل LLM.
    
    Returns:
    - dict يحتوي على: hook, emotional_drivers, base_perspective
    """

    # 1. Hook ذكي مرتبط بالمستخدم
    base_hook = f"What if {topic.lower()} is not what we’ve always believed?"

    # 2. استخلاص محركات نفسية خام من سمات المستخدم
    emotional_drivers = []

    if user_traits.get("prefers_solitude"):
        emotional_drivers.append("deep introspection")
    if user_traits.get("forgets_time_when_drawing"):
        emotional_drivers.append("flow-state driven")
    if user_traits.get("rebels_against_rules"):
        emotional_drivers.append("resistance to external control")
    if user_traits.get("trauma_linked_to_sports"):
        emotional_drivers.append("unprocessed pain in physical expression")

    if not emotional_drivers:
        emotional_drivers.append("curiosity about the deeper meaning of movement")

    # 3. توقيع Moat المستخدم كمصدر القوة
    moat = MOAT_PLAN.get(moat_source, {})
    moat_phrase = moat.get("why_irreplaceable", [""]).pop(0) if moat.get("why_irreplaceable") else ""

    # 4. بناء منظور داخلي (base narrative tone)
    base_perspective = f"This story is not just about '{topic}' — it's about your unspoken relationship with it."

    # 5. نبرة خاصة من tone templates لاحقًا (ممكن نربطها تلقائيًا هنا مستقبلًا)

    return {
        "hook": base_hook,
        "emotional_drivers": emotional_drivers,
        "base_perspective": base_perspective,
        "moat_inspiration": moat_phrase
    }
