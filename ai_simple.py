#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Core - Simple & Reliable Triple Intelligence System
======================================================
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SportSyncAI:
    """Simple, reliable AI system with 3 layers"""
    
    def __init__(self):
        """Initialize OpenAI"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found!")
        
        openai.api_key = self.api_key
        
        self.models = {
            'fast': 'gpt-3.5-turbo',
            'reasoning': 'o1-mini',
            'intelligence': 'gpt-4'
        }
        
        logger.info("✅ AI System Ready")
    
    def call_ai(self, messages: List[Dict], model: str, temp: float = 0.7, max_tokens: int = 1500) -> Optional[str]:
        """Call OpenAI API"""
        try:
            logger.info(f"🔄 Calling {model}...")
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            logger.info(f"✅ {model} responded")
            return content
            
        except Exception as e:
            logger.error(f"❌ {model} failed: {e}")
            return None
    
    def analyze_fast(self, user_input: str, lang: str = "ar") -> Optional[str]:
        """Layer 1: Fast analysis"""
        logger.info("🚀 LAYER 1: Fast Analysis")
        
        prompt = f"""استخرج المعلومات الأساسية من وصف المستخدم:

{user_input}

أعط JSON فقط:
{{
  "emotional_state": "وصف قصير",
  "constraints": ["قيد1", "قيد2"],
  "goals": ["هدف1", "هدف2"]
}}""" if lang == "ar" else f"""Extract key information from user description:

{user_input}

Return JSON only:
{{
  "emotional_state": "brief description",
  "constraints": ["constraint1", "constraint2"],
  "goals": ["goal1", "goal2"]
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        return self.call_ai(messages, self.models['fast'], temp=0.3, max_tokens=300)
    
    def analyze_deep(self, quick_insights: str, user_input: str, lang: str = "ar") -> Optional[str]:
        """Layer 2: Deep reasoning"""
        logger.info("🧠 LAYER 2: Deep Reasoning")
        
        prompt = f"""التحليل السريع: {quick_insights}

قم بتحليل عميق للمستخدم:
1. الدوافع الخفية (Z-layer)
2. مستوى الجاهزية
3. الحواجز غير المعلنة
4. نوع الشخصية الرياضية

اكتب تحليل شامل.""" if lang == "ar" else f"""Quick insights: {quick_insights}

Perform deep analysis:
1. Hidden motivations (Z-layer)
2. Readiness level
3. Unstated barriers
4. Sport personality type

Write comprehensive analysis."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.call_ai(messages, self.models['reasoning'], temp=1.0, max_tokens=2000)
    
    def generate_recommendations(self, quick: str, deep: str, lang: str = "ar") -> Optional[str]:
        """Layer 3: Final recommendations"""
        logger.info("🎯 LAYER 3: Recommendations")
        
        system = f"""أنت مستشار رياضي في SportSync.

التحليل السريع: {quick}
التحليل العميق: {deep}

أنشئ 3 توصيات رياضية مخصصة بصيغة JSON:
{{
  "recommendations": [
    {{
      "title": "اسم الرياضة",
      "essence": "جملة واحدة",
      "experience": "فقرة عن التجربة",
      "why_perfect": ["سبب1", "سبب2", "سبب3"],
      "first_week": "خطة الأسبوع الأول",
      "signs_of_progress": ["علامة1", "علامة2"]
    }}
  ]
}}

ممنوع: أوقات محددة، تكاليف، أماكن، معدات.
ركز على: التجربة، المشاعر، التحول.""" if lang == "ar" else f"""You are a sport consultant at SportSync.

Quick insights: {quick}
Deep analysis: {deep}

Create 3 personalized sport recommendations in JSON:
{{
  "recommendations": [
    {{
      "title": "Sport name",
      "essence": "One sentence",
      "experience": "Experience paragraph",
      "why_perfect": ["reason1", "reason2", "reason3"],
      "first_week": "First week plan",
      "signs_of_progress": ["sign1", "sign2"]
    }}
  ]
}}

Forbidden: specific times, costs, locations, equipment.
Focus on: experience, emotions, transformation."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "أعطني التوصيات الآن" if lang == "ar" else "Give recommendations now"}
        ]
        
        return self.call_ai(messages, self.models['intelligence'], temp=0.7, max_tokens=2500)
    
    def run_pipeline(self, user_input: str, lang: str = "ar") -> Dict[str, Any]:
        """Run full pipeline"""
        logger.info("=" * 60)
        logger.info("🚀 STARTING PIPELINE")
        logger.info("=" * 60)
        
        result = {
            "success": False,
            "recommendations": None,
            "error": None
        }
        
        # Layer 1
        fast = self.analyze_fast(user_input, lang)
        if not fast:
            result["error"] = "Layer 1 failed"
            return result
        
        # Layer 2
        deep = self.analyze_deep(fast, user_input, lang)
        if not deep:
            result["error"] = "Layer 2 failed"
            return result
        
        # Layer 3
        recs = self.generate_recommendations(fast, deep, lang)
        if not recs:
            result["error"] = "Layer 3 failed"
            return result
        
        result["success"] = True
        result["recommendations"] = recs
        
        logger.info("✅ PIPELINE COMPLETE!")
        return result


# Global instance
_ai = None

def get_ai() -> SportSyncAI:
    global _ai
    if _ai is None:
        _ai = SportSyncAI()
    return _ai

def generate_sport_recommendations(user_input: str, lang: str = "ar") -> Dict[str, Any]:
    ai = get_ai()
    return ai.run_pipeline(user_input, lang)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    test = "أبحث عن رياضة هادئة تساعدني على التركيز"
    result = generate_sport_recommendations(test, "ar")
    print(json.dumps(result, ensure_ascii=False, indent=2))
