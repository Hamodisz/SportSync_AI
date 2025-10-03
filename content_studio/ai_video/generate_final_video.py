# content_studio/ai_video/generate_final_video.py
# يصنع فيديو من صور + (نص اختياري) بناءً على metadata.json

from __future__ import annotations
import os, json, argparse
from pathlib import Path

# ---- Pillow compat (ANTIALIAS -> Resampling.LANCZOS) قبل استيراد moviepy ----
try:
    from PIL import Image as _PILImage
    if not hasattr(_PILImage, "ANTIALIAS"):
        _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
except Exception:
    pass

# ---- استيراد moviepy ----
from moviepy.editor import (
    ImageClip, AudioFileClip, concatenate_videoclips,
    CompositeVideoClip, TextClip, vfx
)

# ---- Patch داخلي لخطأ ANTIALIAS داخل دالة resize في moviepy (إذا لزم) ----
try:
    import moviepy.video.fx.resize as mp_resize
    from PIL import Image as _PILImage2
    if getattr(mp_resize, "Image", None) and not hasattr(mp_resize.Image, "ANTIALIAS"):
        mp_resize.Image = _PILImage2
        mp_resize.Image.ANTIALIAS = _PILImage2.Resampling.LANCZOS
except Exception:
    pass


def build_video(meta_path: str, out_path: str, width: int = 1920, height: int = 1920) -> str:
    """
    يبني الفيديو من صور حسب metadata.json:
      {
        "fps": 30,
        "images": ["path/scene_1.png", ...],
        "seconds": [6,8,7],
        "texts": ["سطر نص", "", "سطر ثالث"]
      }
    """
    meta_p = Path(meta_path)
    if not meta_p.exists():
        raise FileNotFoundError(f"لم يتم العثور على ملف الميتاداتا: {meta_p}")

    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    fps = int(meta.get("fps", 30))
    images = list(meta.get("images", []))
    seconds = list(meta.get("seconds", []))
    texts = list(meta.get("texts", []))

    if not images:
        raise ValueError("قائمة الصور فارغة في metadata.json")

    # إذا لم تُحدَّد المدد، نفترض 5 ثواني لكل صورة
    if not seconds or len(seconds) != len(images):
        seconds = [5] * len(images)

    # لو القائمة النصية أقصر من الصور نكمّلها بسلاسل فارغة
    if len(texts) < len(images):
        texts += [""] * (len(images) - len(texts))

    size = (width, height)
    clips = []

    missing = [p for p in images if not Path(p).exists()]
    if missing:
        # نطبع المفقود للمساعدة في الـ debug داخل Actions
        raise FileNotFoundError(f"الصور التالية غير موجودة:\n- " + "\n- ".join(missing))

    for img_path, dur, txt in zip(images, seconds, texts):
        base_clip = ImageClip(img_path).resize(newsize=size).set_duration(float(dur))

        if txt and txt.strip():
            # نص اختياري فوق الصورة
            try:
                txt_clip = TextClip(
                    txt,
                    fontsize=60,
                    color="white",
                    stroke_color="black",
                    stroke_width=3,
                    method="caption",
                    size=(int(size[0]*0.9), None)  # عرض النص أقل قليلًا من عرض الفيديو
                ).set_duration(float(dur)).set_position(("center", "bottom"))
                clip = CompositeVideoClip([base_clip, txt_clip])
            except Exception:
                # لو ما توفرت خطوط/إعدادات نص، نُكمل بدون نص
                clip = base_clip
        else:
            clip = base_clip

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")

    # صوت اختياري عبر متغير بيئي AUDIO_URL
    audio_url = os.getenv("AUDIO_URL", "").strip()
    if audio_url:
        # يتطلب تنزيل الملف أولًا قبل AudioFileClip؛ هنا نتوقع أنه غير مستخدم عادة في Actions
        try:
            import requests, tempfile
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(audio_url)[1] or ".mp3", delete=False) as tmpf:
                tmp = tmpf.name
                r = requests.get(audio_url, timeout=30)
                r.raise_for_status()
                tmpf.write(r.content)
            final = final.set_audio(AudioFileClip(tmp))
        except Exception as e:
            print(f"[تحذير] فشل تحميل الصوت من AUDIO_URL: {e}. سنكمل بدون صوت.")

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    # نستخدم libx264 + aac (لو فيه صوت)
    final.write_videofile(
        str(out_p),
        fps=fps,
        codec="libx264",
        audio_codec="aac"  # لا يضر لو ما فيه صوت
    )
    print(f"✅ تم إنتاج الفيديو: {out_p}")
    return str(out_p)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta", required=True, help="مسار ملف metadata.json")
    parser.add_argument("--out", required=True, help="مسار حفظ الفيديو النهائي")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()

    build_video(args.meta, args.out, width=args.width, height=args.height)


if __name__ == "__main__":
    main()
