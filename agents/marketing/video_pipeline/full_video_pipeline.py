# agents/marketing/full_video_pipeline.py

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from core.brand_signature import add_brand_signature

from agents.marketing.video_pipeline.image_generator import generate_images_from_script
from agents.marketing.video_pipeline.voice_generator import generate_voiceover
from agents.marketing.video_pipeline.video_composer import compose_final_video


def import_script_generator():
    # ✅ حل الاستيراد الدائري
    from agents.marketing.video_pipeline.script_writer import generate_script_from_traits
    return generate_script_from_traits


def generate_ai_video(user_data: dict, lang: str = "en") -> str:
    """
    توليد فيديو كامل مبني على تحليل نفسي عميق للمستخدم
    """
    # ✅ استيراد داخلي لتحليل المحركات الصامتة وتلخيص السمات
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
    from analysis.user_analysis import summarize_traits

    # 1️⃣ التحليل النفسي الكامل
    full_text = user_data.get("full_text", "")
    answers = user_data.get("answers", {})

    traits_1_40 = apply_layers_1_40(full_text)
    traits_41_80 = apply_layers_41_80(full_text)
    traits_81_100 = apply_layers_81_100(full_text)
    traits_101_141 = apply_layers_101_141(full_text)
    silent_drivers = analyze_silent_drivers(user_data, answers)

    # 2️⃣ دمج السمات
    full_summary = {
        **traits_1_40,
        **traits_41_80,
        **traits_81_100,
        **traits_101_141,
        **silent_drivers
    }

    summary = summarize_traits(full_summary)

    # 3️⃣ توليد السكربت بناءً على السمات
    script_text = import_script_generator()(summary, lang=lang)

    # 4️⃣ توليد الصور من السكربت
    images = generate_images_from_script(script_text)

    # 5️⃣ توليد الصوت من السكربت
    voice_path = generate_voiceover(script_text, lang=lang)

    # 6️⃣ تركيب الفيديو النهائي
    final_video_path = compose_final_video(images, voice_path, lang=lang)

    # 7️⃣ توقيع الفيديو بشعار البراند
    signed_video = add_brand_signature(final_video_path)

    print(f"\n✅ Final signed video ready: {signed_video}")
    return signed_video
