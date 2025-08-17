# quiz_service/app.py
# -- coding: utf-8 --

import os, sys, json
from pathlib import Path
import streamlit as st

# ---------- مسارات آمنة حتى لو _file_ غير معرّف ----------
try:
    HERE = Path(_file_).resolve().parent
except NameError:
    HERE = Path.cwd()

ROOT = HERE.parent              # جذر المشروع (أبو مجلد quiz_service)
QUESTIONS_DIR = ROOT / "questions"
CORE_DIR = ROOT / "core"
ANALYSIS_DIR = ROOT / "analysis"

# أضف المسارات لبايثون
for p in (CORE_DIR, ANALYSIS_DIR, ROOT):
    sp = str(p.resolve())
    if sp not in sys.path:
        sys.path.insert(0, sp)

# ---------- استيراد الوحدات الداخلية بأمان ----------
def _missing_dep(msg):
    st.error(msg)
    st.stop()

try:
    from core.backend_gpt import generate_sport_recommendation
except Exception as e:
    _missing_dep(f"لا يمكن استيراد generate_sport_recommendation من core/backend_gpt.py\nتفاصيل: {e}")

try:
    from core.dynamic_chat import start_dynamic_chat
except Exception as e:
    _missing_dep(f"لا يمكن استيراد start_dynamic_chat من core/dynamic_chat.py\nتفاصيل: {e}")

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception as e:
    _missing_dep(f"لا يمكن استيراد analyze_silent_drivers من analysis/layer_z_engine.py\nتفاصيل: {e}")

# ---------- واجهة ----------
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"])
is_arabic = (lang == "العربية")

st.title("🎯 توصيتك الرياضية الذكية" if is_arabic else "🎯 Your Smart Sport Recommendation")

# ---------- تحميل الأسئلة ----------
ar_file = QUESTIONS_DIR / "arabic_questions.json"
en_file = QUESTIONS_DIR / "english_questions.json"
q_path = ar_file if is_arabic else en_file

if not q_path.exists():
    _missing_dep(f"ملف الأسئلة غير موجود: {q_path}")

try:
    questions = json.loads(q_path.read_text(encoding="utf-8"))
except Exception as e:
    _missing_dep(f"تعذّر قراءة ملف الأسئلة {q_path.name}: {e}")

# ---------- جمع الإجابات ----------
answers = {}
for q in questions:
    q_key = q["key"]
    q_text = q["question_ar"] if is_arabic else q["question_en"]
    q_type = q.get("type", "text")
    allow_custom = q.get("allow_custom", False)
    options = q.get("options", [])

    if q_type == "multiselect":
        selected = st.multiselect(q_text, options, key=q_key)
        if allow_custom:
            label = "إجابتك الخاصة (اختياري)" if is_arabic else "Your own answer (optional)"
            custom_input = st.text_input("✏ " + label, key=q_key + "_custom")
            if custom_input:
                selected.append(custom_input)
        answers[q_text] = selected
    else:
        answers[q_text] = st.text_input(q_text, key=q_key)

# ---------- زر التوصية ----------
if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
    user_id = "test_user"

    # 1) توصيات
    recs = generate_sport_recommendation(answers, lang=lang)

    # 2) Layer Z
    silent = analyze_silent_drivers(answers, lang=lang)
    if silent:
        st.markdown("---")
        st.subheader("🧭 ما يحركك دون أن تدري" if is_arabic else "🧭 Your Silent Drivers")
        for s in silent:
            st.write("• " + s)

    # 3) عرض 3 توصيات + تقييم
    for i, rec in enumerate(recs[:3]):
        if is_arabic:
            title = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"][i]
        else:
            title = ["🟢 Recommendation #1", "🌿 Recommendation #2", "🔮 Recommendation #3 (Creative)"][i]
        st.subheader(title)
        st.write(rec)
        st.session_state[f"rating_{i}"] = st.slider(
            "⭐ " + ("قيّم هذه التوصية" if is_arabic else "Rate this recommendation"),
            1, 5, 4, key=f"rating_slider_{i}"
        )

    # 4) محادثة ديناميكية
    st.markdown("---")
    st.subheader("🧠 تحدث مع المدرب الذكي" if is_arabic else "🧠 Talk to the AI Coach")
    prompt_lbl = "💬 اكتب ردّك أو تعليقك هنا..." if is_arabic else "💬 Type your response or ask a question..."
    user_input = st.text_input(prompt_lbl)

    if user_input:
        prev_ratings = [st.session_state.get(f"rating_{i}", 3) for i in range(3)]
        reply = start_dynamic_chat(
            answers=answers,
            previous_recommendation=recs[:3],
            ratings=prev_ratings,
            user_id=user_id,
            lang=lang,
            chat_history=[],
            user_message=user_input
        )
        st.markdown("🤖 AI Coach:")
        st.success(reply)

    # ترويسة بسيطة
    st.markdown("---")
    st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")

    # مشاركة
    share_text = f"https://sportsync.ai/recommendation?lang={lang}&user=test_user"
    st.code(share_text)

# ---------- إعادة الاختبار ----------
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart the test"):
    st.session_state.clear()
    st.rerun()
