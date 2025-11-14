#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Orchestrator - Triple Intelligence System
============================================
Uses 3 AI models in sequence:
1. Fast Model (GPT-3.5-turbo) - Quick understanding
2. Reasoning Model (o1-mini) - Deep analysis
3. Intelligence Model (GPT-4) - Final recommendations

NO FALLBACK ALLOWED - System must work or fail explicitly.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Structured response from AI system"""
    success: bool
    data: Any
    model_used: str
    tokens_used: int
    error: Optional[str] = None


class TripleIntelligenceSystem:
    """
    The core AI engine - NO FALLBACK, ONLY SUCCESS OR EXPLICIT FAILURE
    """
    
    def __init__(self):
        """Initialize with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("❌ CRITICAL: OPENAI_API_KEY not found!")
        
        try:
            self.client = OpenAI(api_key=api_key)
        except TypeError:
            # Fallback for older OpenAI versions
            import openai
            openai.api_key = api_key
            self.client = openai
        
        # Model configuration
        self.models = {
            'fast': 'gpt-3.5-turbo',
            'reasoning': 'o1-mini', 
            'intelligence': 'gpt-4'
        }
        
        logger.info("✅ Triple Intelligence System initialized")
        logger.info(f"📊 Models: Fast={self.models['fast']}, "
                   f"Reasoning={self.models['reasoning']}, "
                   f"Intelligence={self.models['intelligence']}")
    
    def _call_openai(self, 
                     messages: List[Dict[str, str]], 
                     model: str,
                     temperature: float = 0.7,
                     max_tokens: int = 1500) -> AIResponse:
        """
        Direct OpenAI API call with strict error handling
        NO FALLBACK - fails explicitly if error occurs
        """
        try:
            logger.info(f"🔄 Calling {model}...")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens
            
            logger.info(f"✅ {model} responded - {tokens} tokens")
            
            return AIResponse(
                success=True,
                data=content,
                model_used=model,
                tokens_used=tokens
            )
            
        except Exception as e:
            error_msg = f"❌ {model} FAILED: {str(e)}"
            logger.error(error_msg)
            
            return AIResponse(
                success=False,
                data=None,
                model_used=model,
                tokens_used=0,
                error=error_msg
            )
    
    def analyze_user_fast(self, user_input: str, lang: str = "ar") -> AIResponse:
        """
        LAYER 1: Fast Analysis (GPT-3.5-turbo)
        Quick extraction of key insights
        """
        logger.info("🚀 LAYER 1: Fast Intelligence Layer")
        
        system_prompt = f"""أنت محلل سريع للمستخدمين في SportSync.
استخرج النقاط الأساسية فقط:
- الحالة العاطفية (Emotional State)
- القيود الشخصية (Constraints)  
- الأهداف المرجوة (Goals)

أعط إجابة JSON فقط بهذا الشكل:
{{
  "emotional_state": "وصف قصير",
  "constraints": ["قيد1", "قيد2"],
  "goals": ["هدف1", "هدف2"]
}}""" if lang == "ar" else """You are a fast user analyzer for SportSync.
Extract key points only:
- Emotional State
- Personal Constraints
- Desired Goals

Return JSON only in this format:
{{
  "emotional_state": "brief description",
  "constraints": ["constraint1", "constraint2"],
  "goals": ["goal1", "goal2"]
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self._call_openai(
            messages=messages,
            model=self.models['fast'],
            temperature=0.3,
            max_tokens=300
        )
    
    def analyze_deep_reasoning(self, quick_insights: str, user_input: str, lang: str = "ar") -> AIResponse:
        """
        LAYER 2: Deep Reasoning (o1-mini)
        Analyzes hidden motivations and readiness (Z-layer)
        """
        logger.info("🧠 LAYER 2: Reasoning Layer (Deep Thinking)")
        
        prompt = f"""التحليلات السريعة: {quick_insights}

الآن قم بتحليل عميق:

1. **الطبقة Z (Z-layer)**: ما هي الدوافع الخفية؟
2. **مستوى الجاهزية**: هل المستخدم جاهز فعلاً؟
3. **الحواجز غير المعلنة**: ماذا يمنعه من البدء؟
4. **نوع الشخصية الرياضية**: منفرد، جماعي، تكتيكي، عاطفي؟

فكر بعمق واعطني تحليل شامل.""" if lang == "ar" else f"""Quick insights: {quick_insights}

Now perform deep analysis:

1. **Z-layer**: What are the hidden motivations?
2. **Readiness Level**: Is the user truly ready?
3. **Unstated Barriers**: What prevents them from starting?
4. **Sport Personality Type**: Solo, team, tactical, emotional?

Think deeply and give comprehensive analysis."""
        
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        return self._call_openai(
            messages=messages,
            model=self.models['reasoning'],
            temperature=1.0,
            max_tokens=2000
        )
    
    def generate_recommendations(self, 
                                quick_insights: str,
                                deep_analysis: str,
                                lang: str = "ar") -> AIResponse:
        """
        LAYER 3: Intelligence Layer (GPT-4)
        Generates final personalized sport recommendations
        """
        logger.info("🎯 LAYER 3: Intelligence Layer (Final Recommendations)")
        
        system_prompt = f"""أنت مستشار رياضي ذكي في SportSync.
لديك:
- التحليل السريع: {quick_insights}
- التحليل العميق: {deep_analysis}

مهمتك: إنشاء 3 توصيات رياضية مخصصة بالكامل.

**متطلبات صارمة:**
- لا تذكر أوقات محددة (دقائق/ساعات)
- لا تذكر تكاليف أو أسعار
- لا تذكر أماكن محددة
- لا تذكر معدات رياضية
- ركز على التجربة والمشاعر والتحول الداخلي

**صيغة JSON المطلوبة:**
{{
  "recommendations": [
    {{
      "title": "اسم الرياضة المبتكر",
      "essence": "جملة واحدة تلخص الروح",
      "experience": "فقرة تصف التجربة الحية",
      "why_perfect": ["سبب1", "سبب2", "سبب3"],
      "first_week": "خطة الأسبوع الأول",
      "signs_of_progress": ["علامة1", "علامة2", "علامة3"]
    }}
  ]
}}

كن عميقاً، إنسانياً، ومُلهماً.""" if lang == "ar" else f"""You are an intelligent sport consultant at SportSync.
You have:
- Quick insights: {quick_insights}
- Deep analysis: {deep_analysis}

Your mission: Create 3 fully personalized sport recommendations.

**Strict requirements:**
- No specific times (minutes/hours)
- No costs or prices
- No specific locations
- No sports equipment
- Focus on experience, emotions, inner transformation

**Required JSON format:**
{{
  "recommendations": [
    {{
      "title": "Innovative sport name",
      "essence": "One sentence capturing the spirit",
      "experience": "Paragraph describing live experience",
      "why_perfect": ["reason1", "reason2", "reason3"],
      "first_week": "First week plan",
      "signs_of_progress": ["sign1", "sign2", "sign3"]
    }}
  ]
}}

Be deep, human, and inspiring."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "أعطني التوصيات المخصصة الآن" if lang == "ar" else "Give me the personalized recommendations now"}
        ]
        
        return self._call_openai(
            messages=messages,
            model=self.models['intelligence'],
            temperature=0.7,
            max_tokens=2500
        )
    
    def run_full_pipeline(self, user_input: str, lang: str = "ar") -> Dict[str, Any]:
        """
        Execute the complete triple intelligence pipeline
        Returns structured result with all layers' outputs
        
        NO FALLBACK - System must complete all 3 layers or fail explicitly
        """
        logger.info("=" * 60)
        logger.info("🚀 STARTING TRIPLE INTELLIGENCE PIPELINE")
        logger.info("=" * 60)
        
        result = {
            "success": False,
            "layers": {},
            "final_recommendations": None,
            "errors": [],
            "total_tokens": 0
        }
        
        # LAYER 1: Fast Analysis
        fast_response = self.analyze_user_fast(user_input, lang)
        result["layers"]["fast"] = {
            "success": fast_response.success,
            "data": fast_response.data,
            "tokens": fast_response.tokens_used
        }
        result["total_tokens"] += fast_response.tokens_used
        
        if not fast_response.success:
            result["errors"].append(f"LAYER 1 FAILED: {fast_response.error}")
            logger.error("❌ PIPELINE FAILED AT LAYER 1 - NO FALLBACK!")
            return result
        
        # LAYER 2: Deep Reasoning
        deep_response = self.analyze_deep_reasoning(
            fast_response.data, 
            user_input, 
            lang
        )
        result["layers"]["reasoning"] = {
            "success": deep_response.success,
            "data": deep_response.data,
            "tokens": deep_response.tokens_used
        }
        result["total_tokens"] += deep_response.tokens_used
        
        if not deep_response.success:
            result["errors"].append(f"LAYER 2 FAILED: {deep_response.error}")
            logger.error("❌ PIPELINE FAILED AT LAYER 2 - NO FALLBACK!")
            return result
        
        # LAYER 3: Intelligence Recommendations
        intel_response = self.generate_recommendations(
            fast_response.data,
            deep_response.data,
            lang
        )
        result["layers"]["intelligence"] = {
            "success": intel_response.success,
            "data": intel_response.data,
            "tokens": intel_response.tokens_used
        }
        result["total_tokens"] += intel_response.tokens_used
        
        if not intel_response.success:
            result["errors"].append(f"LAYER 3 FAILED: {intel_response.error}")
            logger.error("❌ PIPELINE FAILED AT LAYER 3 - NO FALLBACK!")
            return result
        
        # All layers succeeded!
        result["success"] = True
        result["final_recommendations"] = intel_response.data
        
        logger.info("=" * 60)
        logger.info("✅ PIPELINE COMPLETE - ALL 3 LAYERS SUCCEEDED!")
        logger.info(f"📊 Total tokens used: {result['total_tokens']}")
        logger.info("=" * 60)
        
        return result


# Global instance
_ai_system = None


def get_ai_system() -> TripleIntelligenceSystem:
    """Get or create the global AI system instance"""
    global _ai_system
    if _ai_system is None:
        _ai_system = TripleIntelligenceSystem()
    return _ai_system


def generate_sport_recommendations(user_input: str, lang: str = "ar") -> Dict[str, Any]:
    """
    Main entry point for generating sport recommendations
    
    Args:
        user_input: User's description of their needs/preferences
        lang: Language code ('ar' or 'en')
    
    Returns:
        Dict with recommendations or error information
    """
    system = get_ai_system()
    return system.run_full_pipeline(user_input, lang)


if __name__ == "__main__":
    # Test the system
    test_input = """أنا شخص يحب التحديات الذهنية ويفضل الهدوء. 
    أبحث عن رياضة تجمع بين التفكير الاستراتيجي والحركة البدنية.
    لا أحب الضجيج ولا الرياضات الجماعية الصاخبة."""
    
    print("🧪 Testing Triple Intelligence System...")
    result = generate_sport_recommendations(test_input, "ar")
    
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
