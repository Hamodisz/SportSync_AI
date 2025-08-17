# -- coding: utf-8 --
import os, sys, json
from pathlib import Path
import streamlit as st

# ---------------------------
# مسارات مرنة (تشتغل محليًا وعلى Render)
# ---------------------------
try:
    HERE = Path(_file_).resolve().parent
except NameError:
    HERE = Path.cwd()

ROOT = HERE.parent if HERE.name == "quiz_service" else HERE
for p in (ROOT, ROOT / "core", ROOT / "analysis"):
    sp = str(p.resolve())
    if sp not in sys.path:
        sys.path.insert(0, sp)

# ---------------------------
# استيرادات مرنة من مشروعك
# ---------------------------
try:
    from core.backend_gpt import generate_sport_recommendation
except Exception:
    def generate_sport_recommendation(answers, lang="العربية"):
        #Fallback مبسّط لو ما توفر الموديول
        return [
            "🏃‍♂ الجري الخفيف 3 مرات أسبوعيًا / Light jogging 3x per week",
            "🏋 تمارين مقاومة منزلية 20 دقيقة / 20-min home resistance",
            "🧘 يوجا وتركيز ذهني / Yoga + mindfulness"
        ]

try:
    from core.dynamic_chat import start_dynamic_chat
except Exception:
    def start_dynamic_chat(**kwargs):
        return "فهمت رغبتك. نقدر نخفف الشدة ونزيد التدرّج أسبوعيًا. هل يناسبك؟"

try:
    from analysis.layer_z_engine import analyze_silent_drivers_combined as analyze_silent_drivers
except Exception:
    def analyze_silent_drivers(answers, lang="العربية"):
        return ["تحفيز قصير المدى", "إنجازات سريعة", "تفضيل تدريبات فردية"]

# ---------------------------
# إعداد الصفحة
# ---------------------------
st.set_page_config(page_title="SportSync — Quiz", page_icon="🎯", layout="centered")

# ---------------------------
# اختيار اللغة
# ---------------------------
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"], index=0)
is_ar = (lang == "العربية")

# ---------------------------
# تحميل الأسئلة
# ---------------------------
QUESTIONS_DIR = (ROOT / "questions")
if not QUESTIONS_DIR.exists():
    QUESTIONS_DIR = HERE / "questions"

q_file = QUESTIONS_DIR / ("arabic_questions.json" if is_ar else "english_questions.json")
if not q_file.exists():
    st.error("❌ لم يتم العثور على ملف الأسئلة.")
    st.stop()

with q_file.open("r", encoding="utf-8") as f:
    questions = json.load(f)

# ---------------------------
# عنوان
# ---------------------------
st.title("🎯 توصيتك الرياضية الذكية" if is_ar else "🎯 Your Smart Sport Recommendation")

# ---------------------------
# تجميع الإجابات
# ---------------------------
answers = {}
for q in questions:
    q_key = q.get("key", f"q_{len(answers)+1}")
    text = q["question_ar"] if is_ar else q["question_en"]
    q_type = q.get("type", "text")
    options = q.get("options", [])
    allow_custom = q.get("allow_custom", False)

    if q_type == "multiselect":
        sel = st.multiselect(text, options, key=q_key)
        if allow_custom:
            custom = st.text_input(("✏ إجابتك الخاصة (اختياري)" if is_ar else "✏ Your own answer (optional)"), key=f"{q_key}_custom")
            if custom:
                sel.append(custom)
        answers[q_key] = {"question": text, "answer": sel}

    else:  # text
        t = st.text_input(text, key=q_key)
        answers[q_key] = {"question": text, "answer": t}

st.divider()

col1, col2 = st.columns([1,1])
go = col1.button("🔍 اعرض التوصيات" if is_ar else "🔍 Show Recommendations")
rst = col2.button("🔄 إعادة الاختبار" if is_ar else "🔄 Restart")

if rst:
    st.session_state.clear()
    st.rerun()

if go:
    user_id = "web_user"

    # توصيات
    try:
        recs = generate_sport_recommendation(answers, lang=lang)
    except Exception as e:
        st.error(("خطأ أثناء توليد التوصيات: " if is_ar else "Error generating recommendations: ") + str(e))
        recs = []

    # Layer Z
    try:
        z = analyze_silent_drivers(answers, lang=lang)
    except Exception:
        z = []

    if z:
        st.subheader("🧭 ما يحركك دون أن تدري" if is_ar else "🧭 Your Silent Drivers")
        for item in z:
            st.write("• " + str(item))
        st.divider()

    if not recs:
        st.warning("لا توجد توصيات حالياً." if is_ar else "No recommendations available right now.")
    else:
        for i, rec in enumerate(recs[:3]):
            if is_ar:
                head = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"][i] if i < 3 else f"🔹 توصية {i+1}"
            else:
                head = ["🟢 Recommendation #1","🌿 Recommendation #2","🔮 Recommendation #3 (Creative)"][i] if i < 3 else f"🔹 Recommendation {i+1}"
            st.subheader(head)
            st.write(rec)
            st.slider("⭐ " + ("قيّم التوصية" if is_ar else "Rate this"), 1, 5, 4, key=f"rating_{i}")

        st.divider()
        st.subheader("🧠 تحدث مع المدرب الذكي" if is_ar else "🧠 Talk to the AI Coach")
        prompt = st.text_input("💬 اكتب ردك أو سؤالك..." if is_ar else "💬 Type your response or question...")
        if prompt:
            ratings = [st.session_state.get(f"rating_{i}", 3) for i in range(3)]
            try:
                reply = start_dynamic_chat(
                    answers=answers,
                    previous_recommendation=recs[:3],
                    ratings=ratings,
                    user_id=user_id,
                    lang=lang,
                    chat_history=[],
                    user_message=prompt
                )
            except Exception:
                reply = "تم! سنعدّل الخطة تدريجيًا حسب ملاحظتك." if is_ar else "Got it! We'll adjust the plan gradually."

            st.markdown("🤖 AI Coach:")
            st.success(reply)

    st.caption("🚀 Powered by SportSync AI")
