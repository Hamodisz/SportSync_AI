# -- coding: utf-8 --
import os, csv, json
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import streamlit as st

# === واردات مشروعك (موجودة عندك) ===
from core.backend_gpt import generate_sport_recommendation
from core.dynamic_chat import start_dynamic_chat      # سنستخدمه بالخطوة 2
from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
from core.user_logger import log_user_insight

# -------------------
# إعداد الصفحة
# -------------------
st.set_page_config(page_title="SportSync — Quiz", layout="centered")

# مكان التخزين
DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / "quiz_sessions.csv"

def append_session_log(*, session_id, lang, answers, recommendations, ratings=None, extra=None):
    """يكتب سطرًا إلى CSV مع إنشاء الهيدر تلقائياً إذا لم يوجد."""
    headers = [
        "ts_utc","session_id","lang",
        "answers_json","rec1","rec2","rec3",
        "ratings_json","extra_json"
    ]
    row = [
        datetime.utcnow().isoformat(timespec="seconds")+"Z",
        session_id,
        lang,
        json.dumps(answers, ensure_ascii=False),
        recommendations[0] if len(recommendations) > 0 else "",
        recommendations[1] if len(recommendations) > 1 else "",
        recommendations[2] if len(recommendations) > 2 else "",
        json.dumps(ratings or [], ensure_ascii=False),
        json.dumps(extra or {}, ensure_ascii=False),
    ]
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file: w.writerow(headers)
        w.writerow(row)
    print(f"[INFO] session saved -> {session_id}", flush=True)

# جلسة المستخدم
if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid4().hex[:12]
SESSION_ID = st.session_state["session_id"]

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
st.caption(f"Session: {SESSION_ID}")

# -------------------
# جمع الإجابات
# -------------------
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
            custom_input = st.text_input(
                "✏ " + ("إجابتك الخاصة (اختياري)" if is_arabic else "Your own answer (optional)"),
                key=q_key+"_custom"
            )
            if custom_input:
                selected.append(custom_input)
        answers[q_key] = selected

    else:  # text
        answers[q_key] = st.text_input(q_text, key=q_key)

# -------------------
# زر التوصية
# -------------------
if st.button("🔍 اعرض التوصيات" if is_arabic else "🔍 Show Recommendations"):
    print("[INFO] generating recommendations...", flush=True)

    # ✅ توليد التوصيات
    recs = generate_sport_recommendation(answers, lang=lang)

    # ✅ تحليل Layer Z
    silent_drivers = analyze_silent_drivers(answers, lang=lang)

    # عرض ما يحركك
    if silent_drivers:
        st.markdown("---")
        st.subheader("🧭 ما يحركك دون أن تدري" if is_arabic else "🧭 Your Silent Drivers")
        for s in silent_drivers:
            st.write("• " + s)

    # ✅ عرض التوصيات الثلاثة + سلايدر تقييم
    ratings_keys = []
    for i, rec in enumerate(recs):
        if is_arabic:
            titles = ["🟢 التوصية 1", "🌿 التوصية 2", "🔮 التوصية 3 (ابتكارية)"]
        else:
            titles = ["🟢 Recommendation 1", "🌿 Recommendation 2", "🔮 Recommendation 3 (Creative)"]

        st.markdown("---")
        st.subheader(titles[i] if i < len(titles) else f"Recommendation #{i+1}")
        st.write(rec)
        rk = f"rating_{i}"
        ratings_keys.append(rk)
        st.slider("⭐ " + ("قيّم هذه التوصية" if is_arabic else "Rate this recommendation"), 1, 5, 3, key=rk)

    # ✅ زر حفظ الجلسة (يسجل CSV مع التقييمات)
    if st.button("💾 حفظ تقييمي" if is_arabic else "💾 Save my ratings"):
        user_ratings = [int(st.session_state.get(k, 3)) for k in ratings_keys]
        extra = {"silent_drivers": silent_drivers}
        append_session_log(
            session_id=SESSION_ID,
            lang=lang,
            answers=answers,
            recommendations=recs,
            ratings=user_ratings,
            extra=extra
        )
        st.success("تم حفظ الجلسة ✅" if is_arabic else "Session saved ✅")

    # ملاحظة: سنضيف في الخطوة (2) زر "ما أعجبتني التوصية" لبدء محادثة ديناميكية.
    st.info("📌 بعد الحفظ، سنضيف زر محادثة ذكية في الخطوة التالية.", icon="💡")

# -------------------
# إعادة الاختبار
# -------------------
if st.button("🔄 أعد الاختبار من البداية" if is_arabic else "🔄 Restart the test"):
    st.session_state.clear()
    st.rerun()
