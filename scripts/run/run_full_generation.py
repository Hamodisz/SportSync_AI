# -- coding: utf-8 --
"""
تشغيل بايبلاين الفيديو كامل مع فحص مسبق:
- يتحقق من ffmpeg
- يتأكد من وجود المجلدات الأساسية
- يفحص توفر الأدوات عبر quick_diagnose()
- خيار لتوليد صور بديلة (Placeholders) لتجاوز خطوة توليد الصور السحابية
- يشغّل core_engine لإنتاج الفيديو النهائي
"""

import os
import sys
import subprocess
from pathlib import Path

# اجعل جذر المشروع على مسار الاستيراد (من جذر هذا الملف)
sys.path.append(str(Path(__file__).parent.resolve()))

from src.core.core_engine import run_full_generation, quick_diagnose

# -----------------------------
# إعداد المسارات الأساسية
# -----------------------------
IMAGES_DIR = Path("content_studio/ai_images/outputs/")
VOICE_DIR  = Path("content_studio/ai_voice/voices/")
VOICE_PATH = VOICE_DIR / "final_voice.mp3"
FINAL_DIR  = Path("content_studio/ai_video/final_videos/")

REQUIRED_DIRS = [IMAGES_DIR, VOICE_DIR, FINAL_DIR]

# -----------------------------
# فحوصات مسبقة (Preflight)
# -----------------------------
def check_ffmpeg() -> None:
    """يتأكد أن ffmpeg متاح في PATH قبل تشغيل MoviePy."""
    try:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if out.returncode != 0:
            raise RuntimeError("ffmpeg موجود لكن يرجّع كود غير صفري.")
        print("✅ ffmpeg متوفر.")
    except FileNotFoundError:
        raise SystemExit("❌ ffmpeg غير مثبت/غير موجود في PATH. ثبّته ثم أعد المحاولة.")

def ensure_dirs() -> None:
    """ينشئ المجلدات الأساسية إذا كانت مفقودة."""
    for d in REQUIRED_DIRS:
        if not d.exists():
            print(f"ℹ إنشاء المجلد: {d}")
            d.mkdir(parents=True, exist_ok=True)
    print("✅ المجلدات الأساسية جاهزة.")

def preflight_quick_diagnose() -> None:
    """يعرض تشخيص سريع ويتحقق من توفر الأدوات."""
    diag = quick_diagnose()
    print("🔎 Quick Diagnose:", diag, flush=True)

    missing = diag.get("tools_missing", [])
    if missing:
        raise SystemExit(
            f"❌ مكونات ناقصة/مسارات خاطئة: {missing}\n"
            "↪ تأكد من مسارات ملفات: script_generator / image_generator / voice_generator / video_composer"
        )

def optional_clean_images() -> None:
    """تنظيف صور قديمة (اختياري)."""
    if IMAGES_DIR.exists():
        for f in IMAGES_DIR.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass
    print("🧹 تم تنظيف صور الإخراج السابقة (إن وجدت).")

# -----------------------------
# (جديد) صور بديلة لاختبار البايبلاين بدون OpenAI Images
# -----------------------------
SEED_PLACEHOLDERS = True   # خلّيه True للاختبار. إذا فعّلت توليد الصور السحابي خليها False.

def _seed_placeholder_images(n: int = 5, size=(1024, 1024)) -> None:
    """ينشئ صور Placeholder محليًا داخل IMAGES_DIR."""
    from PIL import Image, ImageDraw, ImageFont  # يعتمد على Pillow
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # نظّف القديم
    for f in IMAGES_DIR.glob("*"):
        try:
            f.unlink()
        except Exception:
            pass

    for i in range(n):
        img = Image.new("RGB", size, (20, 24, 28))
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 64)
        except Exception:
            font = ImageFont.load_default()
        text = f"Scene {i+1}\n(placeholder)"
        # تمركز بسيط للنص
        d.multiline_text(
            (size[0] // 6, size[1] // 3),
            text,
            fill=(230, 230, 230),
            font=font,
            align="center"
        )
        (IMAGES_DIR / f"scene_{i+1}.png").parent.mkdir(parents=True, exist_ok=True)
        img.save(IMAGES_DIR / f"scene_{i+1}.png")

# -----------------------------
# نقطة التشغيل
# -----------------------------
# ... نفس الاستيرادات/الفحوصات عندك ...

if __name__ == "__main__":
    # فحوصاتك المعتادة (ffmpeg, ensure_dirs, quick_diagnose, ...)

    override_script = """Title: Start Your Sport Today
Scene 1: A quiet sunrise — "Every beginning is one small step."
Scene 2: Running track — "Start simple. Keep moving."
Scene 3: A smile — "Consistency beats perfection."
Closing: Try 10 minutes today.
"""

    user_data = {"name": "Guest", "traits": {"tone": "emotional"}}

    result = run_full_generation(
        user_data=user_data,
        lang="en",                # ⬅️ تشغيل كل شيء إنجليزي
        image_duration=4,
        override_script=override_script,
        mute_if_no_voice=True,
        skip_cleanup=True
    )
    print("Video:", result.get("video"))


    # 3) (اختبار) ازرع صور Placeholder بدل توليد الصور السحابي
    if SEED_PLACEHOLDERS:
        print("🧪 Seeding placeholder images (skipping OpenAI images)…", flush=True)
        try:
            _seed_placeholder_images(n=5)  # غيّر العدد لو حاب
        except Exception as e:
            print(f"⚠ فشل إنشاء صور Placeholder: {e}. سنكمل على أي حال.", flush=True)

    # 4) إمّا نستخدم سكربت جاهز (override_script) أو نولّد تلقائيًا من user_data
    override_script = """عنوان: ابدأ رياضتك اليوم
المشهد 1: شروق هادئ — "كل بداية خطوة"
المشهد 2: مضمار جري — "ابدأ بخطوة بسيطة"
المشهد 3: ابتسامة — "الاستمرارية أهم من الكمال"
الخاتمة: جرّب 10 دقائق اليوم.
"""

    # لو تبغى توليد تلقائي من دوال السكربت عندك، خلّي override_script = None
    # override_script = None

    user_data = {
        "name": "Guest",
        "traits": {
            "quality_level": "جيدة",
            "target_audience": "عام",
            "creative": True
        }
    }

    print("🎞 بدء إنتاج الفيديو...", flush=True)
    try:
        result = run_full_generation(
            user_data=user_data,
            lang="ar",
            image_duration=4,
            override_script=override_script,  # غيّرها إلى None لتجربة توليد السكربت تلقائيًا
            mute_if_no_voice=True,            # كمّل بدون صوت لو ما وُجد ملف صوت
            skip_cleanup=True                 # لأننا نظّفنا الصور يدويًا فوق
        )
    except Exception as e:
        print(f"💥 استثناء غير متوقع: {e}", flush=True)
        sys.exit(1)

    if result.get("error"):
        print("❌ خطأ أثناء الإنتاج:", result["error"], flush=True)
        sys.exit(1)

    print("\n✅ تم الإنتاج بنجاح:", flush=True)
    print("📜 Script:\n", (result.get("script") or "")[:200],
          "..." if result.get("script") and len(result["script"]) > 200 else "", flush=True)
    print("🖼 Images:", result.get("images"), flush=True)
    print("🔊 Voice:", result.get("voice"), flush=True)
    print("🎞 Video:", result.get("video"), flush=True)
    print("\n📂 ستجد الملف داخل:", FINAL_DIR.resolve(), flush=True)
