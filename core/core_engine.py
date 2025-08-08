# core/core_engine.py

from _future_ import annotations
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import inspect

# ========== logging (منع تكرار الإعداد) ==========
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(asctime)s | core_engine | %(message)s"
    )

IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_VIDS_DIR = Path("content_studio/ai_video/final_videos/")

for p in (IMAGES_DIR, VOICE_PATH.parent, FINAL_VIDS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# -------- محاولات الاستيراد المرنة --------
_generate_script_fn = None
_generate_images_fn = None
_generate_voice_fn = None
_compose_video_fn = None

# script
try:
    # content_studio
    from content_studio.generate_script.script_generator import generate_script as _generate_script_fn
except Exception:
    try:
        # agents
        from agents.marketing.video_pipeline.script_writer import generate_script_from_traits as _generate_script_fn
    except Exception:
        pass

# images
try:
    from content_studio.ai_images.generate_images import generate_images as _generate_images_fn
except Exception:
    try:
        from agents.marketing.video_pipeline.image_generator import generate_images as _generate_images_fn
    except Exception:
        pass

# voice
try:
    from content_studio.ai_voice.voice_generator import generate_voice_from_script as _generate_voice_fn
except Exception:
    try:
        from agents.marketing.video_pipeline.voice_generator import generate_voiceover as _generate_voice_fn
    except Exception:
        pass

# compose
try:
    from content_studio.ai_video.video_composer import compose_video_from_assets as _compose_video_fn
except Exception:
    pass


def _ensure_tools_available() -> List[str]:
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
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass


def _call_script_generator(user_data: Dict, lang: str) -> str:
    """
    يحاول أولاً دالة agents.generate_script_from_traits(user_data, lang)
    وإن لم تتوفر يستعمل content_studio.generate_script(...) بتوقيعها.
    """
    if _generate_script_fn is None:
        raise RuntimeError("No script generator available")

    name = getattr(generate_script_fn, "name_", "")
    if "generate_script_from_traits" in name:
        return _generate_script_fn(user_data, lang)

    # توقيع content_studio.generate_script
    # عدّل القيم الافتراضية حسب مشروعك
    return _generate_script_fn(
        lang=lang,
        audience=user_data.get("traits", {}).get("target_audience", "عام"),
        quality=user_data.get("traits", {}).get("quality_level", "جيدة"),
        tone="عام",
        purpose="عام",
        custom_prompt=""
    )


def _call_voice_generator(script: str, lang: str) -> Optional[str]:
    """
    يتعامل مع اختلاف التواقيع: بعض الدوال تأخذ (script) فقط،
    وبعضها (script, lang).
    """
    if _generate_voice_fn is None:
        return None

    sig = inspect.signature(_generate_voice_fn)
    params = list(sig.parameters.values())
    try:
        if len(params) >= 2:
            return _generate_voice_fn(script, lang)
        else:
            return _generate_voice_fn(script)
    except Exception as e:
        logging.warning(f"⚠ فشل توليد الصوت: {e}")
        return None


def run_full_generation(
    user_data: Dict,
    lang: str = "ar",
    image_duration: int = 4,
    override_script: Optional[str] = None,
    mute_if_no_voice: bool = True,
    skip_cleanup: bool = False,
) -> Dict:
    """
    pipeline: Script -> Images -> Voice -> Video
    Returns dict: {script, images[], voice, video, error}
    """
    missing = _ensure_tools_available()
    if missing:
        msg = "المكوّنات الناقصة/مسارات خاطئة: " + ", ".join(missing)
        logging.error(msg)
        return {"script": None, "images": [], "voice": None, "video": None, "error": msg}

    try:
        if not skip_cleanup:
            _clean_images_output_dir()

        # 1) Script
        if override_script and override_script.strip():
            script = override_script.strip()
            logging.info("📝 override_script مستخدم.")
        else:
            logging.info("🧠 توليد السكربت...")
            script = _call_script_generator(user_data, lang)
        if not script or not str(script).strip():
            raise ValueError("فشل توليد السكربت.")

        # 2) Images
        logging.info("🖼 توليد الصور...")
        images = _generate_images_fn(script, lang)
        img_count = len(list(IMAGES_DIR.glob("*.png")))
        if not images and img_count == 0:
            raise ValueError("لم يتم توليد أي صور (قائمة فارغة والمجلد فارغ).")
        logging.info(f"📸 عدد الصور في المجلد: {img_count}")

        # 3) Voice
        logging.info("🎙 توليد الصوت...")
        voice_path = _call_voice_generator(script, lang)
        if voice_path and Path(voice_path).exists():
            logging.info(f"🔊 ملف الصوت: {voice_path} (حجم: {Path(voice_path).stat().st_size} بايت)")
        else:
            msg = "لا يوجد صوت صالح، سيتم المتابعة بدون صوت."
            if mute_if_no_voice:
                logging.warning(f"⚠ {msg}")
                voice_path = None
            else:
                raise ValueError(msg)

        # 4) Video
        logging.info("🎞 تركيب الفيديو...")
        video_path = _compose_video_fn(image_duration=image_duration)
        if not video_path or not Path(video_path).exists():
            raise ValueError("فشل تركيب الفيديو النهائي.")
        logging.info(f"✅ فيديو نهائي: {video_path}")

        return {
            "script": str(script),
            "images": [str(p) for p in IMAGES_DIR.glob("*.png")],
            "voice": str(voice_path) if voice_path else None,
            "video": str(video_path),
            "error": None
        }

    except Exception as e:
        # تشخيص إضافي
        diag = {
            "images_dir_exists": IMAGES_DIR.exists(),
            "images_count": len(list(IMAGES_DIR.glob('*.png'))),
            "voice_exists": VOICE_PATH.exists(),
            "voice_size": VOICE_PATH.stat().st_size if VOICE_PATH.exists() else 0,
            "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        }
        logging.error(f"🔥 خطأ أثناء التوليد: {e} | تشخيص: {diag}")
        return {"script": None, "images": [], "voice": None, "video": None, "error": str(e)}


def quick_diagnose() -> Dict:
    return {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob("*.png"))),
        "voice_exists": VOICE_PATH.exists(),
        "voice_size": VOICE_PATH.stat().st_size if VOICE_PATH.exists() else 0,
        "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        "tools_missing": _ensure_tools_available(),
    }
