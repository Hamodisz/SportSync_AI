# -- coding: utf-8 --
"""
فيديو تجريبي بسيط - Demo سريع لـ SportSync
"""
import sys
from pathlib import Path

# إضافة المشروع للمسار
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips
from gtts import gTTS
import os

# المسارات
OUTPUT_DIR = Path("content_studio/ai_video/final_videos")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("🎬 بدء توليد فيديو SportSync Demo...")
print("=" * 60)

# ===== 1. إنشاء الصور =====
print("\n📸 إنشاء الصور...")

scenes = [
    {
        "title": "المشهد 1",
        "text": "أنت لست كسولاً\nأنت فقط لم تلتقِ برياضتك بعد",
        "color": (25, 35, 45)
    },
    {
        "title": "المشهد 2", 
        "text": "SportSync يحلل\n141 طبقة من شخصيتك",
        "color": (35, 45, 55)
    },
    {
        "title": "المشهد 3",
        "text": "3 توصيات دقيقة\nواقعية • بديلة • إبداعية",
        "color": (45, 55, 65)
    },
    {
        "title": "المشهد 4",
        "text": "رياضتك أنت\nالمكتوبة في DNA حركتك",
        "color": (55, 65, 75)
    }
]

image_paths = []
for i, scene in enumerate(scenes):
    # إنشاء صورة
    img = Image.new("RGB", (1080, 1920), scene["color"])
    draw = ImageDraw.Draw(img)
    
    # الخطوط
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
        font_text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 120)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    # رسم النص
    # العنوان في الأعلى
    draw.text((540, 300), scene["title"], fill=(180, 180, 180), 
              font=font_title, anchor="mm")
    
    # النص الأساسي في المنتصف
    draw.multiline_text((540, 960), scene["text"], fill=(255, 255, 255), 
                       font=font_text, anchor="mm", align="center", spacing=40)
    
    # حفظ الصورة
    img_path = OUTPUT_DIR / f"scene_{i+1}.png"
    img.save(img_path)
    image_paths.append(str(img_path))
    print(f"  ✅ {scene['title']}")

# ===== 2. إنشاء الصوت =====
print("\n🔊 إنشاء الصوت...")
voice_text = """
أنت لست كسولاً، أنت فقط لم تلتقِ برياضتك بعد.
SportSync يحلل 141 طبقة من شخصيتك ويكشف المحرك الصامت داخلك.
ثلاث توصيات دقيقة: واقعية، بديلة، وإبداعية.
رياضتك أنت، المكتوبة في DNA حركتك.
SportSync - اكتشف من أنت عن طريق الحركة.
"""

try:
    tts = gTTS(text=voice_text.strip(), lang='ar', slow=False)
    voice_path = OUTPUT_DIR / "demo_voice.mp3"
    tts.save(str(voice_path))
    print(f"  ✅ تم حفظ الصوت")
    has_audio = True
except Exception as e:
    print(f"  ⚠️  فشل إنشاء الصوت: {e}")
    has_audio = False

# ===== 3. إنشاء الفيديو =====
print("\n🎞  تجميع الفيديو...")

try:
    # إنشاء كليبات الصور
    clips = []
    duration_per_image = 4  # 4 ثواني لكل صورة
    
    for img_path in image_paths:
        clip = ImageClip(img_path).with_duration(duration_per_image)
        clips.append(clip)
    
    # دمج الكليبات
    final_video = concatenate_videoclips(clips, method="compose")
    
    # إضافة الصوت إذا كان متاحاً
    if has_audio and voice_path.exists():
        from moviepy import AudioFileClip
        audio = AudioFileClip(str(voice_path))
        final_video = final_video.with_audio(audio)
    
    # حفظ الفيديو
    output_path = OUTPUT_DIR / "sportsync_demo.mp4"
    final_video.write_videofile(
        str(output_path),
        fps=24,
        codec='libx264',
        audio_codec='aac' if has_audio else None,
        preset='medium',
        threads=4
    )
    
    print("\n" + "=" * 60)
    print("✅ تم إنتاج الفيديو بنجاح!")
    print("=" * 60)
    print(f"\n📂 مسار الفيديو:")
    print(f"   {output_path.resolve()}")
    print(f"\n📊 التفاصيل:")
    print(f"   • المدة: {len(scenes) * duration_per_image} ثانية")
    print(f"   • الصور: {len(scenes)} صورة")
    print(f"   • الصوت: {'نعم ✅' if has_audio else 'لا ❌'}")
    print(f"   • الحجم: {output_path.stat().st_size / (1024*1024):.2f} MB")
    print("\n🎉 افتح الملف وشاهد النتيجة!")
    
except Exception as e:
    print(f"\n❌ خطأ في إنتاج الفيديو: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
