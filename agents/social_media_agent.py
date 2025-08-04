import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(_file_), "..", "..")))

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141

from agents.marketing.content_keys_engine import get_content_hooks
from core.brand_signature import sign_output
from content_studio.content_engine import generate_video_from_topic

def generate_social_package(user_data, lang="ar"):
    """
    توليد بوست + فيديو تلقائي بناءً على تحليل الشخصية
    """
    # ✅ استيراد داخلي لحل الاستيراد الدائري
    from analysis.layer_z_engine import analyze_silent_drivers
    from analysis.user_analysis import summarize_traits

    # 🧠 تحليل المستخدم
    traits = {
        **apply_layers_1_40(user_data),
        **apply_layers_41_80(user_data),
        **apply_layers_81_100(user_data),
        **apply_layers_101_141(user_data),
        **analyze_silent_drivers(user_data)
    }

    summary = summarize_traits(traits)
    hooks = get_content_hooks(summary, lang=lang)
    chosen_hook = hooks[0] if hooks else "your sport identity"
    topic = f"How {chosen_hook.lower()} shapes your sport behavior"

    # 🎬 توليد الفيديو من المحتوى
    video_result = generate_video_from_topic(topic, lang=lang, tone="emotional")

    # 📝 صياغة بوست تسويقي
    post = build_social_post(chosen_hook, summary, lang)
    signed_post = sign_output(post)

    return {
        "topic": topic,
        "post": signed_post,
        "script": video_result["script"],
        "video_path": video_result["video"]
    }

def build_social_post(hook, summary, lang="ar"):
    if lang == "ar":
        return f"""
🎯 {hook}

📌 هل تعلم أن: {summary.get('core_emotion', 'كل شخص يتحرك بدافع مختلف')}؟

🎥 شاهد هذا الفيديو الذي قد يغيّر نظرتك للرياضة.

#الذكاء_الرياضي #SportSyncAI
        """.strip()
    else:
        return f"""
🎯 {hook}

📌 Did you know: {summary.get('core_emotion', 'everyone moves from a different inner drive')}?

🎥 Watch this video that might change how you view fitness.

#SportSyncAI #HumanDriven
        """.strip()

# 🧪 تجربة مباشرة
if _name_ == "_main_":
    fake_user = {
        "answers": {
            "Q1": "I lose interest after 3 days.",
            "Q2": "I enjoy learning by doing.",
            "Q3": "I forget time when I'm outdoors."
        }
    }

    result = generate_social_package(fake_user)
    print("🧠 Topic:", result["topic"])
    print("📄 Post:\n", result["post"])
    print("🎬 Video:", result["video_path"])
