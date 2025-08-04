# agents/marketing/video_pipeline/script_writer.py

def generate_script_from_traits(summary: dict, lang: str = "en") -> str:
    """
    توليد سكربت فيديو قصصي بناءً على ملخص السمات
    """
    name = summary.get("name", "this person")
    emotion = summary.get("core_emotion", "a deep, unique drive")
    driver = summary.get("silent_driver", "an invisible inner force")
    sport = summary.get("suggested_sport", "a sport that mirrors their soul")

    if lang == "ar":
        return f"""
تخيل شخصًا يحمل في داخله {emotion}، يتحرك بدافع {driver}...

ربما لم يُكتشف بعد، لكنه موجود. طريقه ليس شائعًا، ولا يشبه أحدًا.

الرياضة التي تنتظره؟ ليست مجرد لعبة… إنها {sport}.

ليس لأنه يجيدها، بل لأنها تُشبهه.

افتح الباب… واكتشف من أنت حقًا.
        """.strip()
    
    else:
        return f"""
Imagine someone driven by {emotion}, moved by {driver}...

They might still be undiscovered, but their path is real. And unique.

The sport waiting for them? Not just a game… it's {sport}.

Not because they’re good at it — but because it reflects who they are.

Open the door… and discover your real self.
        """.strip()
