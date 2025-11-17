# api/index.py
"""
SportSync AI - FastAPI Backend for Vercel
Standalone version that works without complex imports
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json

# Create FastAPI app
app = FastAPI(
    title="SportSync AI API",
    description="AI-powered sport recommendation system",
    version="2.2"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class Answer(BaseModel):
    question_key: str
    answer_text: str

class RecommendationRequest(BaseModel):
    answers: List[Answer]
    language: str = "ar"
    user_id: Optional[str] = None

class RecommendationResponse(BaseModel):
    success: bool
    recommendations: List[str]
    analysis_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Health check endpoint
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "SportSync AI API",
        "version": "2.2",
        "message": "API is running successfully!",
        "endpoints": {
            "/": "Health check",
            "/api/recommend": "POST - Get sport recommendations",
            "/api/questions": "GET - Get questions list",
            "/api/sports": "GET - Get available sports",
            "/api/simple-recommend": "POST - Quick test endpoint"
        }
    }

@app.get("/api/health")
def health_check():
    """Detailed health check"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    return {
        "status": "healthy",
        "openai_configured": bool(api_key and len(api_key) > 10),
        "version": "2.2",
        "python_version": "3.12",
        "framework": "FastAPI"
    }

@app.post("/api/recommend", response_model=RecommendationResponse)
async def get_recommendations(request: RecommendationRequest):
    """
    Generate sport recommendations based on user answers

    For now, returns demo recommendations.
    Full AI integration coming soon!
    """
    try:
        # Check API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return RecommendationResponse(
                success=False,
                recommendations=[],
                error="OpenAI API key not configured. Add OPENAI_API_KEY to Vercel environment variables."
            )

        # For now, return intelligent demo recommendations based on answers
        recommendations = generate_demo_recommendations(request.answers, request.language)

        return RecommendationResponse(
            success=True,
            recommendations=recommendations,
            analysis_summary={
                "total_questions": len(request.answers),
                "language": request.language,
                "user_id": request.user_id,
                "note": "Demo recommendations - Full AI integration in progress"
            }
        )

    except Exception as e:
        return RecommendationResponse(
            success=False,
            recommendations=[],
            error=f"Error: {str(e)}"
        )

def generate_demo_recommendations(answers: List[Answer], lang: str) -> List[str]:
    """Generate intelligent demo recommendations based on answers"""

    # Analyze answers to provide relevant recommendations
    answers_text = " ".join([a.answer_text.lower() for a in answers])

    # Arabic recommendations
    if lang == "ar":
        # Check for keywords in answers
        if "هادئ" in answers_text or "تركيز" in answers_text or "استرخاء" in answers_text:
            return [
                """🧘 **اليوغا التأملية**

✨ **الجوهر:**
رياضة ذهنية-جسدية تجمع بين الحركة الواعية والتنفس العميق والتأمل.

💫 **التجربة:**
لحظات من السكون الداخلي، حيث يتوحد العقل والجسد في تناغم كامل. كل حركة هي تأمل متحرك.

🎯 **لماذا مثالية لك:**
- تناسب طبيعتك الهادئة المحبة للتركيز
- توفر مساحة للاسترخاء العميق
- تطور المرونة الجسدية والذهنية
- ممارسة فردية بدون ضغوط اجتماعية

🚀 **الأسبوع الأول:**
ابدأ بـ 10 دقائق يومياً من وضعيات بسيطة (Child's Pose, Cat-Cow). استخدم تطبيق أو فيديو عربي. ركز على التنفس أكثر من الإتقان.

✅ **علامات التقدم:**
- تشعر بهدوء ذهني بعد الممارسة
- تتحسن مرونتك تدريجياً
- تجد نفسك تتنفس بعمق أكثر في الحياة اليومية
""",

                """🎯 **الرماية بالقوس (Archery)**

✨ **الجوهر:**
رياضة تركيز ودقة تتطلب سكون داخلي وتحكم كامل في التنفس والحركة.

💫 **التجربة:**
لحظة إطلاق السهم = لحظة تأمل خالص. العالم يتوقف، يبقى أنت والهدف فقط.

🎯 **لماذا مثالية لك:**
- تتطلب تركيز عميق (ما تحبه)
- هادئة ولكن تحدي ذهني قوي
- فردية بدون ضغط جماعي
- تطور الصبر والانضباط الذاتي

🚀 **الأسبوع الأول:**
ابحث عن نادي رماية محلي وخذ درس تجريبي. تعلم الأساسيات: الوقفة، الشد، التصويب. لا تتسرع - الرماية فن يحتاج وقت.

✅ **علامات التقدم:**
- تصيب الهدف بشكل متكرر
- تشعر بالهدوء الذهني أثناء الرماية
- تتحسن قدرتك على التركيز لفترات طويلة
""",

                """🌲 **المشي التأملي في الطبيعة (Forest Bathing)**

✨ **الجوهر:**
رياضة يابانية (Shinrin-yoku) تجمع بين المشي البطيء والوعي الكامل بالطبيعة.

💫 **التجربة:**
ليس مجرد مشي - إنه انغماس كامل في الطبيعة بكل حواسك. كل خطوة واعية، كل نفس متصل بالأرض.

🎯 **لماذا مثالية لك:**
- هادئة تماماً ومريحة للأعصاب
- لا تحتاج مهارات أو معدات
- فردية وتعطيك مساحة شخصية
- مثبتة علمياً لتقليل التوتر وتحسين التركيز

🚀 **الأسبوع الأول:**
اختر حديقة أو غابة قريبة. امشِ 20-30 دقيقة ببطء شديد. ركز على: صوت الأوراق، رائحة الأشجار، ملمس الهواء. اترك الهاتف بالبيت.

✅ **علامات التقدم:**
- تشعر بهدوء عميق بعد المشي
- تنام أفضل
- تلاحظ تفاصيل الطبيعة لم تراها من قبل
"""
            ]

        elif "أدرينالين" in answers_text or "سريع" in answers_text or "حركة" in answers_text:
            return [
                """🏃 **Parkour - فن الحركة الحرة**

✨ **الجوهر:**
رياضة حضرية تحول المدينة إلى ملعب. تخطى، اقفز، تسلق - تحرك بحرية مطلقة!

💫 **التجربة:**
أدرينالين نقي! كل حاجز فرصة، كل حائط تحدي. تشعر بالحرية الكاملة.

🎯 **لماذا مثالية لك:**
- أدرينالين عالي (ما تحتاجه!)
- حركة سريعة ومتنوعة
- إبداع في الحركة - كل مسار فريد
- تطور قوة، سرعة، ومرونة

🚀 **الأسبوع الأول:**
ابدأ بالأساسيات في مكان آمن: تعلم القفز الصحيح، الدحرجة، التسلق البسيط. شاهد فيديوهات تعليمية، ابحث عن مجتمع محلي.

✅ **علامات التقدم:**
- تقفز بثقة أكبر
- تحس بقوة في جسمك
- تبدأ تشوف المدينة بعين مختلفة
""",

                """🚴 **Mountain Biking - ركوب الدراجات الجبلية**

✨ **الجوهر:**
سرعة + طبيعة + تحدي! انطلق في مسارات جبلية وعرة بأقصى سرعة ممكنة.

💫 **التجربة:**
رياح على وجهك، قلب ينبض بقوة، عضلات تشتغل، أدرينالين يملأك. حرية مطلقة!

🎯 **لماذا مثالية لك:**
- أدرينالين مستمر طول المسار
- سرعة ومغامرة
- يمكن ممارستها فردياً أو مع مجموعة
- تستكشف أماكن جديدة

🚀 **الأسبوع الأول:**
استأجر أو اشترِ دراجة جبلية. ابدأ بمسارات سهلة قريبة. تعلم التحكم، الفرملة، والتوازن على أرض غير مستوية.

✅ **علامات التقدم:**
- تنزل منحدرات بثقة
- تزيد مسافاتك تدريجياً
- تتحسن لياقتك بشكل ملحوظ
""",

                """🧗 **Rock Climbing - تسلق الصخور**

✨ **الجوهر:**
تحدي الجاذبية! كل حركة محسوبة، كل قبضة مهمة، كل متر للأعلى انتصار.

💫 **التجربة:**
عضلات تحترق، قلب يدق بقوة، ذهن يخطط للخطوة التالية. أدرينالين + تفكير استراتيجي.

🎯 **لماذا مثالية لك:**
- أدرينالين ممتع وآمن (مع الحبال)
- تحدي جسدي وذهني معاً
- شعور إنجاز قوي عند الوصول للقمة
- مجتمع داعم ومشجع

🚀 **الأسبوع الأول:**
زر صالة تسلق داخلية. خذ درس مبتدئين. تعلم استخدام الحبال والأمان. ابدأ بجدران سهلة.

✅ **علامات التقدم:**
- تتسلق جدران أصعب تدريجياً
- قوة قبضتك تزيد
- تخاف أقل، تثق بنفسك أكثر
"""
            ]

        else:
            # Default balanced recommendations
            return [
                """⚽ **كرة القدم الصغيرة (Futsal)**

✨ **الجوهر:**
كرة قدم سريعة في ملعب صغير - تركيز، مهارة، عمل جماعي.

💫 **التجربة:**
مزيج مثالي بين المتعة الجماعية والمهارات الفردية. كل لمسة كرة مهمة!

🎯 **لماذا مثالية لك:**
- توازن بين العمل الجماعي والفردي
- نشاط متوسط (لا هادئ جداً ولا عنيف جداً)
- ممتع ومسلي
- يبني صداقات قوية

🚀 **الأسبوع الأول:**
ابحث عن فريق محلي أو مجموعة أصدقاء. العب مباريات ودية. ركز على المتعة أكثر من الاحتراف.

✅ **علامات التقدم:**
- تتحسن لمساتك على الكرة
- تفهم اللعب الجماعي أكثر
- تستمتع وتنتظر المباراة القادمة
""",

                """🏊 **السباحة**

✨ **الجوهر:**
رياضة متكاملة تشغل كل عضلات الجسم في بيئة هادئة ومنعشة.

💫 **التجربة:**
انعدام وزن، حركة سلسة، تنفس منظم. تأمل متحرك في الماء.

🎯 **لماذا مثالية لك:**
- رياضة شاملة لكل الجسم
- يمكن ممارستها فردياً أو جماعياً
- هادئة للذهن، نشطة للجسم
- مناسبة لكل الأعمار واللياقات

🚀 **الأسبوع الأول:**
ابدأ بـ 20-30 دقيقة سباحة حرة. ركز على التنفس الصحيح. لا تتسرع - السباحة ماراثون مو سباق سرعة.

✅ **علامات التقدم:**
- تسبح مسافات أطول بدون تعب
- تنفسك يصير أقوى
- تشعر بنشاط بعد السباحة
""",

                """🎾 **التنس**

✨ **الجوهر:**
رياضة فردية أو زوجية تجمع بين الاستراتيجية، السرعة، والدقة.

💫 **التجربة:**
كل ضربة قرار، كل نقطة معركة صغيرة. ذهن يخطط، جسم ينفذ.

🎯 **لماذا مثالية لك:**
- تحدي ذهني وجسدي معاً
- يمكن لعبها فردي (1v1) أو زوجي
- اجتماعية ولكن ليست فوضوية
- لياقة ممتازة + مهارة + استراتيجية

🚀 **الأسبوع الأول:**
خذ 2-3 دروس خاصة لتعلم الأساسيات الصحيحة. تدرب على الضربات الأساسية. العب مباريات ودية.

✅ **علامات التقدم:**
- تضرب الكرة بدقة أكبر
- تبدأ تفكر استراتيجياً
- تستمتع بالتحدي
"""
            ]

    # English recommendations
    else:
        return [
            "🧘 **Yoga** - Perfect for calm, focused individuals seeking mind-body balance",
            "🏃 **Parkour** - For adrenaline seekers who love dynamic movement",
            "⚽ **Futsal** - Balanced team sport with individual skill development"
        ]

@app.get("/api/questions")
async def get_questions(lang: str = "ar"):
    """Get the list of questions for the specified language"""

    # Simple demo questions
    if lang == "ar":
        return {
            "success": True,
            "questions": [
                {
                    "key": "q1",
                    "question_ar": "في أي لحظات تحس الوقت يطير وأنت تمارس نشاط؟",
                    "question_en": "When do you feel time flies during an activity?",
                    "options": [
                        {"text_ar": "تركيز هادئ على تفصيلة واحدة", "text_en": "Calm focus on a single detail"},
                        {"text_ar": "أدرينالين وحركة سريعة", "text_en": "Adrenaline and fast movement"},
                        {"text_ar": "عمل جماعي متناغم", "text_en": "Harmonious teamwork"}
                    ]
                },
                {
                    "key": "q2",
                    "question_ar": "ما الذي يحفزك أكثر؟",
                    "question_en": "What motivates you most?",
                    "options": [
                        {"text_ar": "تطوير مهارة بعمق", "text_en": "Developing a skill deeply"},
                        {"text_ar": "التحدي والمنافسة", "text_en": "Challenge and competition"},
                        {"text_ar": "الاستكشاف والتجارب الجديدة", "text_en": "Exploration and new experiences"}
                    ]
                },
                {
                    "key": "q3",
                    "question_ar": "كيف تفضل التعلم؟",
                    "question_en": "How do you prefer to learn?",
                    "options": [
                        {"text_ar": "بمفردي وبتأني", "text_en": "Alone and at my own pace"},
                        {"text_ar": "مع مدرب شخصي", "text_en": "With a personal coach"},
                        {"text_ar": "في مجموعة", "text_en": "In a group"}
                    ]
                }
            ]
        }
    else:
        return {
            "success": True,
            "questions": [
                {
                    "key": "q1",
                    "question_en": "When do you feel time flies during an activity?",
                    "options": [
                        {"text_en": "Calm focus on a single detail"},
                        {"text_en": "Adrenaline and fast movement"},
                        {"text_en": "Harmonious teamwork"}
                    ]
                }
            ]
        }

@app.get("/api/sports")
async def get_sports():
    """Get demo list of available sports"""
    return {
        "success": True,
        "total_sports": 10,
        "sports": [
            {"id": "yoga", "label": "Yoga", "risk_level": "low"},
            {"id": "parkour", "label": "Parkour", "risk_level": "medium"},
            {"id": "futsal", "label": "Futsal", "risk_level": "low"},
            {"id": "swimming", "label": "Swimming", "risk_level": "low"},
            {"id": "tennis", "label": "Tennis", "risk_level": "low"},
            {"id": "archery", "label": "Archery", "risk_level": "low"},
            {"id": "mtb", "label": "Mountain Biking", "risk_level": "medium"},
            {"id": "climbing", "label": "Rock Climbing", "risk_level": "medium"},
            {"id": "forest_bathing", "label": "Forest Bathing", "risk_level": "low"},
            {"id": "tai_chi", "label": "Tai Chi", "risk_level": "low"}
        ]
    }

@app.post("/api/simple-recommend")
async def simple_recommend(request: dict):
    """Simplified recommendation endpoint for quick testing"""
    try:
        answers = request.get("answers", [])
        language = request.get("language", "ar")

        # Convert dict answers to Answer objects
        answer_objects = [Answer(question_key=a.get("question_key", "q1"),
                                 answer_text=a.get("answer_text", ""))
                         for a in answers]

        recommendations = generate_demo_recommendations(answer_objects, language)

        return {
            "success": True,
            "message": "API is working!",
            "received": len(answers),
            "recommendations": recommendations
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# This is required for Vercel
# The 'app' variable must be named 'app' for Vercel to find it
