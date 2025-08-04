def generate_script_from_traits(summary: dict, lang: str = "en", video_type: str = "🎞 مقطع طويل") -> str:
    """
    توليد سكربت فيديو بناءً على السمات والتحليل + نوع الفيديو
    """

    # 📌 استخراج سمات مهمة
    core_motives = summary.get("core_motives", "growth, identity, freedom")
    dominant_trait = summary.get("dominant_trait", "resilience")
    sport_style = summary.get("preferred_style", "solo & creative")
    silent_driver = summary.get("silent_driver", "losing track of time in flow state")

    # 📝 بناء السكربت حسب نوع الفيديو
    if video_type == "🎞 مقطع طويل":
        script = f"""
In a world driven by {core_motives}, there are a few who don't follow — they lead.
This story is about someone whose core is built on {dominant_trait}.
Not because it’s easy, but because comfort was never the goal.

They move through life with a {sport_style} rhythm.
No audience. No medals. Just {silent_driver} — the zone where time disappears.

This is not just training. This is identity.
This is SportSync.
"""
    elif video_type == "🎯 اقتباس قصير":
        script = f"""
{dominant_trait.upper()} isn’t something you show.
It’s what makes you move — even when no one’s watching.

SportSync. Identity in motion.
"""
    elif video_type == "📢 إعلان تجريبي":
        script = f"""
What if your sport... wasn’t just a hobby?

What if it was a map to your mind?
At SportSync, we decode your {dominant_trait}, your drive, your identity.

Join the movement.
"""

    else:
        # 🎬 احتياطي: fallback للنص الكامل
        script = f"""
SportSync is built for those who train beyond applause.

Driven by {core_motives}, fueled by {silent_driver}, 
and defined by a {sport_style} spirit.

This is who you are. This is SportSync.
"""

    return script.strip()
