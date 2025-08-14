# -- coding: utf-8 --
from __future__ import annotations

import os
import logging
from pathlib import Path
from typing import Optional, List, Tuple

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeAudioClip,
)
from moviepy.audio.fx import all as afx
from moviepy.audio.fx.all import audio_loop  # لعمل لووب للصوت الخلفي

# ======================== لوجينغ ========================
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(asctime)s | video_composer | %(message)s",
)

# ======================== مسارات افتراضية ========================
IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_PATH_DEFAULT = Path("content_studio/ai_voice/voices/final_voice.mp3")
VIDEO_OUTPUT_DIR = Path("content_studio/ai_video/final_videos/")
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ======================== أدوات مساعدة ========================
def _collect_images(directory: Path) -> List[Path]:
    """يجمع الصور المدعومة ويرتّبها."""
    exts = (".png", ".jpg", ".jpeg", ".webp")
    files = [p for p in directory.glob("*") if p.suffix.lower() in exts]
    files.sort(key=lambda p: p.name)
    return files

def _resolve_aspect(aspect: Optional[str]) -> Tuple[int, int]:
    """
    يختار الأبعاد حسب الـ aspect:
      - "square"     → 1080x1080
      - "portrait"   → 1080x1920 (9:16)
      - "landscape"  → 1920x1080 (16:9)
    لو لم يمرّر aspect نقرأ من المتغير VIDEO_ASPECT، وإلا الافتراضي مربع.
    """
    asp = (aspect or os.getenv("VIDEO_ASPECT", "square")).lower()
    if asp in ("portrait", "9:16", "portrait_9_16", "tall"):
        return (1080, 1920)
    if asp in ("landscape", "16:9", "landscape_16_9", "wide"):
        return (1920, 1080)
    return (1080, 1080)

def _prepare_clip(path: Path, duration: float, resolution: Tuple[int, int]) -> ImageClip:
    """
    يضبط الصورة لتناسب الفيديو:
    - يغيّر ارتفاعها لارتفاع الفيديو ويحافظ على نسبة الأبعاد
    - يضيف خلفيّة (letterbox) لتصبح بالحجم المطلوب دون قص
    """
    w, h = resolution
    clip = ImageClip(str(path)).set_duration(duration)
    clip = clip.resize(height=h)  # يحافظ على النسبة الأصلية
    clip = clip.on_color(size=resolution, color=(0, 0, 0), col_opacity=1)
    return clip

# ======================== الدالة الرئيسية ========================
def compose_video_from_assets(
    image_duration: float = 4.0,
    resolution: Optional[Tuple[int, int]] = None,   # إن تُركت None نختارها من aspect/env
    fps: int = 24,
    voice_path: Optional[str] = None,
    music_path: Optional[str] = None,
    music_volume: float = 0.15,
    durations: Optional[List[float]] = None,        # مدد مختلفة لكل صورة (اختياري)
    aspect: Optional[str] = None,                   # "square" | "portrait" | "landscape"
    xfade: float = 0.5,                              # زمن تداخل بسيط بين الصور
    kenburns_zoom: float = 0.03,                     # نسبة تكبير بطيء (3%)
) -> Optional[str]:
    """
    يجمع الصور الموجودة في IMAGES_DIR إلى فيديو واحد مع صوت اختياري:

    - Ken Burns خفيف (تكبير تدريجي).
    - Crossfade بين الصور (xfade).
    - دعم مدد ثابتة أو مختلفة لكل صورة (durations).
    - تعليق صوتي + موسيقى خلفية مع لووب تلقائي وfade و ducking بسيط.
    - اختيار نسبة الأبعاد عبر الوسيط أو متغير البيئة VIDEO_ASPECT.

    Returns:
        مسار الفيديو النهائي (str) أو None عند الفشل.
    """
    voice_clip = None
    music_clip = None
    video = None
    clip_list: List[ImageClip] = []
    music_raw = None
    try:
        # 1) تحضير الأبعاد
        target_res = resolution or _resolve_aspect(aspect)
        logging.info(f"Target resolution: {target_res[0]}x{target_res[1]}")

        # 2) اجمع الصور
        images = _collect_images(IMAGES_DIR)
        if not images:
            raise RuntimeError(f"لا توجد صور داخل: {IMAGES_DIR}")

        # 3) أنشئ مقاطع الصور مع Ken Burns + Crossfade
        per_image_durations = durations if durations and len(durations) == len(images) else None

        for i, p in enumerate(images):
            dur = per_image_durations[i] if per_image_durations else image_duration
            c = _prepare_clip(p, dur, target_res)

            # Ken Burns: تكبير تدريجي بسيط
            if kenburns_zoom and kenburns_zoom > 0:
                c = c.resize(lambda t: 1.0 + kenburns_zoom * (t / dur))

            # crossfade داخلي للصورة عدا الأولى
            if xfade and i > 0:
                c = c.crossfadein(xfade)

            clip_list.append(c)

        # padding=-xfade لكي يُطبّق التداخل بين المقاطع المتجاورة
        video = concatenate_videoclips(clip_list, method="compose", padding=-(xfade if xfade else 0))

        # 4) الصوت
        # تعليق صوتي
        vp = Path(voice_path) if voice_path else VOICE_PATH_DEFAULT
        if vp and vp.exists():
            voice_clip = AudioFileClip(str(vp)).fx(afx.audio_fadein, 0.3).fx(afx.audio_fadeout, 0.3)

        # موسيقى خلفية (لووب بطول الفيديو + خفض الصوت)
        if music_path and Path(music_path).exists():
            music_raw = AudioFileClip(music_path)
            music_clip = audio_loop(music_raw, duration=video.duration).volumex(music_volume)
            music_clip = music_clip.fx(afx.audio_fadein, 0.5).fx(afx.audio_fadeout, 0.5)

        if voice_clip and music_clip:
            # Ducking بسيط بخفض الموسيقى قليلًا
            music_clip = music_clip.volumex(0.6)
            audio = CompositeAudioClip([voice_clip, music_clip])
            video = video.set_audio(audio)
        elif voice_clip:
            video = video.set_audio(voice_clip)
        elif music_clip:
            video = video.set_audio(music_clip)
        # وإلا: بدون صوت

        # 5) التصدير
        out_path = VIDEO_OUTPUT_DIR / "final_video.mp4"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        logging.info(f"🎞️ writing video to {out_path}")
        video.write_videofile(
            str(out_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            preset="medium",
            ffmpeg_params=[
                "-movflags",
                "+faststart",
                # أفضل للتشغيل على الويب
                "-pix_fmt",
                "yuv420p",
                # توافق أوسع
            ],
            verbose=False,
            logger=None,
        )

        if not out_path.exists():
            raise RuntimeError("تم التصدير ولكن الملف غير موجود.")

        logging.info(f"✅ Video exported: {out_path}")
        return str(out_path.resolve())

    except Exception as e:
        logging.error(f"🔥 خطأ أثناء تركيب الفيديو: {e}")
        return None

    finally:
        # 6) تنظيف الموارد
        for c in clip_list:
            try:
                c.close()
            except Exception:
                pass
        try:
            if video:
                video.close()
        except Exception:
            pass
        try:
            if voice_clip:
                voice_clip.close()
        except Exception:
            pass
        try:
            if music_clip:
                music_clip.close()
        except Exception:
            pass
        try:
            if music_raw:
                music_raw.close()
        except Exception:
            pass

# ======================== تشغيل سريع (اختياري) ========================
if _name_ == "_main_":
    # تأكد أن لديك صورًا داخل IMAGES_DIR قبل التجربة
    out = compose_video_from_assets(
        image_duration=4,
        # aspect="portrait",  # جرّب "square"/"portrait"/"landscape" أو اضبط VIDEO_ASPECT بالبيئة
        fps=24,
        # voice_path="content_studio/ai_voice/voices/final_voice.mp3",
        # music_path="path/to/music.mp3",
        # durations=[3, 5, 4, 4],  # اختياري: مدة لكل صورة
        xfade=0.5,
        kenburns_zoom=0.03,
    )
    print("Output:", out)
