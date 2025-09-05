import streamlit as st
import json
import os
import uuid
import urllib.parse

from core.submit_answers_to_queue import submit_to_queue
from core.check_result_ready import check_result

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
# عنوان الصفحة
# -------------------
st.title("🎯 توصيتك الرياضية الذكية" if is_arabic else "🎯 Your Smart Sport Recommendation")

# -------------------
# معالجة user_id من الرابط أو توليد جديد
# -------------------
query_params = st.experimental_get_query_params()
user_id = query_params.get("user_id", [None])[0]

if not user_id:
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:6]}"
    user_id = st.session_state.user_id

# -------------------
# حالة العرض
# -------------------
if "view" not in st.session_state:
    # هل عنده توصية جاهزة؟
    result = check_result(user_id)
    if result:
        st.session_state.result = result
        st.session_state.view = "result"
    elif os.path.exists(f"data/pending_requests/{user_id}.json"):
        st.session_state.view = "waiting"
    else:
        st.session_state.view = "quiz"

# -------------------
# صفحة الأسئلة
# -------------------
if st.session_state.view == "quiz":
    st.session_state.answers = {}
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
            st.session_state.answers[q_text] = selected

        elif q_type == "text":
            st.session_state.answers[q_text] = st.text_input(q_text, key=q_key)

    if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
        submit_to_queue(user_id=user_id, answers=st.session_state.answers, lang=lang)
        st.session_state.view = "waiting"
        st.rerun()

# -------------------
# شاشة الانتظار
# -------------------
elif st.session_state.view == "waiting":
    st.markdown("### ⏳ " + ("تحليل شخصيتك قيد المعالجة..." if is_arabic else "Analyzing your sport identity..."))
    st.info("🔬 " + ("نحن نغوص في أعماق شخصيتك الرياضية... قد يستغرق ذلك أقل من دقيقة." if is_arabic else "We're diving deep into your sport identity. Please wait..."))

    if st.button("🔄 تحديث النتيجة" if is_arabic else "🔄 Refresh Result"):
        result = check_result(user_id)
        if result:
            st.session_state.result = result
            st.session_state.view = "result"
            st.rerun()
        else:
            st.warning("🚧 " + ("لم تجهز التوصية بعد." if is_arabic else "Recommendation not ready yet."))

# -------------------
# عرض النتيجة
# -------------------
elif st.session_state.view == "result":
    result = st.session_state.result
    profile = result.get("profile", {})
    recs = result.get("recommendations", [])

    for i, rec in enumerate(recs):
        st.subheader(
            f"🟢 التوصية رقم {i+1}" if is_arabic else
            f"🟢 Recommendation #{i+1}" if i == 0 else
            f"🌿 التوصية رقم {i+1}" if i == 1 else
            f"🔮 التوصية رقم {i+1} (Creative)"
        )
        st.write(rec)

    st.markdown("---")
    st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")

    share_url = f"https://sportsync.ai/recommendation?user_id={user_id}&lang={lang}"
    st.markdown("📤 شارك توصيتك مع صديق!" if is_arabic else "📤 Share your recommendation with a friend!")
    st.code(share_url)

# -------------------
# زر إعادة الاختبار
# -------------------
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart the test"):
    st.session_state.clear()
    st.rerun()
