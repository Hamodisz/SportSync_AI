# app.py

import streamlit as st
import json

from core.backend_gpt import generate_sport_recommendation
from core.dynamic_chat import start_dynamic_chat
from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from core.user_logger import log_user_insight

# -------------------
# اللغة
# -------------------
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"])
is_arabic = (lang == "العربية")

# -------------------
# تحميل الأسئلة
# -------------------
question_file = "questions/arabic_questions.json" if is_arabic else "questions/english_questions.json"
with open(question_file, "r", encoding="utf-8") as f:
    questions = json.load(f)

# -------------------
# العنوان
# -------------------
st.title("🎯 توصيتك الرياضية الذكية" if is_arabic else "🎯 Your Smart Sport Recommendation")

# -------------------
# جمع الإجابات
# -------------------
answers = {}
for q in questions:
    q_key = q["key"]
    q_text = q["question_ar"] if is_arabic else q["question_en"]
    q_type = q["type"]
    allow_custom = q.get("allow_custom", False)
    options = q.get("options", [])

    if q_type == "multiselect":
        selected = st.multiselect(q_text, options, key=q_key)
        if allow_custom:
            custom_input = st.text_input("✏ " + ("إجابتك الخاصة (اختياري)" if is_arabic else "Your own answer (optional)"), key=q_key+"_custom")
            if custom_input:
                selected.append(custom_input)
        answers[q_text] = selected

    elif q_type == "text":
        answers[q_text] = st.text_input(q_text, key=q_key)

# -------------------
# زر التوصية
# -------------------
if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
    user_id = "test_user"

    # ✅ توليد التوصيات
    recs = generate_sport_recommendation(answers, lang=lang)

    # ✅ تحليل Layer Z
    silent_drivers = analyze_silent_drivers(answers, lang=lang)
    if silent_drivers:
        st.markdown("---")
        st.subheader("🧭 ما يحركك دون أن تدري" if is_arabic else "🧭 Your Silent Drivers")
        for s in silent_drivers:
            st.write("• " + s)

    # ✅ عرض التوصيات الثلاثة
    for i, rec in enumerate(recs):
        if is_arabic:
            st.subheader(f"🟢 التوصية رقم {i+1}" if i == 0 else f"🌿 التوصية رقم {i+1}" if i == 1 else f"🔮 التوصية رقم {i+1} (ابتكارية)")
        else:
            st.subheader(f"🟢 Recommendation #{i+1}" if i == 0 else f"🌿 Recommendation #{i+1}" if i == 1 else f"🔮 Recommendation #{i+1} (Creative)")
        st.write(rec)

        # تقييم المستخدم لكل توصية
        rating = st.slider("⭐ " + ("قيّم هذه التوصية" if is_arabic else "Rate this recommendation"), 1, 5, key=f"rating_{i}")
        st.session_state[f"rating_{i}"] = rating

    # ✅ محادثة ديناميكية مع المدرب
    st.markdown("---")
    st.subheader("🧠 تحدث مع المدرب الذكي" if is_arabic else "🧠 Talk to the AI Coach")
    user_input = st.text_input("💬 اكتب ردّك أو تعليقك هنا..." if is_arabic else "💬 Type your response or ask a question...")

    if user_input:
        prev_ratings = [st.session_state.get(f"rating_{i}", 3) for i in range(3)]
        reply = start_dynamic_chat(
            answers=answers,
            previous_recommendation=recs,
            ratings=prev_ratings,
            user_id=user_id,
            lang=lang,
            chat_history=[],
            user_message=user_input
        )
        st.markdown("🤖 AI Coach:")
        st.success(reply)

    # ✅ توقيع البراند
    st.markdown("---")
    st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")

    # ✅ زر المشاركة
    st.markdown("📤 شارك هذا التحليل مع صديق!" if is_arabic else "📤 Share this analysis with a friend!")
    share_text = f"https://sportsync.ai/recommendation?lang={lang}&user=test_user"
    st.code(share_text)

# -------------------
# إعادة الاختبار
# -------------------
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart the test"):
    st.session_state.clear()
    st.experimental_rerun()
