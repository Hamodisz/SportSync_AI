# core/core_engine.py
# ---------------------------------------------
# محرك مركزي يربط: (سكربت -> صور -> صوت -> فيديو)
# مصمم ليتحمل اختلاف المسارات بين agents/... و content_studio/...
# ويرجع نتيجة موحّدة + رسائل تشخيص واضحة.
# ---------------------------------------------

from _future_ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

# ========== إعداد لوجينغ بسيط ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | core_engine | %(message)s"
)

# ========== مسارات الأصول القياسية ==========
IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_VIDS_DIR = Path("content_studio/ai_video/final_videos/")

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
VOICE_PATH.parent.mkdir(parents=True, exist_ok=True)
FINAL_VIDS_DIR.mkdir(parents=True, exist_ok=True)

# ========== استيرادات مرنة (تحتمل أكثر من مسار/اسم) ==========
# سكربت
_generate_script_fn = None
try:
    # نسخة content_studio
    from content_studio.generate_script.script_generator import generate_script as _generate_script_fn
except Exception:
    try:
        # نسخة agents
        from agents.marketing.video_pipeline.script_writer import generate_script_from_traits as _generate_script_fn
    except Exception:
        pass

# صور
_generate_images_fn = None
try:
    # نسخة content_studio
    from content_studio.ai_images.generate_images import generate_images as _generate_images_fn
except Exception:
    try:
        # نسخة agents
        from agents.marketing.video_pipeline.image_generator import generate_images as _generate_images_fn
    except Exception:
        pass

# صوت
_generate_voice_fn = None
try:
    # نسخة content_studio (gTTS / ElevenLabs حسب ما عندك)
    from content_studio.ai_voice.voice_generator import generate_voice_from_script as _generate_voice_fn
except Exception:
    try:
        # نسخة agents
        from agents.marketing.video_pipeline.voice_generator import generate_voiceover as _generate_voice_fn
    except Exception:
        pass

# تركيب فيديو
_compose_video_fn = None
try:
    from content_studio.ai_video.video_composer import compose_video_from_assets as _compose_video_fn
except Exception:
    # لو عندك اسم/مكان مختلف، أضفه هنا إن لزم
    pass


def _ensure_tools_available() -> List[str]:
    """يرجع قائمة بالأجزاء المفقودة (إن وجدت)."""
    missing = []
    if _generate_script_fn is None:
        missing.append("generate_script (script_generator / script_writer)")
    if _generate_images_fn is None:
        missing.append("generate_images (ai_images)")
    if _generate_voice_fn is None:
        missing.append("generate_voice (voice_generator)")
    if _compose_video_fn is None:
        missing.append("compose_video_from_assets (video_composer)")
    return missing


def _clean_images_output_dir():
    """تنظيف مجلد الصور قبل أي تشغيل (اختياري لكن مفيد لتجنّب تداخل النتائج)."""
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass


def run_full_generation(
    user_data: Dict,
    lang: str = "ar",
    image_duration: int = 4,
    override_script: Optional[str] = None
) -> Dict:
    """
    يشغل البايبلاين كاملًا:
      1) توليد سكربت (أو استخدام سكربت ممرَّر)
      2) توليد صور
      3) توليد صوت
      4) تركيب فيديو نهائي

    Args:
        user_data: بيانات المستخدم (traits الخ...)
        lang: لغة الإخراج "ar"/"en"
        image_duration: مدة عرض كل صورة (ثواني)
        override_script: إن وفّرته، يتم تخطي توليد السكربت واستخدامه مباشرة

    Returns:
        dict: {script, images[], voice, video, error}
    """
    missing = _ensure_tools_available()
    if missing:
        msg = "المكوّنات التالية غير متوفرة أو مساراتها خاطئة: " + ", ".join(missing)
        logging.error(msg)
        return {"script": None, "images": [], "voice": None, "video": None, "error": msg}

    try:
        # 0) تحضير
        _clean_images_output_dir()

        # 1) سكربت
        if override_script and override_script.strip():
            script = override_script.strip()
            logging.info("📝 تم استخدام سكربت ممرَّر (override_script).")
        else:
            logging.info("🧠 توليد السكربت...")
            # دوال مختلفة قديم/حديث:
            # - content_studio.generate_script.script_generator.generate_script(user_args...)
            # - agents.marketing.video_pipeline.script_writer.generate_script_from_traits(user_data, lang)
            if generate_script_fn.name_ == "generate_script_from_traits":
                script = _generate_script_fn(user_data, lang)  # نسخة agents
            else:
                # نسخة content_studio: عدّل التواقيع حسب دالتك إن اختلفت
                script = _generate_script_fn(
                    lang=lang,
                    audience=user_data.get("traits", {}).get("target_audience", "عام"),
                    quality=user_data.get("traits", {}).get("quality_level", "جيدة"),
                    tone="عام",
                    purpose="عام",
                    custom_prompt=""
                )
        if not script or not str(script).strip():
            raise ValueError("فشل توليد السكربت (script).")

        # 2) صور
        logging.info("🖼 توليد الصور...")
        images = _generate_images_fn(script, lang)
        if not images:
            raise ValueError("لم يتم توليد أي صور داخل المحتوى (images).")
        # تحقق وجود فعلي بالمجلد المتوقَّع
        if not any(IMAGES_DIR.glob("*.png")):
            logging.warning("⚠ قائمة الصور رجعت، لكن مجلد الإخراج فارغ. تحقق من generate_images.")

        # 3) صوت
        logging.info("🎙 توليد الصوت...")
        voice_path = generate_voice_fn(script, lang) if _generate_voice_fn.code_.co_argcount >= 2 else _generate_voice_fn(script)
        if not voice_path or not Path(voice_path).exists():
            logging.warning("⚠ لم يتم العثور على ملف الصوت الناتج. سيتم تركيب الفيديو بدون صوت.")
            voice_path = None

        # 4) فيديو
        logging.info("🎞 تركيب الفيديو النهائي...")
        video_path = _compose_video_fn(image_duration=image_duration)
        if not video_path or not Path(video_path).exists():
            raise ValueError("فشل تركيب الفيديو النهائي (video).")

        logging.info("✅ اكتمل التوليد بنجاح.")
        return {
            "script": str(script),
            "images": [str(p) for p in IMAGES_DIR.glob("*.png")],
            "voice": str(voice_path) if voice_path else None,
            "video": str(video_path),
            "error": None
        }

    except Exception as e:
        logging.error(f"🔥 خطأ: {e}")
        return {"script": None, "images": [], "voice": None, "video": None, "error": str(e)}


def quick_diagnose() -> Dict:
    """
    تشخيص سريع لوضع البيئة والمسارات.
    """
    status = {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob("*.png"))),
        "voice_exists": VOICE_PATH.exists(),
        "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        "tools_missing": _ensure_tools_available(),
    }
    return status
