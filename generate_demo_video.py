# -- coding: utf-8 --
"""
توليد فيديو تجريبي لـ SportSync AI
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.resolve()))

from core.core_engine import run_full_generation

# سكربت تجريبي مقنع عن SportSync
demo_script = """عنوان: اكتشف رياضتك الحقيقية

المشهد 1: شخص يجلس بهدوء، ينظر للأفق
"أنت لست كسولاً... أنت فقط لم تلتقِ برياضتك بعد"

المشهد 2: شاشة تحليل ذكية مع أيقونات نفسية
"SportSync يحلل 141 طبقة من شخصيتك - يكشف المحرك الصامت داخلك"

المشهد 3: ثلاث بطاقات رياضية بتصاميم مختلفة
"3 توصيات دقيقة: واقعية، بديلة، إبداعية - واحدة منهم راح تغير حياتك"

المشهد 4: شخص يبتسم وهو يمارس رياضته
"مو رياضة عشوائية... رياضتك أنت - المكتوبة في DNA حركتك"

الخاتمة: شعار SportSync مع رسالة
"SportSync - اكتشف من أنت عن طريق الحركة"
"""

user_data = {
    "name": "Demo User",
    "traits": {
        "tone": "emotional",
        "target": "general_audience"
    }
}

print("🎬 بدء توليد فيديو SportSync التجريبي...")
print("=" * 60)

try:
    result = run_full_generation(
        user_data=user_data,
        lang="ar",
        image_duration=5,  # 5 ثواني لكل صورة
        override_script=demo_script,
        mute_if_no_voice=True,
        skip_cleanup=True
    )
    
    if result.get("error"):
        print(f"\n❌ خطأ: {result['error']}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ تم إنتاج الفيديو بنجاح!")
    print("=" * 60)
    print(f"\n📜 السكربت: {len(result.get('script', ''))} حرف")
    print(f"🖼  الصور: {len(result.get('images', []))} صورة")
    print(f"🔊 الصوت: {result.get('voice', 'لا يوجد')}")
    print(f"🎞  الفيديو: {result.get('video')}")
    print("\n📂 مسار الفيديو الكامل:")
    print(f"   {Path(result.get('video')).resolve()}")
    print("\n🎉 افتح الملف وشاهد النتيجة!")
    
except Exception as e:
    print(f"\n💥 استثناء: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
