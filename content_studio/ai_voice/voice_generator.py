# -- coding: utf-8 --
"""
توليد تعليق صوتي (MP3) من السكربت باستخدام gTTS.
- يجزّئ النص تلقائياً لو كان طويلاً (gTTS لا يحب النصوص الطويلة جداً).
- يجمّع المقاطع الصوتية في ملف واحد عبر MoviePy.
- يعيد المسار الكامل لملف الصوت النهائي.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List

from gtts import gTTS

# مجلدات واسم الملف النهائي
VOICE_DIR = Path("content_studio/ai_voice/voices/")
VOICE_DIR.mkdir(parents=True, exist_ok=True)
VOICE_PATH = VOICE_DIR / "final_voice.mp3"


def _normalize_text(text: str) -> str:
    """تنظيف بسيط للنص قبل الإرسال إلى gTTS."""
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _split_for_tts(text: str, max_chars: int = 220) -> List[str]:
    """
    تقسيم النص إلى قطع قصيرة (آمنة على gTTS).
    نحاول التقسيم على الجُمل، ثم ندمج الجمل الصغار حتى حد max_chars.
    """
    # قسّم على علامات انتهاء الجملة
    # نُبقي العلامة حتى لا تضيع الوقفات الصوتية
    sentences = re.split(r"([\.!\?،…])", text)
    # أعد تركيب الجمل مع علاماتها
    sents: List[str] = []
    buf = ""
    for i in range(0, len(sentences), 2):
        part = sentences[i].strip()
        mark = sentences[i + 1] if i + 1 < len(sentences) else ""
        if not part:
            continue
        sents.append((part + mark).strip())

    # ادمج الجمل الصغيرة ضمن حاويات <= max_chars
    chunks: List[str] = []
    cur = ""
    for s in sents if sents else [text]:
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= max_chars:
            cur = f"{cur} {s}"
        else:
            chunks.append(cur.strip())
            cur = s
    if cur:
        chunks.append(cur.strip())

    # احتياط نهائي لو بقيت قطع طويلة جداً
    out: List[str] = []
    for c in chunks:
        if len(c) <= max_chars:
            out.append(c)
        else:
            # قصّها بالقوة على حدود الكلمات
            words = c.split()
            buf = ""
            for w in words:
                if len(buf) + 1 + len(w) <= max_chars:
                    buf = f"{buf} {w}".strip()
                else:
                    out.append(buf)
                    buf = w
            if buf:
                out.append(buf)
    return out


def generate_voice_from_script(script: str, lang: str = "en") -> str:
    """
    توليد تعليق صوتي من السكربت.
    :param script: نص السكربت الكامل.
    :param lang: 'en' أو 'ar' (أي قيمة لا تبدأ بـ en ستعامل كـ ar).
    :return: مسار ملف MP3 النهائي.
    """
    from moviepy.editor import AudioFileClip, concatenate_audioclips  # import محلي لتسريع التحميل

    lang_code = "en" if str(lang).lower().startswith("en") else "ar"
    text = _normalize_text(script)
    if not text:
        raise ValueError("النص فارغ — لا يمكن توليد صوت.")

    # قسّم النص
    chunks = _split_for_tts(text, max_chars=220)

    # لو قطعة واحدة، أسهل نحفظ مباشرة
    if len(chunks) == 1:
        tts = gTTS(chunks[0], lang=lang_code)
        tts.save(str(VOICE_PATH))
        return str(VOICE_PATH)

    # خلاف ذلك: أنشئ عدة ملفات مؤقتة ثم جمّعها
    tmp_paths: List[Path] = []
    try:
        for i, c in enumerate(chunks, start=1):
            tmp_p = VOICE_DIR / f"piece{i:03d}.mp3"
            gTTS(c, lang=lang_code).save(str(tmp_p))
            tmp_paths.append(tmp_p)

        # اجمع عبر MoviePy
        clips = [AudioFileClip(str(p)) for p in tmp_paths]
        final = concatenate_audioclips(clips)
        final.write_audiofile(str(VOICE_PATH), fps=44100, bitrate="128k", verbose=False, logger=None)

        # أغلق المقاطع لتفريغ المقابض
        for c in clips:
            c.close()
        final.close()

        return str(VOICE_PATH)

    finally:
        # نظّف الملفات المؤقتة إن وُجدت
        for p in tmp_paths:
            try:
                os.remove(p)
            except Exception:
                pass
