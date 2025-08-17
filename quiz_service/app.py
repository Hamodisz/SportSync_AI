# -- coding: utf-8 --
import os, sys, csv, json
from uuid import uuid4
from datetime import datetime
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

# أضف الجذر فقط لتفادي خطأ core كـ باكدج
root_str = str(ROOT.resolve())
if root_str not in sys.path:
    sys.path.insert(0, root_str)
# لو تبغى تحليل فقط، ممكن تضيف analysis اختيارياً
ana_str = str((ROOT / "analysis").resolve())
if ana_str not in sys.path:
    sys.path.insert(0, ana_str)

# ---------------------------
# استيرادات مرنة من مشروعك
# ---------------------------
try:
    from core.backend_gpt import generate_sport_recommendation
except Exception:
    def generate_sport_recommendation(answers, lang="العربية"):
        # Fallback مبسّط
        return [
            "🏃‍♂ الجري الخفيف 3 مرات أسبوعيًا / Light jogging 3x per week",
            "🏋 تمارين مقاومة منزلية 20 دقيقة / 20-min home resistance",
            "🧘 يوغا + تنفّس / Yoga + breathing"
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

# معرف الجلسة
if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid4().hex[:12]
SESSION_ID = st.session_state["session_id"]

# ملف سجل الجلسات
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = DATA_DIR / "quiz_sessions.csv"

def save_session_csv(*, session_id, lang, answers, recs, ratings=None, chat_history=None, z_signals=None):
    headers = [
        "ts_utc","session_id","lang",
        "answers_json","rec1","rec2","rec3",
        "ratings_json","z_signals_json","chat_history_json"
    ]
    row = [
        datetime.utcnow().isoformat(timespec="seconds")+"Z",
        session_id,
        lang,
        json.dumps(answers, ensure_ascii=False),
        recs[0] if len(recs)>0 else "",
        recs[1] if len(recs)>1 else "",
        recs[2] if len(recs)>2 else "",
        json.dumps(ratings or [], ensure_ascii=False),
        json.dumps(z_signals or [], ensure_ascii=False),
        json.dumps(chat_history or [], ensure_ascii=False),
    ]
    new_file = not LOG_PATH.exists()
    with LOG_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_file: w.writerow(headers)
        w.writerow(row)

# ---------------------------
# اختيار اللغة + تحميل الأسئلة
# ---------------------------
lang = st.sidebar.radio("🌐 اختر اللغة / Choose Language", ["العربية", "English"], index=0)
is_ar = (lang == "العربية")

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
# واجهة
# ---------------------------
st.title("🎯 توصيتك الرياضية الذكية" if is_ar else "🎯 Your Smart Sport Recommendation")
st.caption(f"Session: {SESSION_ID}")

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
            custom = st.text_input(("✏ إجابتك الخاصة (اختياري)" if is_ar else "✏ Your own answer (optional)"),
                                   key=f"{q_key}_custom")
            if custom:
                sel.append(custom)
        answers[q_key] = {"question": text, "answer": sel}
    else:
        t = st.text_input(text, key=q_key)
        answers[q_key] = {"question": text, "answer": t}

st.divider()

col1, col2 = st.columns([1,1])
go  = col1.button("🔍 اعرض التوصيات" if is_ar else "🔍 Show Recommendations")
rst = col2.button("🔄 إعادة الاختبار" if is_ar else "🔄 Restart")

if rst:
    st.session_state.clear()
    st.rerun()

# مساحة للمخرجات
if "recs" not in st.session_state:
    st.session_state["recs"] = []
if "z_signals" not in st.session_state:
    st.session_state["z_signals"] = []
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

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

    st.session_state["recs"] = recs[:3]
    st.session_state["z_signals"] = z

# عرض النتائج إن وجدت
recs = st.session_state.get("recs", [])
z = st.session_state.get("z_signals", [])

if z:
    st.subheader("🧭 ما يحركك دون أن تدري" if is_ar else "🧭 Your Silent Drivers")
    for item in z:
        st.write("• " + str(item))
    st.divider()

if recs:
    star_keys = []
    for i, rec in enumerate(recs):
        if is_ar:
            head = ["🟢 التوصية رقم 1", "🌿 التوصية رقم 2", "🔮 التوصية رقم 3 (ابتكارية)"][i] if i < 3 else f"🔹 توصية {i+1}"
        else:
            head = ["🟢 Recommendation #1","🌿 Recommendation #2","🔮 Recommendation #3 (Creative)"][i] if i < 3 else f"🔹 Recommendation {i+1}"
        st.subheader(head)
        st.write(rec)
        rk = f"rating_{i}"
        star_keys.append(rk)
        st.slider("⭐ " + ("قيّم التوصية" if is_ar else "Rate this"), 1, 5, 4, key=rk)

    c1, c2 = st.columns([1,1])

    if c1.button("💾 حفظ تقييمي" if is_ar else "💾 Save my ratings"):
        ratings = [int(st.session_state.get(k, 3)) for k in star_keys]
        try:
            save_session_csv(
                session_id=SESSION_ID, lang=lang,
                answers=answers, recs=recs, ratings=ratings,
                chat_history=st.session_state.get("chat_history", []),
                z_signals=z
            )
            st.success("تم حفظ الجلسة ✅" if is_ar else "Session saved ✅")
        except Exception as e:
            st.error(("تعذّر حفظ الجلسة: " if is_ar else "Failed to save session: ") + str(e))

    # زر "ما أعجبتني التوصية"
    if c2.button("😕 ما أعجبتني التوصية" if is_ar else "😕 I don’t like these"):
        st.session_state["show_chat"] = True

    st.divider()

    # محادثة ديناميكية
    if st.session_state.get("show_chat"):
        st.subheader("🧠 تحدث مع المدرب الذكي" if is_ar else "🧠 Talk to the AI Coach")

        # عرض تاريخ المحادثة
        for role, msg in st.session_state["chat_history"]:
            if role == "user":
                st.markdown(f"🧍‍♂:** {msg}")
            else:
                st.markdown(f"🤖:** {msg}")

        user_msg = st.text_input("💬 اكتب ردك أو سؤالك..." if is_ar else "💬 Type your response or question...", key="chat_input")
        if st.button("إرسال" if is_ar else "Send", key="send_btn"):
            if user_msg.strip():
                st.session_state["chat_history"].append(("user", user_msg))
                ratings = [int(st.session_state.get(f"rating_{i}", 3)) for i in range(len(recs))]
                try:
                    reply = start_dynamic_chat(
                        answers=answers,
                        previous_recommendation=recs,
                        ratings=ratings,
                        user_id=SESSION_ID,
                        lang=lang,
                        chat_history=[m for _, m in st.session_state["chat_history"]],
                        user_message=user_msg
                    )
                except Exception:
                    reply = "تم! سنعدّل الخطة تدريجيًا حسب ملاحظتك." if is_ar else "Got it! We'll adjust the plan gradually."
                st.session_state["chat_history"].append(("assistant", reply))
                st.rerun()

# ذيل الصفحة
st.caption("🚀 Powered by SportSync AI")
