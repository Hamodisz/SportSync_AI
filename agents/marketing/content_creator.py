from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from analysis.trait_utils import summarize_traits
from agents.marketing.content_keys_engine import get_content_hooks
from core.brand_signature import add_brand_signature


def generate_content(user_data, lang="ar"):
    """
    توليد محتوى تعليمي تسويقي يعتمد على التحليل النفسي للمستخدم
    """
    # 🧠 جلب النص الكامل من المستخدم
    full_text = user_data.get("full_text", "")

    # 🔍 تحليل السمات والطبقات
    traits_1_40 = apply_layers_1_40(full_text)
    traits_41_80 = apply_layers_41_80(full_text)
    traits_81_100 = apply_layers_81_100(full_text)
    traits_101_141 = apply_layers_101_141(full_text)
    
    # ✅ تمرير answers كـ questions إذا لم تكن موجودة
    questions = user_data.get("answers", {})
    silent_drivers = analyze_silent_drivers(user_data, questions)

    # 🧠 تلخيص الشخصية
    summary = summarize_traits({
        **traits_1_40, 
        **traits_41_80, 
        **traits_81_100, 
        **traits_101_141, 
        **silent_drivers
    })

    # 🎯 الحصول على مفاتيح السوشال ميديا (hooks)
    hooks = get_content_hooks(summary, lang=lang)

    # ✍ توليد المحتوى النهائي
    contents = []
    for hook in hooks:
        post = build_social_post(hook, summary, lang)
        signed = sign_output(post)
        contents.append(signed)

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
    """
    توقيع المحتوى بتوقيع البراند
    """
    return add_brand_signature(text)

