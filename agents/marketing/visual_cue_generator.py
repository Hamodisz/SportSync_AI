# agents/marketing/visual_cue_generator.py

"""
يضيف إشارات بصرية ذكية داخل السكربت الطويل،
تساعد على تحويله إلى فيديو سينمائي مؤثر بدون مجهود إخراجي ضائع.
"""

def inject_visual_guidance(sections: list) -> list:
    """
    يأخذ كل فقرة في السكربت، ويحقن داخلها أو قبلها تعليمات بصرية ذكية.

    Parameters:
    - sections (list): فقرات السكربت النصية

    Returns:
    - list: فقرات مع تعليمات بصرية مضافة
    """
    visual_cues = [
        "[Visual: A person sitting alone in a large empty space. Soft ambient music.]",
        "[Visual: Close-up of hands drawing, fading into chaotic motion scenes.]",
        "[Visual: Fast-cut montage of social pressures, metrics, failures.]",
        "[Visual: The same person begins walking slowly through sunlight. Rhythm returns.]",
        "[Visual: Calm shot of user standing in nature. Text fades in: 'You were never broken.']"
    ]

    injected_sections = []
    for i, section in enumerate(sections):
        cue = visual_cues[i] if i < len(visual_cues) else "[Visual: Fade to black with hopeful music.]"
        injected_sections.append(f"{cue}\n\n{section}")

    return injected_sections
