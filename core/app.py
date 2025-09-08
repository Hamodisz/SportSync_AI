import streamlit as st
import json, os, uuid, urllib.parse
import qrcode
from io import BytesIO

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
# user_id من الرابط أو توليد جديد (يدعم user_id أو user)
# -------------------
qp = st.experimental_get_query_params()
user_id = qp.get("user_id", [None])[0] or qp.get("user", [None])[0]

if not user_id:
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:6]}"
    user_id = st.session_state.user_id
else:
    st.session_state.user_id = user_id

# قاعدة الرابط (للمشاركة)
APP_BASE = os.getenv("APP_BASE_URL", "https://sportsync.ai")
url_lang = urllib.parse.quote(lang)
share_url = f"{APP_BASE}/recommendation?user_id={user_id}&lang={url_lang}"

# -------------------
# الحالة الحالية
# -------------------
if "view" not in st.session_state:
    result = check_result(user_id)
    if result:
        st.session_state.result = result
        st.session_state.view = "result"
    elif os.path.exists(f"data/pending_requests/{user_id}.json"):
        st.session_state.view = "waiting"
    else:
        st.session_state.view = "quiz"

# -------------------
# عرض الأسئلة
# -------------------
if st.session_state.view == "quiz":
    # نجمع الإجابات بمفاتيح ثابتة (key) مع نص السؤال
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
                custom_input = st.text_input("✏ " + ("إجابتك الخاصة (اختياري)" if is_arabic else "Your own answer (optional)"),
                                             key=f"{q_key}_custom")
                if custom_input:
                    selected = list(selected) + [custom_input]
            answers[q_key] = {"question": q_text, "answer": selected}

        elif q_type == "text":
            txt = st.text_input(q_text, key=q_key)
            answers[q_key] = {"question": q_text, "answer": txt}

    if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
        submit_to_queue(user_id=user_id, answers=answers, lang=lang)
        st.session_state.view = "waiting"
        st.rerun()

# -------------------
# شاشة الانتظار
# -------------------
elif st.session_state.view == "waiting":
    st.markdown("### ⏳ " + ("تحليل شخصيتك قيد المعالجة..." if is_arabic else "Analyzing your sport identity..."))
    st.info("🔬 " + ("نغوص في شخصيتك الرياضية بعمق… قد يأخذ قليل وقت." if is_arabic else "Digging deep into your sport identity…"))

    # أعطِ المستخدم رابط الرجوع + QR (المغزى الأساسي)
    st.markdown("**🔗 " + ("رابط المتابعة:" if is_arabic else "Follow-up link:") + "**")
    st.code(share_url)
    st.text_input("انسخ الرابط:", share_url, key="share_link_wait")

    qr = qrcode.make(share_url)
    buf = BytesIO(); qr.save(buf)
    st.image(buf.getvalue(), caption=("📱 امسح الكود لفتح التوصية لاحقًا" if is_arabic else "📱 Scan to open later"), width=200)

    col1, col2 = st.columns(2)
    if col1.button("🔄 تحديث النتيجة" if is_arabic else "🔄 Refresh Result"):
        result = check_result(user_id)
        if result:
            st.session_state.result = result
            st.session_state.view = "result"
            st.rerun()
        else:
            st.warning("🚧 " + ("لم تجهز التوصية بعد." if is_arabic else "Recommendation not ready yet."))
    if col2.button("✏ عدّل إجاباتك" if is_arabic else "✏ Modify your answers"):
        # إلغاء الطلب المعلّق اختياريًا بترك الملف كما هو، أو امسحه لو تبغى
        st.session_state.view = "quiz"
        st.rerun()

# -------------------
# عرض التوصية النهائية
# -------------------
elif st.session_state.view == "result":
    result = st.session_state.result or {}
    profile = result.get("profile", {})
    recs = result.get("cards") or result.get("recommendations") or []

    if not recs:
        st.warning("لم تصلنا كروت التوصية بعد.")
    else:
        for rec in recs:
            # الكروت عندنا نصوص منسّقة — اعرضها كما هي
            if isinstance(rec, str):
                st.markdown(rec)
            else:
                # لو كانت Dict (صيغة JSON خام)، نعرِضها كما هي
                st.write(rec)
            st.markdown("---")

    st.caption("🚀 Powered by SportSync AI – Your identity deserves its own sport.")

    # مشاركة الرابط
    st.markdown("📤 " + ("شارك توصيتك مع صديق!" if is_arabic else "Share your recommendation!"))
    st.code(share_url)
    st.text_input("انسخ الرابط:", share_url, key="share_link_done")

    qr = qrcode.make(share_url)
    buf = BytesIO(); qr.save(buf)
    st.image(buf.getvalue(), caption=("📱 امسح QR Code لفتح التوصية" if is_arabic else "📱 Scan QR to open"), width=200)

    if st.button("✏ عدّل إجاباتك" if is_arabic else "✏ Modify your answers"):
        # امسح نتيجة المستخدم عشان يطلب تحليل جديد
        result_file = f"data/ready_results/{user_id}.json"
        if os.path.exists(result_file):
            os.remove(result_file)
        st.session_state.view = "quiz"
        st.rerun()

# -------------------
# زر إعادة الاختبار
# -------------------
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart the test"):
    st.session_state.clear()
    st.rerun()
