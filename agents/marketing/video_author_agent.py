# agents/marketing/video_author_agent.py

"""
هذا هو وكيل تأليف الفيديوهات الطويلة لـ Sport Sync AI.
يكتب سكربتات بجودة كتب صوتية — مبنية على الهوية النفسية، تحليل Layer Z، ومصدر الحصانة (Moat).
"""

from agents.marketing.video_story_prompt_engine import build_story_prompt
from agents.marketing.emotional_flow_model import apply_emotional_structure
from agents.marketing.visual_cue_generator import inject_visual_guidance
from agents.marketing.chapter_archiver import save_script_as_chapter
from strategy.strategic_moat_plan import MOAT_PLAN


def generate_script(topic: str, user_traits: dict, tone: str = "philosophical", moat_source: str = "Layer Z Engine") -> dict:
    """
    يُولد سكربت فيديو عميق بأسلوب سردي طويل + توقيع Moat.

    Parameters:
    - topic: فكرة الفيديو الرئيسية
    - user_traits: معالم نفسية للمستخدم (من Layer Z أو غيره)
    - tone: نوع الأسلوب (philosophical / poetic_pain / raw_rebellion...)
    - moat_source: مصدر الحصانة المستخدم كمحرك داخلي

    Returns:
    - dict: يحتوي على title, hook, sections[], visual_cues, moat_signature
    """
    
    # 1. نبني البرومبت العاطفي القصصي
    story_prompt = build_story_prompt(topic, user_traits, tone, moat_source)
    
    # 2. نطبق النموذج العاطفي (تصاعد درامي)
    raw_sections = apply_emotional_structure(story_prompt)
    
    # 3. نحقن إشارات بصرية ذكية (visual instructions)
    sections_with_visuals = inject_visual_guidance(raw_sections)
    
    # 4. توقيع الحصانة
    moat_signature = f"🔐 Powered by: {moat_source} – {MOAT_PLAN.get(moat_source, {}).get('description', '')}"
    
    # 5. بناء السكربت النهائي
    script = {
        "title": f"{topic.strip().capitalize()}",
        "hook": story_prompt.get("hook", ""),
        "sections": sections_with_visuals,
        "moat_signature": moat_signature,
        "tone": tone
    }
    
    # 6. حفظ كفصل في الكتاب
    save_script_as_chapter(script)
    
    return script
