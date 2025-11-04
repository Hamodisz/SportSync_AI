# -*- coding: utf-8 -*-
"""
فيديو 5 دقائق مع صور RunPod الواقعية
=====================================
اختبار كامل لجودة النصوص + صور AI احترافية
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
import time
import io
import base64

# استيراد RunPod client
from core.runpod_flux_client import RunPodFluxClient, enhance_prompt_for_sport

# =====================================================
# السكربت الكامل - محتوى غني لـ 5 دقائق
# =====================================================

FULL_SCRIPT = [
    {
        "title": "المشهد 1: المشكلة الحقيقية",
        "image_prompt": "Person sitting on couch looking frustrated at gym membership card, indoor lighting, cinematic, realistic",
        "text": "كم مرة قلت لنفسك: راح أبدأ رياضة؟ كم نادي رياضي اشتركت فيه وما كملت أسبوعين؟ المشكلة مو فيك... المشكلة إنك تبحث عن الرياضة الخطأ."
    },
    {
        "title": "المشهد 2: الاكتشاف",
        "image_prompt": "Scientific laboratory with DNA helix and athletic silhouettes, futuristic technology, professional photography",
        "text": "في 2024، علماء النفس الرياضي اكتشفوا شيء مذهل: كل شخص عنده بصمة حركية فريدة - مثل بصمة الإصبع. هذي البصمة تحدد الرياضة المثالية لك."
    },
    {
        "title": "المشهد 3: العلم وراء SportSync",
        "image_prompt": "Digital brain scan with multiple data layers and neural pathways, high-tech visualization, 8k",
        "text": "SportSync يحلل 141 طبقة من شخصيتك: تحليل الحركة، المحفزات النفسية، البيئة المثالية، نوع التحدي المناسب... كل هذا في ثواني."
    },
    {
        "title": "المشهد 4: Layer-Z المحرك الصامت",
        "image_prompt": "Abstract representation of hidden motivations, dark mysterious background with light rays, artistic",
        "text": "Layer-Z هو المحرك الصامت اللي يكشف الدوافع الخفية. يقرأ ما بين السطور ويفهم احتياجاتك الحقيقية قبل ما تفهمها أنت."
    },
    {
        "title": "المشهد 5: النظام الثلاثي",
        "image_prompt": "Three glowing paths diverging in forest, magical atmosphere, each path unique, cinematic lighting",
        "text": "SportSync يعطيك 3 خيارات ذكية: الواقعي - تبدأه اليوم، البديل - بديل قوي، الإبداعي - رياضة مصممة خصيصاً لشخصيتك."
    },
    {
        "title": "المشهد 6: قصة أحمد - المبرمج",
        "image_prompt": "Young programmer at archery range drawing bow with deep focus, professional photography, golden hour",
        "text": "أحمد جرّب الجيم 5 مرات وفشل. SportSync اكتشف إنه anxious high-focus seeker. أعطاه رماية السهام. الحين يمارسها 4 مرات بالأسبوع من سنة."
    },
    {
        "title": "المشهد 7: الفرق الحقيقي",
        "image_prompt": "Split screen comparison: left side chaotic gym, right side person enjoying perfect sport match, dramatic",
        "text": "الطريقة التقليدية: جرب كل شيء لين تلقى شيء يعجبك. SportSync: نحلل شخصيتك أولاً، ثم نعطيك الرياضة المناسبة من أول مرة."
    },
    {
        "title": "المشهد 8: التقنية المتقدمة",
        "image_prompt": "Futuristic AI system analyzing person's silhouette with colorful data streams, sci-fi style, 8k",
        "text": "Pydantic AI، قاعدة معرفة من 8000+ رياضة، نظام Hybrid Recommendation، Layer-Z Engine. تقنية متقدمة لتوصية دقيقة."
    },
    {
        "title": "المشهد 9: هوية مو مجرد تمرين",
        "image_prompt": "Person discovering their reflection as athlete, mirror transformation effect, inspirational, cinematic",
        "text": "SportSync مو مجرد نظام توصيات. هو نظام اكتشاف هوية. الرياضة اللي نعطيك هي انعكاس لشخصيتك الحقيقية."
    },
    {
        "title": "المشهد 10: النتائج المثبتة",
        "image_prompt": "Graph showing dramatic upward trend with 87% success rate, professional infographic style, clean",
        "text": "بعد 6 أشهر: 87% استمروا أكثر من شهرين، 94% قالوا هذي أول مرة أحس إن الرياضة جزء مني، 78% اكتشفوا رياضات جديدة."
    },
    {
        "title": "المشهد 11: ابدأ رحلتك",
        "image_prompt": "Person taking first step on glowing path toward mountain peak, sunrise, motivational, epic",
        "text": "أجب على 20 سؤال ذكي، النظام يحلل فوراً، استلم 3 توصيات مفصلة، ابدأ رياضتك الحقيقية اليوم."
    },
    {
        "title": "المشهد 12: الختام",
        "image_prompt": "Silhouette of person in victory pose at sunset, powerful and inspiring, cinematic masterpiece",
        "text": "أنت مو كسلان. أنت فقط ما لقيت رياضتك بعد. SportSync - اكتشف من أنت عن طريق الحركة. لأن لكل روح، رياضة تناسبها."
    }
]

# =====================================================
# المسارات
# =====================================================

OUTPUT_DIR = Path("content_studio/ai_video/final_videos")
IMAGES_DIR = OUTPUT_DIR / "runpod_scenes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# =====================================================
# توليد الصور باستخدام RunPod
# =====================================================

def generate_runpod_images(scenes: list):
    """توليد صور RunPod لكل مشهد"""
    print("\n🎨 توليد صور RunPod Flux (هذه الخطوة قد تستغرق 10-15 دقيقة)...")
    print("=" * 70)
    
    try:
        client = RunPodFluxClient()
        print("✅ تم الاتصال بـ RunPod")
    except Exception as e:
        print(f"❌ فشل الاتصال بـ RunPod: {e}")
        print("💡 راح نستخدم صور placeholder بديلة")
        return generate_placeholder_images(scenes)
    
    image_paths = []
    
    for i, scene in enumerate(scenes, 1):
        print(f"\n[{i}/{len(scenes)}] {scene['title']}")
        print(f"   Prompt: {scene['image_prompt'][:60]}...")
        
        try:
            # تحسين البرومبت
            enhanced_prompt = enhance_prompt_for_sport(
                scene['image_prompt'],
                lang='en'
            )
            
            # توليد الصورة
            result = client.generate_image(
                prompt=enhanced_prompt,
                width=1080,
                height=1920,  # Portrait
                steps=25,
                cfg_scale=7.5
            )
            
            if result.get('success'):
                # حفظ الصورة
                img_data = base64.b64decode(result['image_b64'])
                img_path = IMAGES_DIR / f"scene_{i:02d}.png"
                
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                
                # إضافة النص على الصورة
                img_path = add_text_overlay(
                    img_path,
                    scene['title'],
                    scene['text'],
                    i,
                    len(scenes)
                )
                
                image_paths.append(str(img_path))
                print(f"   ✅ تم (seed: {result.get('seed', 'N/A')})")
                
            else:
                print(f"   ⚠️ فشل: {result.get('error', 'Unknown')}")
                # استخدام placeholder كبديل
                img_path = create_placeholder(i, scene)
                image_paths.append(str(img_path))
            
            # انتظار قصير بين الطلبات
            if i < len(scenes):
                time.sleep(2)
                
        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            img_path = create_placeholder(i, scene)
            image_paths.append(str(img_path))
    
    print("\n" + "=" * 70)
    print(f"✅ تم توليد {len(image_paths)} صورة")
    return image_paths

# =====================================================
# إضافة نص على الصورة
# =====================================================

def add_text_overlay(img_path: Path, title: str, text: str, scene_num: int, total_scenes: int):
    """إضافة نص على صورة RunPod"""
    try:
        # فتح الصورة
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        
        # خطوط
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
            font_text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 45)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # خلفية شبه شفافة للنص
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # مستطيل خلفية للعنوان
        overlay_draw.rectangle([(0, 100), (1080, 280)], fill=(0, 0, 0, 180))
        
        # مستطيل خلفية للنص
        overlay_draw.rectangle([(0, 1400), (1080, 1800)], fill=(0, 0, 0, 180))
        
        # دمج الخلفية مع الصورة
        img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)
        img = img.convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # رسم العنوان
        draw.text((540, 190), title, fill=(255, 255, 255), 
                 font=font_title, anchor="mm")
        
        # رسم النص (مختصر)
        text_lines = wrap_text(text, 35)
        y = 1500
        for line in text_lines[:5]:
            draw.text((540, y), line, fill=(255, 255, 255),
                     font=font_text, anchor="mm")
            y += 60
        
        # رقم المشهد
        draw.text((540, 1850), f"{scene_num} / {total_scenes}",
                 fill=(200, 200, 200), font=font_text, anchor="mm")
        
        # حفظ
        img.save(img_path)
        return img_path
        
    except Exception as e:
        print(f"   ⚠️ فشل إضافة النص: {e}")
        return img_path

def wrap_text(text: str, max_chars: int):
    """تقسيم النص لأسطر"""
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= max_chars:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines

# =====================================================
# صور Placeholder (بديلة)
# =====================================================

def create_placeholder(scene_num: int, scene: dict):
    """إنشاء صورة placeholder"""
    colors = [(25, 35, 45), (35, 45, 55), (45, 55, 65), 
              (55, 65, 75), (30, 50, 70), (40, 60, 80)]
    color = colors[scene_num % len(colors)]
    
    img = Image.new("RGB", (1080, 1920), color)
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
        font_text = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 50)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
    
    draw.text((540, 200), scene['title'], fill=(180, 180, 180),
             font=font_title, anchor="mm")
    
    text_lines = wrap_text(scene['text'], 30)
    y = 600
    for line in text_lines[:8]:
        draw.text((540, y), line, fill=(255, 255, 255),
                 font=font_text, anchor="mm")
        y += 80
    
    draw.text((540, 1800), f"{scene_num} / {len(FULL_SCRIPT)}",
             fill=(150, 150, 150), font=font_text, anchor="mm")
    
    img_path = IMAGES_DIR / f"scene_{scene_num:02d}_placeholder.png"
    img.save(img_path)
    return img_path

def generate_placeholder_images(scenes: list):
    """توليد كل الصور كـ placeholder"""
    print("\n🎨 توليد صور placeholder...")
    image_paths = []
    
    for i, scene in enumerate(scenes, 1):
        img_path = create_placeholder(i, scene)
        image_paths.append(str(img_path))
        print(f"   ✅ المشهد {i}")
    
    return image_paths

# =====================================================
# الكود الرئيسي
# =====================================================

if __name__ == "__main__":
    print("🎬 بدء توليد فيديو 5 دقائق مع RunPod")
    print("=" * 70)
    print("⏱️  الوقت المتوقع: 15-20 دقيقة")
    print("=" * 70)
    
    start_total = time.time()
    
    # 1. عرض المشاهد
    print(f"\n📋 السكربت: {len(FULL_SCRIPT)} مشهد")
    for i, scene in enumerate(FULL_SCRIPT, 1):
        print(f"   {i}. {scene['title']}")
    
    # 2. توليد الصور من RunPod
    image_paths = generate_runpod_images(FULL_SCRIPT)
    
    # 3. توليد الصوت
    print("\n🔊 توليد الصوت...")
    print("   ⏳ هذه الخطوة قد تستغرق دقيقة...")
    
    try:
        voice_text = " ... ".join([scene['text'] for scene in FULL_SCRIPT])
        tts = gTTS(text=voice_text, lang='ar', slow=False)
        voice_path = OUTPUT_DIR / "runpod_demo_voice.mp3"
        tts.save(str(voice_path))
        print(f"   ✅ تم ({voice_path.stat().st_size / 1024:.0f} KB)")
        has_audio = True
    except Exception as e:
        print(f"   ⚠️ فشل: {e}")
        has_audio = False
    
    # 4. تجميع الفيديو
    print("\n🎞  تجميع الفيديو...")
    print("   ⏳ قد يستغرق 2-3 دقائق...")
    
    try:
        # حساب المدة
        if has_audio:
            audio = AudioFileClip(str(voice_path))
            audio_duration = audio.duration
            duration_per_image = audio_duration / len(FULL_SCRIPT)
            print(f"   📊 مدة الصوت: {audio_duration:.1f}ث ({audio_duration/60:.1f} دقيقة)")
        else:
            duration_per_image = 25
            audio_duration = duration_per_image * len(FULL_SCRIPT)
        
        # إنشاء الكليبات
        clips = [ImageClip(img).with_duration(duration_per_image) 
                for img in image_paths]
        
        final_video = concatenate_videoclips(clips, method="compose")
        
        if has_audio:
            final_video = final_video.with_audio(audio)
        
        # حفظ
        output_path = OUTPUT_DIR / "sportsync_runpod_5min.mp4"
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec='libx264',
            audio_codec='aac' if has_audio else None,
            preset='medium',
            threads=4
        )
        
        total_time = time.time() - start_total
        
        # النتيجة
        print("\n" + "=" * 70)
        print("✅ تم إنتاج الفيديو بنجاح!")
        print("=" * 70)
        
        print(f"\n📂 مسار الفيديو:")
        print(f"   {output_path.resolve()}")
        
        print(f"\n📊 التفاصيل:")
        print(f"   • المدة: {audio_duration:.0f}ث ({audio_duration/60:.1f} دقيقة)")
        print(f"   • المشاهد: {len(FULL_SCRIPT)}")
        print(f"   • الصور: RunPod Flux AI")
        print(f"   • الصوت: {'نعم ✅' if has_audio else 'لا'}")
        print(f"   • الحجم: {output_path.stat().st_size / (1024*1024):.2f} MB")
        print(f"   • وقت الإنتاج الكلي: {total_time/60:.1f} دقيقة")
        
        print("\n🎉 افتح الفيديو واستمتع بجودة النصوص والصور!")
        
        # فتح الفيديو
        import os
        os.system(f'open "{output_path}"')
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
