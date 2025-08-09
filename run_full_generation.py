# -- coding: utf-8 --
"""
تشغيل بايبلاين الفيديو كامل مع فحص مسبق:
- يتحقق من ffmpeg
- يتأكد من وجود المجلدات الأساسية
- يفحص توفر الدوال المطلوبة عبر quick_diagnose()
- يشغّل core_engine لإنتاج الفيديو
"""

import os
import sys
import subprocess
from pathlib import Path

# ===== تحسينات خاصة بويندوز =====
if os.name == "nt":
    # تأكد أن الإخراج يدعم العربية
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    # تغيير Code Page إلى UTF-8 (لا يضر لو كانت مضبوطة مسبقًا)
    try:
        os.system("chcp 65001 >NUL")
    except Exception:
        pass
# ===============================

# ✅ اسمح بالاستيراد من المشروع كله (من جذر الملف الحالي)
sys.path.append(str(Path(_file_).parent.resolve()))

from core.core_engine import run_full_generation, quick_diagnose

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
        raise SystemExit(
            "❌ ffmpeg غير مثبت/غير موجود في PATH على ويندوز.\n"
            "↪ نزّله من https://ffmpeg.org/download.html وأضِف مجلد bin إلى PATH، ثم أعد التشغيل."
        )

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
# نقطة التشغيل
# -----------------------------
if _name_ == "_main_":
    print("🚀 RUN START", flush=True)

    # 0) فحص متغير المفتاح (تنبيهي فقط — لا نوقف التنفيذ)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠ تنبيه: OPENAI_API_KEY غير مضبوط — لو تولّد صور/نص من OpenAI قد يفشل.", flush=True)

    # 1) فحص ffmpeg + المجلدات + التشخيص
    check_ffmpeg()
    ensure_dirs()
    preflight_quick_diagnose()
    optional_clean_images()  # تقدر تعلّقها لو تبغى تحتفظ بالصور القديمة

    # 2) إمّا نستخدم سكربت جاهز (override_script) أو نولّد تلقائيًا من user_data
    override_script = """عنوان: ابدأ رياضتك اليوم
المشهد 1: شروق هادئ — "كل بداية خطوة"
المشهد 2: مضمار جري — "ابدأ بخطوة بسيطة"
المشهد 3: ابتسامة — "الاستمرارية أهم من الكمال"
الخاتمة: جرّب 10 دقائق اليوم.
"""

    # لو تبي تختبر توليد السكربت تلقائي بدون نص جاهز، خلّي override_script = None
    # override_script = None

    user_data = {
        "name": "Guest",
        "traits": {
            "quality_level": "جيدة",
            "target_audience": "عام",
            "creative": True
        }
    }

    print("🚀 بدء إنتاج الفيديو...", flush=True)
    try:
        result = run_full_generation(
            user_data=user_data,
            lang="ar",
            image_duration=4,
            override_script=override_script,  # غيّرها إلى None لتجربة توليد السكربت تلقائيًا
            mute_if_no_voice=True,            # كمّل بدون صوت لو gTTS فشل/النت ضعيف
            skip_cleanup=True                 # ما ننظّف داخل core (نظّفنا قبل)
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
