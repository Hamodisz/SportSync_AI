# -- coding: utf-8 --
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional
import re

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | core_engine | %(message)s"
)

# مسارات قياسية
IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH = Path("content_studio/ai_voice/voices/final_voice.mp3")
FINAL_VIDS_DIR = Path("content_studio/ai_video/final_videos/")
BURNED_DIR = Path("content_studio/ai_video/_burned_images/")

for p in (IMAGES_DIR, VOICE_PATH.parent, FINAL_VIDS_DIR, BURNED_DIR):
    p.mkdir(parents=True, exist_ok=True)

# --------- استيرادات مرنة ----------
_generate_script_fn = None
try:
    from content_studio.generate_script.script_generator import generate_script as _generate_script_fn
except Exception:
    pass

_generate_images_fn = None
try:
    from content_studio.ai_images.generate_images import generate_images as _generate_images_fn
except Exception:
    pass

_generate_voice_fn = None
try:
    from content_studio.ai_voice.voice_generator import generate_voice_from_script as _generate_voice_fn
except Exception:
    pass

_compose_video_fn = None
try:
    # إن كان عندك كومبوزر مخصص
    from content_studio.ai_video.video_composer import compose_video_from_assets as _compose_video_fn
except Exception:
    pass

# ======== تركيب الفيديو (Fallback محلي باستخدام MoviePy) ========
def _natural_key(p: Path):
    """ترتيب طبيعي لملفات مثل scene_1, scene_2..."""
    stem = p.stem
    try:
        n = int(stem.split("_")[-1])
    except Exception:
        n = 10**9
    return (stem.split("_")[0], n, p.name)

# --------- أدوات مساعدة للنصوص (captions) ----------
def _extract_scenes(script_text: str) -> List[str]:
    """يفصل السكربت إلى مشاهد (عربي/إنجليزي)."""
    parts = re.split(r"(?:Scene\s*#?\d*[:\-]?\s*)|(?:مشهد\s*#?\d*[:\-]?\s*)",
                     script_text, flags=re.IGNORECASE)
    scenes = [p.strip() for p in parts if p and p.strip()]
    if not scenes:
        scenes = [p.strip() for p in re.split(r"\n\s*\n", script_text) if p.strip()]
    return scenes


def _wrap_lines(text: str, max_len: int = 36) -> List[str]:
    words = text.split()
    out, line = [], ""
    for w in words:
        nxt = (line + " " + w).strip()
        if len(nxt) <= max_len:
            line = nxt
        else:
            if line:
                out.append(line)
            line = w
    if line:
        out.append(line)
    return out[:8]


def _burn_captions_on_images(images: List[Path], captions: List[str]) -> List[Path]:
    """يحرق عبارات captions على الصور ويحفظها في BURNED_DIR بنفس الترتيب."""
    from PIL import Image, ImageDraw, ImageFont

    # نظّف مجلد الصور المحروقة
    for f in BURNED_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    out_paths: List[Path] = []
    for i, img_path in enumerate(images):
        cap = captions[i] if i < len(captions) else ""
        im = Image.open(img_path).convert("RGBA")

        # طبقة شفافة للنص
        overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # خط
        try:
            font = ImageFont.truetype("arial.ttf", max(24, im.size[0] // 32))
        except Exception:
            font = ImageFont.load_default()

        lines = _wrap_lines(cap, max_len=max(24, im.size[0] // 28))
        if lines:
            # صندوق شبه شفاف أسفل الصورة
            pad = 24
            line_h = (font.size + 8)
            box_h = pad * 2 + line_h * len(lines)

            # مستطيل خلفي
            rect_y0 = im.size[1] - box_h
            rect_y1 = im.size[1]
            draw.rectangle([(0, rect_y0), (im.size[0], rect_y1)], fill=(0, 0, 0, 140))

            # ارسم السطور
            y = rect_y0 + pad
            x = pad
            for ln in lines:
                # ظل بسيط للنص
                draw.text((x+2, y+2), ln, font=font, fill=(0, 0, 0, 200))
                draw.text((x, y), ln, font=font, fill=(255, 255, 255, 255))
                y += line_h

        burned = Path(BURNED_DIR / f"{img_path.stem}_cap.png")
        im_out = Image.alpha_composite(im, overlay).convert("RGB")
        burned.parent.mkdir(parents=True, exist_ok=True)
        im_out.save(burned, format="PNG")
        out_paths.append(burned)

    return out_paths


def _fallback_compose_video(
    image_duration: int = 4,
    fps: int = 30,
    voice: Optional[str] = None,
    captions: Optional[List[str]] = None
) -> str:
    """تصميم فيديو بسيط من الصور باستخدام MoviePy. يدعم حرق captions قبل التجميع."""
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
    images = sorted(list(IMAGES_DIR.glob(".png")) + list(IMAGES_DIR.glob(".jpg")))
    if not images:
        raise ValueError("لا توجد صور في مجلد الإخراج.")
    clips = [ImageClip(str(p)).set_duration(image_duration) for p in images]
    video = concatenate_videoclips(clips, method="compose")

    if voice and Path(voice).exists():
        video = video.set_audio(AudioFileClip(str(voice)))
    out = FINAL_VIDS_DIR / "final_video.mp4"
    video.write_videofile(str(out), fps=fps, codec="libx264", audio_codec="aac")
    return str(out)

# نفرض الفولباك حتى لو وُجد كومبوزر خارجي (علشان نضمن يشتغل الآن)
_compose_video_fn = _fallback_compose_video


def _ensure_tools_available() -> List[str]:
    missing: List[str] = []
    if _generate_images_fn is None:
        missing.append("generate_images")
    # السكربت/الصوت اختياريان، الفيديو عندنا فولباك
    return missing


def quick_diagnose() -> Dict:
    return {
        "images_dir_exists": IMAGES_DIR.exists(),
        "images_count": len(list(IMAGES_DIR.glob("*.png"))) + len(list(IMAGES_DIR.glob("*.jpg"))),
        "voice_exists": VOICE_PATH.exists(),
        "voice_size": VOICE_PATH.stat().st_size if VOICE_PATH.exists() else 0,
        "final_videos_dir_exists": FINAL_VIDS_DIR.exists(),
        "tools_missing": _ensure_tools_available(),
    }


def run_full_generation(
    user_data: Dict,
    lang: str = "en",                 # 🔁 الافتراضي الآن إنجليزي
    image_duration: int = 4,
    override_script: Optional[str] = None,
    mute_if_no_voice: bool = True,
    skip_cleanup: bool = True,
) -> Dict:
    """يشغّل خط الإنتاج: Script -> Images -> (Voice) -> Video (مع captions)."""
    try:
        # تنظيف صور قديمة (اختياري)
        if not skip_cleanup and IMAGES_DIR.exists():
            for f in IMAGES_DIR.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass

        # 1) سكربت
        if override_script and override_script.strip():
            script = override_script.strip()
            logging.info("📝 استخدمنا سكربت جاهز (override_script).")
        else:
            if _generate_script_fn:
                # عدّل التوقيع حسب دالتك لو اختلف
                script = _generate_script_fn(
                    topic=user_data.get("topic", "sports motivation"),
                    tone=user_data.get("traits", {}).get("tone", "emotional"),
                    lang="english" if lang.lower().startswith("en") else "arabic",
                )
            else:
                script = (
                    "Scene 1: Start with a small step.\n\n"
                    "Scene 2: Keep going when no one is watching.\n\n"
                    "Scene 3: Results come to those who don’t quit."
                )

        captions = _extract_scenes(script)

        # 2) صور
        if _generate_images_fn is None:
            raise RuntimeError("دالة generate_images غير متوفرة.")
        images = _generate_images_fn(script, lang)
        if not images:
            raise RuntimeError("لم يتم توليد أي صور.")

        # 3) صوت (اختياري)
        voice_path = None
        if _generate_voice_fn:
            try:
                voice_path = generate_voice_fn(script, lang) if _generate_voice_fn.code_.co_argcount >= 2 else _generate_voice_fn(script)
            except Exception as e:
                logging.warning(f"تعذّر توليد الصوت: {e}")
                if not mute_if_no_voice:
                    raise

        # 4) فيديو
        if _compose_video_fn:
            try:
                # وقّع دالتك إن كان مختلفاً
                video_path = _compose_video_fn(image_duration=image_duration, voice_path=voice_path)
            except TypeError:
                video_path = _compose_video_fn(image_duration=image_duration)
        else:
            video_path = _fallback_compose_video(image_duration=image_duration, voice=voice_path)

        return {
            "script": str(script),
            "images": [str(p) for p in sorted(IMAGES_DIR.glob("*.png")) + sorted(IMAGES_DIR.glob("*.jpg"))],
            "voice": str(voice_path) if voice_path else None,
            "video": str(video_path),
            "error": None,
        }

    except Exception as e:
        logging.error(f"🔥 فشل التشغيل: {e}")
        return {"script": None, "images": [], "voice": None, "video": None, "error": str(e)}
