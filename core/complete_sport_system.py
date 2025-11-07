# -*- coding: utf-8 -*-
"""
Complete Sport Invention Integration
=====================================
النظام الكامل المتكامل - نسخة محسّنة ونظيفة
"""

from typing import Dict, List, Any, Optional
import json

# Import all components
try:
    from core.advanced_sport_inventor import get_advanced_inventor
    from core.dual_model_client import (
        analyze_user_with_discovery,
        _init_dual_models
    )
    from core.llm_client import chat_once, make_llm_client_singleton
    FULL_SYSTEM_AVAILABLE = True
except Exception as e:
    print(f"[INTEGRATION] Import error: {e}")
    FULL_SYSTEM_AVAILABLE = False


def generate_complete_sport_recommendations(
    user_answers: Dict[str, Any],
    user_traits: Dict[str, float],
    user_identity: Dict[str, float],
    language: str = 'ar',
    num_recommendations: int = 3
) -> List[Dict[str, Any]]:
    """
    توليد التوصيات الكاملة - شخصية وعميقة
    """
    
    if not FULL_SYSTEM_AVAILABLE:
        return _fallback_recommendations(language)
    
    print("[INTEGRATION] Starting complete invention process...")
    
    # Step 1: Discovery Analysis
    print("[INTEGRATION] Step 1/6: Discovery Model analysis...")
    discovery_analysis = analyze_user_with_discovery(
        answers=user_answers,
        identity=user_identity,
        traits=user_traits,
        lang=language
    )
    
    # Step 2: Advanced Inventor
    print("[INTEGRATION] Step 2/6: Advanced Sport Invention...")
    inventor = get_advanced_inventor()
    
    inventions = []
    for i in range(num_recommendations):
        try:
            invention = inventor.invent_sport(
                user_answers=user_answers,
                traits=user_traits,
                lang=language
            )
            
            if invention:
                invention['discovery_insights'] = discovery_analysis.get('initial_insights', {})
                invention['layer_z_drivers'] = discovery_analysis.get('hidden_drives', [])
                inventions.append(invention)
                
        except Exception as e:
            print(f"[INTEGRATION] Invention {i} failed: {e}")
    
    # Step 3: Reasoning Model Enhancement
    print("[INTEGRATION] Step 3/6: Reasoning Model enhancement...")
    if len(inventions) > 0:
        inventions = _enhance_with_reasoning(inventions, discovery_analysis, user_traits, language)
    
    # Step 4: Validate and score
    print("[INTEGRATION] Step 4/6: Validation...")
    inventions = _validate_and_score(inventions, user_traits)
    
    # Step 5: Sort and return top N
    print("[INTEGRATION] Step 5/6: Finalization...")
    inventions.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    
    final_inventions = inventions[:num_recommendations]
    
    print(f"[INTEGRATION] ✅ Generated {len(final_inventions)} complete sport inventions")
    
    return final_inventions


def _enhance_with_reasoning(
    inventions: List[Dict],
    discovery_analysis: Dict,
    user_traits: Dict[str, float],
    language: str
) -> List[Dict]:
    """
    تحسين الاختراعات باستخدام Reasoning Model - مع تشخيص نفسي عميق
    """
    try:
        _init_dual_models()
        client = make_llm_client_singleton()
        
        if not client:
            return inventions
        
        # بناء السياق الشخصي العميق
        user_context = _build_personal_context(discovery_analysis, user_traits, language)
        
        if language == 'ar':
            system_prompt = """أنت مستشار رياضي نفسي عميق. مهمتك: تشخيص الهوية الرياضية المخفية.

**البنية الدقيقة (EXACTLY):**

```json
{
  "sports": [
    {
      "sport_name": "[اسم مثير بالإنجليزية]",
      "what_is_it": [
        "جملة 1 - وصف التجربة",
        "جملة 2 - عناصر الرياضة",
        "جملة 3 - الإحساس العميق"
      ],
      "why_suits_you": [
        "أنت [صفة نفسية] - [ربط بالرياضة]",
        "[دافع خفي] - [كيف تلمسه الرياضة]",
        "[متعة حقيقية] - [ليس مجرد حركة]"
      ],
      "how_it_looks": [
        "تدخل [وصف البداية]",
        "تستخدم [التجربة الحية]",
        "[نتيجة نفسية] - داخلك تعرف إنك تنمو"
      ],
      "important_notes": [
        "[جملة قوية تلامس الهوية]",
        "[نصيحة عملية للبدء]"
      ]
    }
  ]
}
```

**مثال حقيقي:**
"أنت تكره التكرار، ترفض السطحية، وتحب توصل لجوهر الشي الحقيقي"

**CRITICAL:**
- استخدم "أنت" في كل جملة بـ why_suits_you
- الطول الكلي: 120-180 كلمة
- لا تذكر VR إلا إذا كان مناسب للشخصية
- التركيز على الهوية والشعور

JSON format ONLY."""
        else:
            system_prompt = """You are a deep sports psychologist. Mission: Diagnose hidden athletic identity.

**Exact Structure (EXACTLY):**

```json
{
  "sports": [
    {
      "sport_name": "[Exciting English name]",
      "what_is_it": [
        "Sentence 1 - experience description",
        "Sentence 2 - sport elements",
        "Sentence 3 - deep feeling"
      ],
      "why_suits_you": [
        "You [psychological trait] - [sport connection]",
        "[Hidden driver] - [how sport touches it]",
        "[True pleasure] - [not just movement]"
      ],
      "how_it_looks": [
        "You enter [start description]",
        "You use [live experience]",
        "[Psychological result] - inside you know you're growing"
      ],
      "important_notes": [
        "[One powerful identity-touching sentence]",
        "[Practical advice to start]"
      ]
    }
  ]
}
```

**Real Example:**
"You hate repetition, reject superficiality, and love reaching the true essence"

**CRITICAL:**
- Use "You" in every why_suits_you sentence
- Total length: 120-180 words
- Mention VR only if fits personality
- Focus on identity and feeling

JSON format ONLY."""
        
        import os
        reasoning_model = os.getenv("CHAT_MODEL_REASONING", "gpt-4o")
        
        reasoning_data = {
            'inventions': [
                {
                    'label': inv.get('sport_label'),
                    'base': inv.get('base_sport'),
                    'components': inv.get('hybrid_components', [])
                }
                for inv in inventions
            ],
            'language': language
        }
        
        enhanced_json = chat_once(
            client,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_context + "\n\n" + json.dumps(reasoning_data, ensure_ascii=False)}
            ],
            model=reasoning_model,
            temperature=0.7,
            max_tokens=800
        )
        
        # Parse and merge
        try:
            enhanced_data = json.loads(enhanced_json)
            enhanced_sports = enhanced_data.get('sports', [])
            
            for i, sport in enumerate(enhanced_sports):
                if i < len(inventions):
                    inventions[i]['sport_name'] = sport.get('sport_name', inventions[i].get('sport_label'))
                    inventions[i]['what_is_it'] = sport.get('what_is_it', [])
                    inventions[i]['why_suits_you'] = sport.get('why_suits_you', [])
                    inventions[i]['how_it_looks'] = sport.get('how_it_looks', [])
                    inventions[i]['important_notes'] = sport.get('important_notes', [])
                    
        except Exception as e:
            print(f"[REASONING] JSON parse failed: {e}")
        
    except Exception as e:
        print(f"[REASONING] Enhancement failed: {e}")
    
    return inventions


def _validate_and_score(
    inventions: List[Dict],
    traits: Dict[str, float]
) -> List[Dict]:
    """
    التحقق من صحة الاختراعات وتقييمها
    """
    for invention in inventions:
        # Map old fields to new structure if needed
        if 'sport_label' in invention and 'sport_name' not in invention:
            invention['sport_name'] = invention['sport_label']
        
        if 'what_is_it' not in invention or not invention['what_is_it']:
            # Generate from existing data
            label = invention.get('sport_name', invention.get('sport_label', 'رياضة مخصصة'))
            base = invention.get('base_sport', '')
            if base:
                invention['what_is_it'] = [
                    f"تجربة رياضية مبتكرة تجمع عناصر {base}",
                    "مصممة خصيصاً لتناسب شخصيتك",
                    "تركز على المتعة والتطور المستمر"
                ]
            else:
                invention['what_is_it'] = [
                    f"{label} - تجربة فريدة",
                    "مصممة لتلامس دوافعك العميقة",
                    "كل جلسة فرصة جديدة للنمو"
                ]
        
        if 'why_suits_you' not in invention or not invention['why_suits_you']:
            # Generate from traits
            top_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)[:3]
            invention['why_suits_you'] = [
                f"أنت تمتلك {top_traits[0][0]} بنسبة عالية",
                "تبحث عن تجربة تلامس شخصيتك الحقيقية",
                "هذه الرياضة تفهم دوافعك الخفية"
            ]
        
        if 'how_it_looks' not in invention or not invention['how_it_looks']:
            first_week = invention.get('first_week', {})
            if first_week:
                steps = list(first_week.values())[:3]
                invention['how_it_looks'] = steps if steps else [
                    "تدخل التجربة بعقل منفتح",
                    "تستخدم جسمك وعقلك معاً",
                    "كل لحظة فرصة للنمو"
                ]
            else:
                invention['how_it_looks'] = [
                    "تبدأ بجلسة قصيرة 10-15 دقيقة",
                    "تشعر بالاتصال بين العقل والجسد",
                    "التقدم يأتي طبيعياً مع الممارسة"
                ]
        
        if 'important_notes' not in invention or not invention['important_notes']:
            where_start = invention.get('where_to_start', [])
            invention['important_notes'] = where_start[:2] if where_start else [
                "ابدأ بدون ضغط أو توقعات",
                "استمتع بالرحلة أكثر من الوجهة"
            ]
        
        # Validate word count
        total_words = 0
        for field in ['what_is_it', 'why_suits_you', 'how_it_looks', 'important_notes']:
            items = invention.get(field, [])
            if isinstance(items, list):
                total_words += sum(len(str(item).split()) for item in items)
        
        # Validate "أنت" usage
        why_suits = invention.get('why_suits_you', [])
        you_count = sum(1 for item in why_suits if 'أنت' in str(item) or 'You' in str(item))
        
        # Calculate score
        base_score = 85
        if 120 <= total_words <= 180:
            base_score += 5
        if you_count >= 2:
            base_score += 5
        if all(k in invention for k in ['sport_name', 'what_is_it', 'why_suits_you']):
            base_score += 5
        
        invention['match_score'] = min(base_score, 100)
        invention['word_count'] = total_words
        invention['you_count'] = you_count
    
    return inventions


def _build_personal_context(
    discovery_analysis: Dict, 
    user_traits: Dict[str, float],
    language: str
) -> str:
    """
    بناء السياق الشخصي العميق
    """
    
    # Extract dominant identity
    identity_scores = discovery_analysis.get('identity_scores', {})
    if identity_scores:
        dominant_identity = max(identity_scores.items(), key=lambda x: x[1])[0]
        identity_strength = max(identity_scores.values())
    else:
        dominant_identity = 'explorer'
        identity_strength = 0.5
    
    # Extract hidden drivers
    hidden_drivers = discovery_analysis.get('hidden_drives', [])[:3]
    
    # Extract top traits
    top_traits = sorted(user_traits.items(), key=lambda x: x[1], reverse=True)[:3]
    
    if language == 'ar':
        context = f"""**السياق الشخصي العميق:**

🧬 الهوية الأقوى: {dominant_identity} ({identity_strength:.0%})

🔥 الدوافع الخفية (Layer Z):
{chr(10).join([f'• {driver}' for driver in hidden_drivers]) if hidden_drivers else '• بحث عن المعنى'}

🧠 السمات النفسية الأقوى:
{chr(10).join([f'• {trait}: {score:.0%}' for trait, score in top_traits])}

**مهمتك:**
اخترع رياضة تلامس هذه الهوية والدوافع بعمق.
استخدم لغة "أنت" المباشرة.
اجعلهم يشعرون "هذا أنا تماماً!".
"""
    else:
        context = f"""**Deep Personal Context:**

🧬 Dominant Identity: {dominant_identity} ({identity_strength:.0%})

🔥 Hidden Drivers (Layer Z):
{chr(10).join([f'• {driver}' for driver in hidden_drivers]) if hidden_drivers else '• Seeking meaning'}

🧠 Strongest Traits:
{chr(10).join([f'• {trait}: {score:.0%}' for trait, score in top_traits])}

**Your Mission:**
Invent a sport touching this identity and drivers deeply.
Use direct "you" language.
Make them feel "This is exactly ME!".
"""
    
    return context


def _fallback_recommendations(language: str) -> List[Dict]:
    """
    توصيات احتياطية
    """
    if language == 'ar':
        return [
            {
                'sport_name': 'رياضة مخصصة',
                'what_is_it': ['تجربة فريدة قيد التطوير'],
                'why_suits_you': ['تم تصميمها خصيصاً لك'],
                'how_it_looks': ['ستكتشفها قريباً'],
                'important_notes': ['جاري العمل على تخصيصها'],
                'match_score': 75,
                'fallback': True
            }
        ]
    else:
        return [
            {
                'sport_name': 'Custom Sport',
                'what_is_it': ['Unique experience in development'],
                'why_suits_you': ['Designed specifically for you'],
                'how_it_looks': ['You will discover it soon'],
                'important_notes': ['Currently being customized'],
                'match_score': 75,
                'fallback': True
            }
        ]


__all__ = ['generate_complete_sport_recommendations']
