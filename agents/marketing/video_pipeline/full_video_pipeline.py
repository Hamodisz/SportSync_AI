# full_video_pipeline.py

from analysis.analysis_layers_1_40 import apply_layers_1_40
from analysis.analysis_layers_41_80 import apply_layers_41_80
from analysis.analysis_layers_81_100 import apply_layers_81_100
from analysis.analysis_layers_101_141 import apply_layers_101_141
from core.brand_signature import add_brand_signature

from agents.marketing.video_pipeline.image_generator import generate_images
from agents.marketing.video_pipeline.voice_generator import generate_voiceover
from agents.marketing.video_pipeline.video_composer import compose_final_video

# ✅ حل الاستيراد الدائري
def import_script_generator():
    from agents.marketing.video_pipeline.script_writer import generate_script_from_traits
    return generate_script_from_traits

def generate_ai_video(user_data: dict, lang: str = "en") -> str:
    """
    توليد فيديو كامل مبني على تحليل نفسي عميق للمستخدم
    """
    # 1. تحليل السمات
    traits = {}
    traits.update(apply_layers_1_40(user_data))
    traits.update(apply_layers_41_80(user_data))
    traits.update(apply_layers_81_100(user_data))
    traits.update(apply_layers_101_141(user_data))

    user_data["traits"] = traits

    # 2. استدعاء مولد السكربت الديناميكي
    generate_script_from_traits = import_script_generator()
    script_text = generate_script_from_traits(user_data, lang=lang)

    # 3. توليد الصور
    images = generate_images(script_text)

    # 4. توليد الصوت
    voice_path = generate_voiceover(script_text, lang=lang)

    # 5. تركيب الفيديو
    final_video_path = compose_final_video(images, voice_path)

    # 6. توقيع البراند
    signed_video = add_brand_signature(final_video_path)

    print(f"\n✅ Final signed video ready: {signed_video}")
    return signed_video
