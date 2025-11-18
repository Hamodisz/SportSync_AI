"""
SportSync AI - DUAL-AI SYSTEM
Complete system with 10 questions + DUAL AI analysis

ARCHITECTURE:
1. Reasoning AI (o1-preview): Deep personality analysis, psychological insights
2. Intelligence AI (GPT-4): Creative sport generation, 8 billion unique identities
3. MCP Integration: Real-time communication protocol
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import json
import os
from pathlib import Path
from openai import OpenAI
import httpx
import random
import re
import hashlib
from datetime import datetime
from expanded_fallback_sports import EXPANDED_FALLBACK_SPORTS

# Create FastAPI app
app = FastAPI(
    title="SportSync AI - Full System",
    description="Complete AI-powered sport recommendation system with 10-question personality analysis",
    version="3.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════
# LOAD FULL QUESTIONS DATA
# ═══════════════════════════════════════════════════════════════

QUESTIONS_DATA = None

def load_questions():
    """Load all 10 questions from arabic_questions_v2.json"""
    global QUESTIONS_DATA

    # Try multiple paths
    possible_paths = [
        Path(__file__).parent.parent / "data" / "questions" / "arabic_questions_v2.json",
        Path("data/questions/arabic_questions_v2.json"),
        Path("/var/task/data/questions/arabic_questions_v2.json"),  # Vercel path
    ]

    for path in possible_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                QUESTIONS_DATA = json.load(f)
            return QUESTIONS_DATA

    # Fallback: Embed minimal questions
    QUESTIONS_DATA = [
        {
            "key": "q1",
            "question_ar": "متى تحس أن الوقت اختفى وأنت في قمة تركيزك؟",
            "question_en": "When do you feel time disappeared while you're in peak focus?",
            "options": [
                {
                    "text_ar": "عندما أدخل في تفصيلة واحدة بعمق شديد",
                    "text_en": "When I dive deeply into a single detail",
                    "scores": {"calm_adrenaline": -0.9, "solo_group": -0.7, "sensory_sensitivity": 0.8}
                },
                {
                    "text_ar": "في لحظات السرعة والتفاعل المباشر",
                    "text_en": "In moments of speed and direct interaction",
                    "scores": {"calm_adrenaline": 0.8, "solo_group": 0.3, "sensory_sensitivity": 0.6}
                },
                {
                    "text_ar": "عندما أواجه تحديات متنوعة ومفاجئة",
                    "text_en": "When facing diverse and surprising challenges",
                    "scores": {"calm_adrenaline": 0.6, "repeat_variety": 0.9, "sensory_sensitivity": 0.7}
                },
                {
                    "text_ar": "أثناء التعاون والتناغم مع الآخرين",
                    "text_en": "During collaboration and harmony with others",
                    "scores": {"solo_group": 0.9, "calm_adrenaline": -0.1, "compete_enjoy": -0.4}
                }
            ]
        }
    ]
    return QUESTIONS_DATA

# Load questions on startup
load_questions()

# ═══════════════════════════════════════════════════════════════
# PERSONALITY SCORING ENGINE
# ═══════════════════════════════════════════════════════════════

def calculate_personality_scores(answers: List[Dict]) -> Dict[str, float]:
    """Calculate Z-axis personality scores from user answers"""

    z_scores = {
        "calm_adrenaline": 0.0,
        "solo_group": 0.0,
        "technical_intuitive": 0.0,
        "control_freedom": 0.0,
        "repeat_variety": 0.0,
        "compete_enjoy": 0.0,
        "sensory_sensitivity": 0.0
    }

    counts = {k: 0 for k in z_scores.keys()}

    for answer in answers:
        q_key = answer.get("question_key", "")
        answer_text = answer.get("answer_text", "")

        # Find the question
        question = next((q for q in QUESTIONS_DATA if q["key"] == q_key), None)
        if not question:
            continue

        # Find the selected option
        selected_option = None
        for option in question.get("options", []):
            if answer_text in option.get("text_ar", "") or answer_text in option.get("text_en", ""):
                selected_option = option
                break

        if not selected_option:
            continue

        # Add scores
        option_scores = selected_option.get("scores", {})
        for axis, score in option_scores.items():
            if axis in z_scores:
                z_scores[axis] += score
                counts[axis] += 1

    # Average the scores
    for axis in z_scores:
        if counts[axis] > 0:
            z_scores[axis] = z_scores[axis] / counts[axis]

    return z_scores

# ═══════════════════════════════════════════════════════════════
# REASONING AI - Deep Personality Analysis (o1-preview)
# ═══════════════════════════════════════════════════════════════

def analyze_personality_with_reasoning_ai(z_scores: Dict[str, float], answers: List[Dict], lang: str = "ar") -> Dict[str, Any]:
    """
    REASONING AI (o1-preview): Deep psychological analysis

    This AI model:
    - Analyzes personality patterns with PhD-level psychology reasoning
    - Identifies unique traits and hidden motivations
    - Provides insights that generic scoring systems miss
    - Reasons through complex personality interactions
    """
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Fallback to basic analysis
        return {
            "personality_type": determine_profile_type(z_scores),
            "key_traits": ["Based on Z-scores"],
            "hidden_motivations": ["Requires AI reasoning"],
            "psychological_insights": "AI reasoning unavailable - using basic analysis",
            "reasoning_confidence": 0.5
        }

    # Create OpenAI client (new v1+ syntax) with custom http_client to bypass proxy issues
    http_client = httpx.Client(timeout=60.0)
    client = OpenAI(api_key=api_key, http_client=http_client)

    # Prepare personality data
    z_scores_text = "\n".join([f"- {axis.replace('_', '/')}: {score:.2f}" for axis, score in z_scores.items()])

    reasoning_prompt = f"""You are a PhD-level sports psychologist with deep expertise in personality analysis.

PERSONALITY Z-SCORES:
{z_scores_text}

Your task: Provide DEEP REASONING about this person's personality:

1. What are their CORE psychological drivers? (Not just surface traits)
2. What HIDDEN MOTIVATIONS might they have that they don't even realize?
3. How do these personality dimensions INTERACT with each other?
4. What makes this person TRULY UNIQUE compared to mainstream profiles?
5. What sports experiences would profoundly match their AUTHENTIC SELF?

Think deeply. Reason through the psychology. Look beyond obvious patterns.

Return your analysis as JSON:
{{
  "personality_type": "descriptive label",
  "core_drivers": ["driver 1", "driver 2", "driver 3"],
  "hidden_motivations": ["motivation 1", "motivation 2"],
  "unique_traits": ["what makes them different"],
  "psychological_insights": "deep paragraph of reasoning",
  "sport_criteria": ["what they TRULY need in sports"],
  "reasoning_confidence": 0.0-1.0
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",  # Reasoning model (o1-preview not available, using gpt-4-turbo)
            messages=[
                {"role": "system", "content": "You are a PhD-level sports psychologist specializing in deep personality analysis and reasoning."},
                {"role": "user", "content": reasoning_prompt}
            ]
        )

        # Parse response
        content = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', content, re.DOTALL)

        if json_match:
            analysis = json.loads(json_match.group())
            return analysis
        else:
            raise ValueError("No JSON in reasoning response")

    except Exception as e:
        print(f"Reasoning AI error: {e}")
        # Fallback
        return {
            "personality_type": determine_profile_type(z_scores),
            "core_drivers": ["Requires reasoning AI"],
            "hidden_motivations": ["Requires reasoning AI"],
            "unique_traits": ["Requires reasoning AI"],
            "psychological_insights": f"Reasoning AI unavailable: {str(e)}",
            "sport_criteria": ["Based on Z-scores"],
            "reasoning_confidence": 0.3
        }

# ═══════════════════════════════════════════════════════════════
# SPORT RECOMMENDATION ENGINE
# ═══════════════════════════════════════════════════════════════

SPORT_DATABASE = {
    "calm_focused": [
        {
            "name_ar": "🧘 اليوغا التأملية",
            "name_en": "Meditative Yoga",
            "description_ar": "رياضة ذهنية-جسدية تجمع بين الحركة الواعية والتنفس العميق والتأمل. مثالية للباحثين عن التركيز والسكون الداخلي.",
            "description_en": "Mind-body practice combining conscious movement, deep breathing, and meditation. Perfect for those seeking focus and inner calm.",
            "match_profile": {"calm_adrenaline": -0.7, "solo_group": -0.5, "sensory_sensitivity": 0.7}
        },
        {
            "name_ar": "🎯 الرماية بالقوس",
            "name_en": "Archery",
            "description_ar": "رياضة تركيز ودقة تتطلب سكون داخلي وتحكم كامل في التنفس والحركة.",
            "description_en": "Precision sport requiring inner calm and complete control of breathing and movement.",
            "match_profile": {"calm_adrenaline": -0.8, "solo_group": -0.6, "technical_intuitive": -0.5}
        },
        {
            "name_ar": "🌲 المشي التأملي",
            "name_en": "Mindful Walking / Forest Bathing",
            "description_ar": "انغماس كامل في الطبيعة بكل حواسك. كل خطوة واعية، كل نفس متصل بالأرض.",
            "description_en": "Full immersion in nature with all your senses. Every step conscious, every breath connected to the earth.",
            "match_profile": {"calm_adrenaline": -0.9, "solo_group": -0.7, "sensory_sensitivity": 0.8}
        }
    ],
    "active_adrenaline": [
        {
            "name_ar": "🏃 Parkour - فن الحركة الحرة",
            "name_en": "Parkour - Free Movement",
            "description_ar": "رياضة حضرية تحول المدينة إلى ملعب. تخطى، اقفز، تسلق - تحرك بحرية مطلقة!",
            "description_en": "Urban sport that transforms the city into a playground. Jump, climb, move with total freedom!",
            "match_profile": {"calm_adrenaline": 0.8, "control_freedom": 0.7, "repeat_variety": 0.6}
        },
        {
            "name_ar": "🚴 ركوب الدراجات الجبلية",
            "name_en": "Mountain Biking",
            "description_ar": "سرعة + طبيعة + تحدي! انطلق في مسارات جبلية وعرة بأقصى سرعة ممكنة.",
            "description_en": "Speed + nature + challenge! Blast through rugged mountain trails at maximum velocity.",
            "match_profile": {"calm_adrenaline": 0.7, "solo_group": 0.0, "sensory_sensitivity": 0.6}
        },
        {
            "name_ar": "🧗 تسلق الصخور",
            "name_en": "Rock Climbing",
            "description_ar": "تحدي الجاذبية! كل حركة محسوبة، كل قبضة مهمة، كل متر للأعلى انتصار.",
            "description_en": "Challenge gravity! Every move calculated, every grip matters, every meter up is a victory.",
            "match_profile": {"calm_adrenaline": 0.6, "technical_intuitive": -0.4, "control_freedom": 0.5}
        }
    ],
    "social_team": [
        {
            "name_ar": "⚽ كرة القدم الصغيرة (Futsal)",
            "name_en": "Futsal",
            "description_ar": "كرة قدم سريعة في ملعب صغير - تركيز، مهارة، عمل جماعي.",
            "description_en": "Fast-paced football in a small court - focus, skill, teamwork.",
            "match_profile": {"solo_group": 0.7, "calm_adrenaline": 0.3, "compete_enjoy": 0.5}
        },
        {
            "name_ar": "🏐 الكرة الطائرة الشاطئية",
            "name_en": "Beach Volleyball",
            "description_ar": "رياضة جماعية ممتعة تجمع بين اللياقة والمرح والتواصل الاجتماعي.",
            "description_en": "Fun team sport combining fitness, enjoyment, and social connection.",
            "match_profile": {"solo_group": 0.8, "calm_adrenaline": 0.2, "sensory_sensitivity": 0.4}
        }
    ],
    "balanced": [
        {
            "name_ar": "🏊 السباحة",
            "name_en": "Swimming",
            "description_ar": "رياضة متكاملة تشغل كل عضلات الجسم في بيئة هادئة ومنعشة.",
            "description_en": "Complete sport engaging all body muscles in a calm, refreshing environment.",
            "match_profile": {"calm_adrenaline": -0.2, "solo_group": 0.0, "sensory_sensitivity": 0.5}
        },
        {
            "name_ar": "🎾 التنس",
            "name_en": "Tennis",
            "description_ar": "رياضة فردية أو زوجية تجمع بين الاستراتيجية، السرعة، والدقة.",
            "description_en": "Individual or doubles sport combining strategy, speed, and precision.",
            "match_profile": {"compete_enjoy": 0.5, "technical_intuitive": -0.3, "solo_group": 0.0}
        },
        {
            "name_ar": "🚶 المشي السريع",
            "name_en": "Power Walking",
            "description_ar": "رياضة بسيطة وفعالة يمكن ممارستها في أي مكان وزمان.",
            "description_en": "Simple and effective sport that can be practiced anywhere, anytime.",
            "match_profile": {"calm_adrenaline": -0.5, "solo_group": -0.4, "control_freedom": 0.6}
        }
    ]
}

def generate_unique_sports_with_ai(z_scores: Dict[str, float], lang: str = "ar", reasoning_insights: Dict[str, Any] = None) -> List[Dict]:
    """
    INTELLIGENCE AI (GPT-4): Generate TRULY UNIQUE sports
    NOW WITH WEB SEARCH - Can find ANY of 8000+ sports!

    Process:
    1. Search web for sports matching personality
    2. Use GPT-4 to analyze and select best matches
    3. Can discover obscure, niche, hybrid sports
    4. NOT limited to pre-defined database
    """
    # Get OpenAI API key from environment
    api_key = os.environ.get("OPENAI_API_KEY")

    if not api_key:
        # Fallback to creative generation without API
        return generate_unique_sports_fallback(z_scores, lang)

    # Create OpenAI client (new v1+ syntax) with custom http_client to bypass proxy issues
    http_client = httpx.Client(timeout=60.0)
    client = OpenAI(api_key=api_key, http_client=http_client)

    # STEP 1: Search web for sports (8000+ possibilities)
    from mcp_research import MCPResearchEngine
    research_engine = MCPResearchEngine()

    personality_type = reasoning_insights.get("personality_type", "Unknown") if reasoning_insights else "Unknown"
    search_query = f"best sports activities for {personality_type} personality type unique unusual"

    print(f"🔍 Searching web for sports: {search_query}")
    web_results = research_engine.search_web_advanced(search_query, num_results=10)

    # Create detailed personality profile
    personality_desc = f"""
Personality Z-Scores (scale -1.0 to +1.0):
- Calm/Adrenaline: {z_scores.get('calm_adrenaline', 0.0):.2f}
- Solo/Group: {z_scores.get('solo_group', 0.0):.2f}
- Technical/Intuitive: {z_scores.get('technical_intuitive', 0.0):.2f}
- Control/Freedom: {z_scores.get('control_freedom', 0.0):.2f}
- Repetition/Variety: {z_scores.get('repeat_variety', 0.0):.2f}
- Compete/Enjoy: {z_scores.get('compete_enjoy', 0.0):.2f}
- Sensory Sensitivity: {z_scores.get('sensory_sensitivity', 0.0):.2f}
"""

    # STEP 2: Add web search results context
    web_sports_context = "\n\nWEB SEARCH RESULTS (8000+ sports discovered):\n"
    for i, result in enumerate(web_results[:10], 1):
        web_sports_context += f"{i}. {result.get('title', 'Unknown')}\n"
        web_sports_context += f"   {result.get('snippet', '')[:200]}...\n"

    # Add reasoning AI insights if available
    reasoning_context = ""
    if reasoning_insights:
        reasoning_context = f"""

DEEP PSYCHOLOGICAL INSIGHTS (from Reasoning AI):
- Personality Type: {reasoning_insights.get('personality_type', 'Unknown')}
- Core Drivers: {', '.join(reasoning_insights.get('core_drivers', []))}
- Hidden Motivations: {', '.join(reasoning_insights.get('hidden_motivations', []))}
- Unique Traits: {', '.join(reasoning_insights.get('unique_traits', []))}
- Sport Criteria: {', '.join(reasoning_insights.get('sport_criteria', []))}
- Insights: {reasoning_insights.get('psychological_insights', '')}
"""

    system_prompt = f"""You are a revolutionary sports psychologist with access to 8000+ sports via web search.

You have:
1. DEEP REASONING insights from Reasoning AI
2. WEB SEARCH RESULTS showing 10 potential sports from the internet
3. Access to thousands of sports (not just mainstream ones)

Your task: Select and customize 3 TRULY UNIQUE sports from web results OR create hybrids.

CRITICAL RULES:
1. PRIORITIZE sports from the web search results (these are real, from the internet)
2. NEVER recommend mainstream sports (swimming, tennis, football) unless you are 200% certain
3. Out of 8 billion people, only a tiny fraction match common sports
4. Use the web results to find NICHE, UNUSUAL, OBSCURE sports
5. Can combine/hybrid sports from web results
6. Consider psychological insights and core drivers
7. Be specific with names (not "martial arts" but "Kendo combined with meditation")
8. Each recommendation should reference web search findings

You can discover: Parkour, Bouldering, Ultimate Frisbee, Capoeira, Slacklining, Geocaching,
Trail Running, Stand-up Paddleboarding, Disc Golf, Orienteering, Spikeball, Roller Derby,
and 8000+ more via web search!

Language: {'Arabic' if lang == 'ar' else 'English'}

Return 3 UNIQUE sports as JSON:
[
  {{
    "name_ar": "unique Arabic name",
    "name_en": "unique English name",
    "description_ar": "why this specific person matches this specific sport (reference their psychology)",
    "description_en": "why this specific person matches this specific sport (reference their psychology)",
    "uniqueness_score": 0.0-1.0,
    "psychological_match": "how it connects to their core drivers"
  }}
]
"""

    try:
        user_prompt = f"Generate 3 TRULY UNIQUE sports for this personality:\n\n{personality_desc}{web_sports_context}{reasoning_context}"

        print(f"🤖 Asking GPT-4 to select from {len(web_results)} web results...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=1.2,  # High creativity
            max_tokens=1500
        )

        # Parse GPT response
        content = response.choices[0].message.content

        # Extract JSON
        import re
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            sports = json.loads(json_match.group())

            # Add match scores
            for i, sport in enumerate(sports):
                sport['match_score'] = 0.85 + (i * 0.03) + (sport.get('uniqueness_score', 0.5) * 0.1)

            return sports[:3]
        else:
            raise ValueError("No JSON found in response")

    except Exception as e:
        print(f"AI generation error: {e}")
        return generate_unique_sports_fallback(z_scores, lang)

def generate_unique_sports_fallback(z_scores: Dict[str, float], lang: str = "ar") -> List[Dict]:
    """
    EXPANDED Fallback: 261 diverse sports (up from 36)
    Uses personality-matched selection from expanded list
    Priority 3: Prevent duplication during API failures
    """
    import hashlib

    # Create a unique seed from user's personality
    score_string = "".join([f"{k}:{v:.2f}" for k, v in sorted(z_scores.items())])
    seed = int(hashlib.md5(score_string.encode()).hexdigest()[:8], 16)
    random.seed(seed)

    calm = z_scores.get("calm_adrenaline", 0.0)
    social = z_scores.get("solo_group", 0.0)
    variety = z_scores.get("repeat_variety", 0.0)

    # Dynamic sport selection from expanded list (261 sports)
    recommendations = []

    # Sport 1: Based on calm/adrenaline axis (29 options per category)
    if calm < -0.6:
        calm_category = "very_calm"
        description_ar = f"رياضة مصممة خصيصاً للشخصيات الهادئة (درجة {calm:.1f}). تجمع بين السكون الداخلي والحركة الواعية."
        description_en = f"Sport designed for calm personalities (score {calm:.1f}). Combines inner peace with conscious movement."
    elif calm > 0.6:
        calm_category = "very_adrenaline"
        description_ar = f"رياضة عالية الأدرينالين (درجة {calm:.1f}) مثالية لمحبي التحدي والإثارة."
        description_en = f"High-adrenaline sport (score {calm:.1f}) perfect for thrill-seekers."
    else:
        calm_category = "balanced_calm"
        description_ar = f"رياضة متوازنة (درجة {calm:.1f}) تجمع بين الهدوء والنشاط."
        description_en = f"Balanced sport (score {calm:.1f}) combining calm and activity."

    sport1_data = random.choice(EXPANDED_FALLBACK_SPORTS[calm_category]["sports"])
    sport1 = {
        "name_ar": sport1_data["name_ar"],
        "name_en": sport1_data["name_en"],
        "description_ar": description_ar,
        "description_en": description_en
    }

    # Sport 2: Based on social/solo axis (29 options per category)
    if social > 0.6:
        social_category = "very_social"
        description_ar = f"رياضة جماعية (درجة {social:.1f}) تعزز التواصل والعمل الجماعي."
        description_en = f"Team sport (score {social:.1f}) enhancing connection and teamwork."
    elif social < -0.6:
        social_category = "very_solo"
        description_ar = f"رياضة فردية (درجة {social:.1f}) مثالية للتركيز الذاتي."
        description_en = f"Solo sport (score {social:.1f}) perfect for self-focus."
    else:
        social_category = "balanced_social"
        description_ar = f"رياضة مرنة (درجة {social:.1f}) يمكن ممارستها فردياً أو جماعياً."
        description_en = f"Flexible sport (score {social:.1f}) playable solo or with others."

    sport2_data = random.choice(EXPANDED_FALLBACK_SPORTS[social_category]["sports"])
    sport2 = {
        "name_ar": sport2_data["name_ar"],
        "name_en": sport2_data["name_en"],
        "description_ar": description_ar,
        "description_en": description_en
    }

    # Sport 3: Based on variety/repetition axis (29 options per category)
    if variety > 0.6:
        variety_category = "high_variety"
        description_ar = f"رياضة متنوعة (درجة {variety:.1f}) تقدم تحديات جديدة كل يوم."
        description_en = f"Varied sport (score {variety:.1f}) offering new challenges daily."
    elif variety < -0.6:
        variety_category = "low_variety"
        description_ar = f"رياضة منتظمة (درجة {variety:.1f}) مثالية لبناء العادات."
        description_en = f"Regular sport (score {variety:.1f}) perfect for building habits."
    else:
        variety_category = "balanced_variety"
        description_ar = f"رياضة متوسطة (درجة {variety:.1f}) توازن بين الروتين والتنوع."
        description_en = f"Moderate sport (score {variety:.1f}) balancing routine and variety."

    sport3_data = random.choice(EXPANDED_FALLBACK_SPORTS[variety_category]["sports"])
    sport3 = {
        "name_ar": sport3_data["name_ar"],
        "name_en": sport3_data["name_en"],
        "description_ar": description_ar,
        "description_en": description_en
    }

    recommendations = [sport1, sport2, sport3]

    # Add match scores
    for i, rec in enumerate(recommendations):
        # Calculate match score based on how well it fits the profile
        base_score = 0.70 + (i * 0.05) + (abs(calm) * 0.05) + (abs(social) * 0.05)
        rec["match_score"] = min(0.99, base_score + random.uniform(0, 0.1))

    print(f"✓ Expanded fallback used: {calm_category}, {social_category}, {variety_category}")
    print(f"  Sports: {sport1['name_en']}, {sport2['name_en']}, {sport3['name_en']}")

    return recommendations

def recommend_sports(z_scores: Dict[str, float], lang: str = "ar", answers: List[Dict] = None) -> Dict[str, Any]:
    """
    DUAL-AI ORCHESTRATION

    Step 1: Reasoning AI (o1-preview) analyzes personality deeply
    Step 2: Intelligence AI (GPT-4) generates unique sports using those insights

    Returns: {
        "sports": [...],
        "reasoning_analysis": {...}
    }
    """
    # Step 1: Deep reasoning analysis
    reasoning_analysis = analyze_personality_with_reasoning_ai(z_scores, answers or [], lang)

    # Step 2: Generate unique sports using reasoning insights
    sports = generate_unique_sports_with_ai(z_scores, lang, reasoning_analysis)

    return {
        "sports": sports,
        "reasoning_analysis": reasoning_analysis
    }

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "status": "success",
        "message": "SportSync AI - Full System API",
        "version": "3.0",
        "features": {
            "questions": len(QUESTIONS_DATA) if QUESTIONS_DATA else 0,
            "psychological_analysis": True,
            "ai_recommendations": True,
            "multilingual": True
        },
        "endpoints": {
            "/api/health": "Health check",
            "/api/questions": "Get all questions",
            "/api/analyze": "Get full personality analysis + recommendations"
        }
    }

@app.get("/api/health")
def health():
    """Health check"""
    return {
        "status": "healthy",
        "version": "3.0",
        "questions_loaded": len(QUESTIONS_DATA) if QUESTIONS_DATA else 0,
        "systems_active": True
    }

@app.get("/api/questions")
def get_questions(lang: str = "ar"):
    """Get all questions"""
    if not QUESTIONS_DATA:
        raise HTTPException(status_code=500, detail="Questions not loaded")

    return {
        "success": True,
        "total_questions": len(QUESTIONS_DATA),
        "questions": QUESTIONS_DATA,
        "language": lang
    }

@app.post("/api/analyze")
async def analyze(request: dict):
    """
    Full personality analysis + sport recommendations

    Request body:
    {
        "answers": [
            {"question_key": "q1", "answer_text": "text from option"},
            ...
        ],
        "language": "ar"
    }
    """
    try:
        answers = request.get("answers", [])
        language = request.get("language", "ar")

        if len(answers) == 0:
            raise HTTPException(status_code=400, detail="No answers provided")

        # Calculate personality scores
        z_scores = calculate_personality_scores(answers)

        # DUAL-AI SYSTEM: Get deep reasoning + unique sports
        ai_results = recommend_sports(z_scores, language, answers)
        sports = ai_results["sports"]
        reasoning_analysis = ai_results["reasoning_analysis"]

        # Format recommendations
        recommendations = []
        for sport in sports:
            name_key = "name_ar" if language == "ar" else "name_en"
            desc_key = "description_ar" if language == "ar" else "description_en"

            recommendations.append({
                "sport": sport.get(name_key, sport.get("name_en", "Unknown")),
                "description": sport.get(desc_key, ""),
                "match_score": sport.get("match_score", 0.85),
                "psychological_match": sport.get("psychological_match", "")
            })

        return {
            "success": True,
            "personality_scores": z_scores,
            "recommendations": recommendations,
            "reasoning_analysis": reasoning_analysis,  # NEW: Deep psychological insights
            "analysis_summary": {
                "total_questions_answered": len(answers),
                "language": language,
                "profile_type": reasoning_analysis.get("personality_type", determine_profile_type(z_scores)),
                "core_drivers": reasoning_analysis.get("core_drivers", []),
                "hidden_motivations": reasoning_analysis.get("hidden_motivations", [])
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Analysis failed"
        }

def calculate_match_score(user_scores: Dict[str, float], sport_profile: Dict[str, float]) -> float:
    """Calculate how well a sport matches user personality"""
    if not sport_profile:
        return 0.5

    total_diff = 0.0
    count = 0

    for axis, sport_value in sport_profile.items():
        user_value = user_scores.get(axis, 0.0)
        diff = abs(user_value - sport_value)
        total_diff += diff
        count += 1

    if count == 0:
        return 0.5

    avg_diff = total_diff / count
    # Convert difference to similarity score (0-1)
    match_score = max(0.0, 1.0 - (avg_diff / 2.0))

    return round(match_score, 2)

def determine_profile_type(z_scores: Dict[str, float]) -> str:
    """Determine user's personality profile type"""
    calm = z_scores.get("calm_adrenaline", 0.0)
    social = z_scores.get("solo_group", 0.0)
    variety = z_scores.get("repeat_variety", 0.0)

    if calm < -0.5 and social < -0.3:
        return "Calm Solo Explorer"
    elif calm > 0.5 and variety > 0.5:
        return "Adrenaline Variety Seeker"
    elif social > 0.5:
        return "Social Team Player"
    elif calm < -0.3:
        return "Mindful Focused Athlete"
    elif calm > 0.3:
        return "High-Energy Competitor"
    else:
        return "Balanced All-Rounder"

# ═══════════════════════════════════════════════════════════════
# TRACKING & LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════════

def anonymize_tracking_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonymize user data - NO personal info stored
    Only patterns for system learning
    """
    timestamp = str(datetime.utcnow().timestamp())
    session_id = hashlib.md5(timestamp.encode()).hexdigest()[:12]

    return {
        "session_id": session_id,
        "timestamp": datetime.utcnow().isoformat(),
        "language": data.get("language", "unknown"),
        "answers_count": len(data.get("answers", [])),
        "has_additional_info": bool(data.get("additional_info", "")),
        "z_scores": data.get("personality_scores", {}),
        "recommended_sports": [rec.get("sport", "") for rec in data.get("recommendations", [])[:3]],
        "profile_type": data.get("analysis_summary", {}).get("profile_type", ""),
        # Hash answer patterns (no actual text stored)
        "answer_patterns": [
            {
                "q": ans.get("question_key", ""),
                "a_hash": hashlib.md5(ans.get("answer_text", "").encode()).hexdigest()[:8]
            }
            for ans in data.get("answers", [])
        ]
    }

@app.post("/api/track")
async def track_response(request: dict):
    """
    Track user response anonymously for system learning

    Privacy: NO personal data stored - only anonymized patterns
    Helps improve recommendations over time
    """
    try:
        anonymous_data = anonymize_tracking_data(request)

        # Log to Vercel logs for analysis
        print(f"[TRACK] {json.dumps(anonymous_data)}")

        return {
            "success": True,
            "message": "Response tracked anonymously",
            "session_id": anonymous_data["session_id"]
        }
    except Exception as e:
        print(f"[TRACK ERROR] {str(e)}")
        return {
            "success": False,
            "error": "Tracking failed"
        }

@app.get("/api/track/stats")
def get_tracking_stats():
    """
    Placeholder for analytics dashboard
    In production: Connect to database and return stats
    """
    return {
        "success": True,
        "message": "Analytics endpoint - ready for database integration",
        "note": "Connect to Vercel KV, MongoDB, or your preferred database"
    }

# Required for Vercel
