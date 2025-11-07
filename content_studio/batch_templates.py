# -*- coding: utf-8 -*-
"""
Batch Templates System for SportSync AI
Generates 100 videos (20 long + 80 shorts) automatically
"""

import os
import json
from typing import List, Dict
from pathlib import Path

# ============================================
# SHORTS TEMPLATES (80 videos, 15-60 seconds)
# ============================================

SHORTS_TEMPLATES = {
    "tip": {
        "name": "Quick Tip",
        "duration": 30,
        "count": 20,
        "structure": {
            "hook": "5 seconds - shocking statement",
            "tip": "15 seconds - actionable advice",
            "cta": "10 seconds - try SportSync"
        },
        "topics": [
            "Why your personality predicts your sport better than fitness",
            "The #1 mistake people make choosing a sport",
            "How to know if a sport is right for you in 60 seconds",
            "The hidden factor in sport success nobody talks about",
            "Why quitting a sport doesn't mean you're weak",
            "The psychology behind sport addiction",
            "How VR is revolutionizing sport training",
            "Why team sports aren't for everyone (and that's OK)",
            "The science of finding your sport identity",
            "How AI reads your personality in 3 questions",
            "Why calm people excel at tactical sports",
            "The truth about sport motivation",
            "How to turn boredom into your sport superpower",
            "Why gamers make great tactical athletes",
            "The sport trait you didn't know you had",
            "How to match sport to your energy level",
            "Why traditional sport advice fails 90% of people",
            "The one question that reveals your sport type",
            "How your childhood affects your sport choice",
            "The future of personalized sport matching"
        ]
    },
    
    "story": {
        "name": "Success Story",
        "duration": 45,
        "count": 20,
        "structure": {
            "problem": "10 seconds - person struggling",
            "discovery": "15 seconds - found right sport via AI",
            "transformation": "15 seconds - life changed",
            "cta": "5 seconds - your turn"
        },
        "scenarios": [
            "From couch potato to rock climber",
            "Gamer discovers tactical combat sports",
            "Shy person finds flow in solo sports",
            "ADHD warrior thrives in fast-paced sports",
            "Introvert masters archery precision",
            "Ex-athlete finds new identity in VR sports",
            "Burnout survivor heals through mindful movement",
            "Overthinker excels at strategy sports",
            "Adrenaline junkie finds calm in climbing",
            "Perfectionist discovers dance therapy",
            "Tech nerd becomes esports athlete",
            "Artist finds expression in parkour",
            "Analyst masters chess boxing",
            "Empath thrives in team coordination sports",
            "Night owl discovers late-night swimming",
            "Planner succeeds in tactical team sports",
            "Creative mind flows in improvisation sports",
            "Logical thinker dominates strategy games",
            "Sensitive soul heals through yoga combat",
            "Rebel finds freedom in extreme sports"
        ]
    }
}

# ============================================
# LONG VIDEO TEMPLATES (20 videos, 3-5 minutes)
# ============================================

LONG_TEMPLATES = {
    "deep_dive": {
        "name": "Deep Dive Analysis",
        "duration": 240,
        "count": 10,
        "structure": {
            "intro": "30 seconds - hook",
            "problem": "60 seconds - common struggles",
            "solution": "90 seconds - AI analysis",
            "proof": "45 seconds - success story",
            "cta": "15 seconds - call to action"
        }
    },
    "tutorial": {
        "name": "How-To Guide",
        "duration": 180,
        "count": 10,
        "structure": {
            "intro": "20 seconds - what you'll learn",
            "steps": "120 seconds - step by step",
            "tips": "30 seconds - pro tips",
            "cta": "10 seconds - try it now"
        }
    }
}


def get_all_templates() -> Dict:
    """Return all available templates"""
    return {
        "shorts": SHORTS_TEMPLATES,
        "long": LONG_TEMPLATES
    }


def get_template_by_type(template_type: str, category: str = None) -> Dict:
    """Get specific template by type and optional category"""
    all_templates = get_all_templates()
    
    if template_type == "shorts":
        if category and category in SHORTS_TEMPLATES:
            return SHORTS_TEMPLATES[category]
        return SHORTS_TEMPLATES
    elif template_type == "long":
        if category and category in LONG_TEMPLATES:
            return LONG_TEMPLATES[category]
        return LONG_TEMPLATES
    
    return {}


def calculate_total_videos() -> Dict[str, int]:
    """Calculate total number of videos per category"""
    shorts_count = sum(t["count"] for t in SHORTS_TEMPLATES.values())
    long_count = sum(t["count"] for t in LONG_TEMPLATES.values())
    
    return {
        "shorts": shorts_count,
        "long": long_count,
        "total": shorts_count + long_count
    }


if __name__ == "__main__":
    stats = calculate_total_videos()
    print(f"📊 Template Statistics:")
    print(f"   Shorts: {stats['shorts']} videos")
    print(f"   Long: {stats['long']} videos")
    print(f"   Total: {stats['total']} videos")
