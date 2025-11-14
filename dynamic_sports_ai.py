# -*- coding: utf-8 -*-
"""
core/dynamic_sports_ai.py

Dynamic Sports Recommendation Engine
الذكاء يستخدم معرفته بـ 8000+ رياضة بدون حاجة لـ KB

الفكرة:
- الذكاء (GPT-4) عنده معرفة بآلاف الرياضات
- نعطيه profile المستخدم
- هو يحلل ويقترح من معرفته
- يخترع رياضات هجينة إذا لزم الأمر
"""

from typing import Dict, List, Any, Optional
import json

class DynamicSportsAI:
    """محرك توصيات رياضية ديناميكي"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def recommend_sports(self, 
                        user_profile: Dict[str, Any],
                        z_scores: Dict[str, float],
                        systems_analysis: Dict[str, Any],
                        lang: str = "العربية",
                        count: int = 3) -> List[Dict[str, Any]]:
        """
        التوصية بالرياضات من معرفة الذكاء
        
        Args:
            user_profile: ملف المستخدم الكامل
            z_scores: نتائج Layer-Z
            systems_analysis: نتائج الأنظمة الـ 15
            lang: اللغة
            count: عدد التوصيات
        
        Returns:
            قائمة بالرياضات المقترحة مع التفاصيل
        """
        
        # بناء الـ prompt للذكاء
        prompt = self._build_prompt(user_profile, z_scores, systems_analysis, lang, count)
        
        # استدعاء الذكاء
        if self.llm_client:
            response = self._call_llm(prompt)
            sports = self._parse_llm_response(response, lang)
        else:
            # Fallback: توصيات أساسية
            sports = self._fallback_recommendations(user_profile, z_scores, count)
        
        return sports
    
    def _build_prompt(self, profile: Dict, z_scores: Dict, 
                     systems: Dict, lang: str, count: int) -> str:
        """بناء prompt ذكي للذكاء"""
        
        ar = (lang == "العربية")
        
        prompt = f"""أنت خبير عالمي في الرياضة وعلم النفس الرياضي.

لديك معرفة بأكثر من 8000 رياضة من جميع أنحاء العالم:
- رياضات تقليدية (كرة القدم، السباحة، الجودو...)
- رياضات نادرة (كروكيه، سيبك تاكرو، جيوكيندو...)
- رياضات حديثة (VR sports، esports، parkour...)
- رياضات هجينة (يمكنك اختراع واحدة جديدة!)

معطيات المستخدم:

## Layer-Z Axes:
{json.dumps(z_scores, ensure_ascii=False, indent=2)}

## تحليل الأنظمة الـ 15:
{json.dumps(systems, ensure_ascii=False, indent=2)}

## Profile:
{json.dumps(profile, ensure_ascii=False, indent=2)}

المطلوب:
قدم {count} توصيات رياضية مخصصة لهذا المستخدم.

**القواعد المهمة:**
1. استخدم معرفتك الواسعة - لا تقتصر على رياضات مشهورة فقط
2. ابحث عن رياضات نادرة إذا كانت مناسبة
3. يمكنك اختراع رياضة هجينة جديدة إذا لم تجد مطابقة مثالية
4. كل توصية يجب أن تكون مفصلة

**Format الإخراج (JSON):**
```json
[
  {{
    "sport_name": "اسم الرياضة",
    "category": "التصنيف (تقليدي/نادر/هجين/مخترع)",
    "match_score": 0.95,
    "why_perfect": "لماذا مناسبة لهذا المستخدم (3 جمل)",
    "inner_sensation": "الإحساس الداخلي المتوقع",
    "first_week": "خطة الأسبوع الأول (نوعية)",
    "skills_needed": ["مهارة 1", "مهارة 2", "مهارة 3"],
    "vr_variant": "نسخة VR إن وُجدت",
    "difficulty": 3,
    "risk_level": "low/medium/high",
    "solo_or_group": "solo/group/both",
    "indoor_outdoor": "indoor/outdoor/both"
  }}
]
```

**ابدأ التحليل والتوصية:**
"""
        
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """استدعاء الذكاء"""
        try:
            from core.llm_client import chat_once
            
            response = chat_once(
                self.llm_client,
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o",
                max_tokens=2000,
                temperature=0.8  # إبداع معتدل
            )
            
            return response
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "{}"
    
    def _parse_llm_response(self, response: str, lang: str) -> List[Dict[str, Any]]:
        """تحليل رد الذكاء"""
        try:
            # إزالة markdown إذا وُجد
            response = response.replace("```json", "").replace("```", "").strip()
            
            # تحويل JSON
            sports = json.loads(response)
            
            # التحقق من الصيغة
            if isinstance(sports, list):
                return sports
            else:
                return [sports]
        
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return []
    
    def _fallback_recommendations(self, profile: Dict, 
                                  z_scores: Dict, count: int) -> List[Dict[str, Any]]:
        """توصيات احتياطية إذا فشل الذكاء"""
        
        # منطق بسيط بناءً على المحاور
        sports = []
        
        # مثال بسيط
        if z_scores.get("calm_adrenaline", 0) < -0.5:
            sports.append({
                "sport_name": "Yoga",
                "category": "تقليدي",
                "match_score": 0.75,
                "why_perfect": "يناسب شخصيتك الهادئة",
                "difficulty": 2,
                "solo_or_group": "both"
            })
        
        if z_scores.get("solo_group", 0) < -0.5:
            sports.append({
                "sport_name": "Football",
                "category": "تقليدي",
                "match_score": 0.70,
                "why_perfect": "رياضة جماعية ممتعة",
                "difficulty": 3,
                "solo_or_group": "group"
            })
        
        # إضافة رياضة افتراضية
        sports.append({
            "sport_name": "Swimming",
            "category": "تقليدي",
            "match_score": 0.65,
            "why_perfect": "رياضة شاملة ومتوازنة",
            "difficulty": 2,
            "solo_or_group": "solo"
        })
        
        return sports[:count]

# مثال الاستخدام
if __name__ == "__main__":
    # Test
    engine = DynamicSportsAI()
    
    test_profile = {
        "age_range": "25-35",
        "goals": ["fitness", "mental_clarity"]
    }
    
    test_z_scores = {
        "calm_adrenaline": -0.7,
        "solo_group": 0.4,
        "technical_intuitive": 0.3
    }
    
    test_systems = {
        "big_five": {"type": "INTJ"},
        "mbti": {"type": "INTJ"}
    }
    
    recommendations = engine.recommend_sports(
        test_profile,
        test_z_scores,
        test_systems,
        lang="العربية",
        count=3
    )
    
    print("🎯 التوصيات:")
    for i, sport in enumerate(recommendations, 1):
        print(f"\n{i}. {sport.get('sport_name', 'N/A')}")
        print(f"   التطابق: {sport.get('match_score', 0):.0%}")
        print(f"   السبب: {sport.get('why_perfect', 'N/A')}")
