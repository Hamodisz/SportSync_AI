def get_content_hooks(summary, lang="ar"):
    core = summary.get("core_emotion", "الفضول")
    strength = summary.get("dominant_trait", "حب التجربة")
    challenge = summary.get("challenge", "الملل من الروتين")

    if lang == "ar":
        return [
            f"عمرك حسّيت إن {core} هو الشي الوحيد اللي يحركك بدون ما تحس؟",
            f"{strength} مو بس نقطة قوة… هذا الشي اللي يخليك تعيش.",
            f"الناس تكره الروتين، بس إنت؟ {challenge} هو الدافع الخفي فيك.",
            f"مو كل رياضة تناسبك… إنت تحتاج تجربة تكشفك لنفسك.",
            "في رياضات تصقل الجسم، وفي رياضة تصقل الهوية… أي وحدة تبي؟",
            "ما تدور على رياضة، تدور على شعور يلمسك.",
            "اللحظة اللي تذوب فيها وتنسى الوقت… هناك هويتك الرياضية."
        ]
    else:
        return [
            f"Have you ever felt that {core} is the only thing that moves you—without effort?",
            f"{strength} isn’t just a strength… it’s your emotional heartbeat.",
            f"While others fear routine, {challenge} is what actually fuels you.",
            "Not every sport is for you… you need an experience that reveals you.",
            "Some sports shape the body. The right one shapes the soul.",
            "You’re not looking for a sport. You’re looking for a feeling.",
            "That moment when time disappears? That’s your real sport identity."
        ]
