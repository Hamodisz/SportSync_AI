# ========================================================
# 📁 File: agents/marketing/video_pipeline/image_generator.py
# 🎯 Purpose: توليد الصور الذكية تلقائيًا من السكربت النصي
# ⚙ Author: SportSync AI Engineering Team
# 🔐 Version: 1.0 - Production Grade
# ========================================================

import logging
from pathlib import Path
import shutil
import uuid
from typing import List

# مسارات النظام القياسية (قابلة للتعديل حسب بيئة التشغيل)
OUTPUT_DIR = Path("content_studio/ai_images/outputs/")
SAMPLE_IMAGES_DIR = Path("sample_assets/images/")  # مجلد صور احتياطية مؤقتة

def generate_images(script: str, lang: str = "en") -> List[str]:
    """
    🎨 توليد صور ذكية بناءً على النص المقدم.
    
    ✅ حالياً يقوم بنسخ صور تجريبية من مجلد sample_assets لأغراض التطوير.
    ❗ في النسخ المستقبلية، يمكن استبدال هذا الجزء بواجهة OpenAI أو Stable Diffusion أو أي API آخر.

    Args:
        script (str): النص الكامل للسكربت المراد تحويله إلى صور.
        lang (str): اللغة المستهدفة (ar أو en).

    Returns:
        List[str]: قائمة المسارات المطلقة للصور التي تم توليدها.
    """
    
    logging.info("🚀 [Image Generation] Starting image generation process...")
    logging.debug(f"📝 Script: {script[:100]}...")  # عرض أول 100 حرف فقط للحماية
    logging.debug(f"🌐 Language: {lang}")

    try:
        # 1️⃣ تأكد من وجود مجلد الإخراج
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 2️⃣ نظّف الصور السابقة (اختياري حسب الحاجة)
        for old_file in OUTPUT_DIR.glob("*"):
            old_file.unlink()

        # 3️⃣ تحقق من وجود صور مؤقتة للتجريب
        if not SAMPLE_IMAGES_DIR.exists():
            raise FileNotFoundError("❌ مجلد الصور التجريبية غير موجود: sample_assets/images/")

        sample_images = list(SAMPLE_IMAGES_DIR.glob("*.png"))
        if not sample_images:
            raise FileNotFoundError("🚫 لم يتم العثور على صور داخل sample_assets/images/")

        # 4️⃣ انسخ الصور إلى مجلد الإخراج بأسماء عشوائية
        generated_paths = []
        for i, image in enumerate(sample_images):
            new_name = f"img_{uuid.uuid4().hex[:8]}.png"
            destination = OUTPUT_DIR / new_name
            shutil.copy(image, destination)
            generated_paths.append(str(destination))
            logging.debug(f"✅ Copied image: {destination}")

        logging.info(f"✅ [Image Generation] Successfully generated {len(generated_paths)} images.")
        return generated_paths

    except Exception as e:
        logging.error(f"❌ [Image Generation] Failed to generate images: {e}")
        return []
