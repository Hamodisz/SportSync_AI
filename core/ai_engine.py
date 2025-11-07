#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Core - Triple Intelligence System (OpenAI 1.x Compatible)
===========================================================
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SportSyncAI:
    """Triple Intelligence System"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found!")
        
        self.client = OpenAI(api_key=api_key)
        
        self.models = {
            'fast': 'gpt-3.5-turbo',
            'reasoning': 'gpt-4o',  # Changed from o1-mini
            'intelligence': 'gpt-4o'
        }
        
        logger.info("✅ AI System Ready")
    
    def call_ai(self, messages: List[Dict], model: str, temp: float = 0.7, max_tokens: int = 1500) -> Optional[str]:
        """Call OpenAI API"""
        try:
            logger.info(f"🔄 Calling {model}...")
            
            # o1 models use different parameter names
            if model.startswith('o1'):
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens
                )
            else:
                response = self.client.chat.completions.create(
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
}}""" if lang == "ar" else f"""Extract key information:

{user_input}

Return JSON:
{{
  "emotional_state": "brief",
  "constraints": ["c1", "c2"],
  "goals": ["g1", "g2"]
}}"""
        
        messages = [{"role": "user", "content": prompt}]
        return self.call_ai(messages, self.models['fast'], temp=0.3, max_tokens=300)
    
    def analyze_deep(self, quick_insights: str, user_input: str, lang: str = "ar") -> Optional[str]:
        """Layer 2: Deep reasoning"""
        logger.info("🧠 LAYER 2: Deep Reasoning")
        
        prompt = f"""التحليل السريع: {quick_insights}

قم بتحليل عميق:
1. الدوافع الخفية
2. مستوى الجاهزية
3. الحواجز
4. نوع الشخصية

اكتب تحليل شامل.""" if lang == "ar" else f"""Quick insights: {quick_insights}

Deep analysis:
1. Hidden motivations
2. Readiness
3. Barriers
4. Personality type

Write comprehensive analysis."""
        
        messages = [{"role": "user", "content": prompt}]
        return self.call_ai(messages, self.models['reasoning'], temp=1.0, max_tokens=2000)
    
    def generate_recommendations(self, quick: str, deep: str, lang: str = "ar") -> Optional[str]:
        """Layer 3: Final recommendations"""
        logger.info("🎯 LAYER 3: Recommendations")
        
        system = f"""أنت مستشار رياضي في SportSync.

التحليلات:
- السريع: {quick}
- العميق: {deep}

أنشئ 3 توصيات رياضية JSON:
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

ممنوع: أوقات، تكاليف، أماكن، معدات.""" if lang == "ar" else f"""You are a sport consultant.

Analysis:
- Quick: {quick}
- Deep: {deep}

Create 3 personalized sport recommendations in JSON.

Forbidden: times, costs, locations, equipment."""
        
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": "أعطني التوصيات" if lang == "ar" else "Give recommendations"}
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
