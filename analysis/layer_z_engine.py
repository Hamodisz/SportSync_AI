# agents/marketing/content_creator_agent.py

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from analysis.user_analysis import summarize_traits
from agents.marketing.content_keys_engine import get_content_hooks
from core.brand_signature import add_brand_signature


def generate_content(user_data, lang="ar"):
    """
    توليد محتوى تعليمي تسويقي يعتمد على التحليل النفسي للمستخدم
    """
    full_text = user_data.get("full_text", "")
    questions = user_data.get("answers", {})

    # تحليل الطبقات
    traits_1_40 = apply_layers_1_40(full_text)
    traits_41_80 = apply_layers_41_80(full_text)
    traits_81_100 = apply_layers_81_100(full_text)
    traits_101_141 = apply_layers_101_141(full_text)
    silent_drivers = analyze_silent_drivers(user_data, questions)

    # دمج السمات
    all_traits = {}
    for group in [traits_1_40, traits_41_80, traits_81_100, traits_101_141, silent_drivers]:
        if isinstance(group, dict):
            all_traits.update(group)

    # التلخيص
    summary = summarize_traits(all_traits)

    # توليد المنشورات من مفاتيح المحتوى
    hooks = get_content_hooks(summary, lang=lang)
    contents = [sign_output(build_social_post(h, summary, lang)) for h in hooks]

    return contents


def build_social_post(hook, summary, lang="ar"):
    """
    صياغة منشور جذاب بناءً على hook وتحليل الشخصية
    """
    if lang == "ar":
        return f"""
🎯 {hook}

📌 هل تعلم أن: {summary.get('core_emotion', 'كل شخص يتحرك بدافع مختلف')}؟

👀 اكتشف رياضتك التي تكشف حقيقتك الخفية.

#الذكاء_الرياضي #SportSyncAI
        """.strip()
    else:
        return f"""
🎯 {hook}

📌 Did you know: {summary.get('core_emotion', 'everyone moves from a different inner drive')}?

👀 Discover your sport that reveals your hidden self.

#SportSyncAI #HumanDriven
        """.strip()


def sign_output(text):
    return add_brand_signature(text)
