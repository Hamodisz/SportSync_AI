# -*- coding: utf-8 -*-
"""
Batch Production Engine - SportSync AI
Automates production of 100 videos (80 shorts + 20 long)
"""

import os
import json
from typing import List, Dict

# Quick topics library
SHORTS_TOPICS = {
    "tips": [f"Quick Tip #{i+1}: Sport Psychology Insight" for i in range(20)],
    "stories": [f"Success Story #{i+1}: AI Transformation" for i in range(20)],
    "comparisons": [f"VR vs Real #{i+1}: Sport Comparison" for i in range(20)],
    "challenges": [f"60-Second Challenge #{i+1}: Predict Your Sport" for i in range(20)]
}

LONG_TOPICS = [
    "How AI Finds Your Perfect Sport - Complete Guide",
    "The Science Behind Sport-Personality Matching",
    "Why 90% Choose Wrong Sport (AI Solution)",
    "SportSync Algorithm Deep Dive",
    "The Future of Personalized Sport Recommendations",
    "From Couch to Champion with AI",
    "Layer-Z: The Silent Engine Explained",
    "Sport Identity Psychology Full Analysis",
    "Machine Learning in Sports Science",
    "VR Sports Revolution Complete Guide",
    "Case Study: Gamer to Combat Athlete",
    "Case Study: Burnout to Champion Journey",
    "Case Study: Introvert Archery Master",
    "Case Study: Mid-Life Sport Discovery",
    "Case Study: ADHD Athlete Success Story",
    "Technical: 141 Analysis Layers Breakdown",
    "Technical: Neural Networks in Sport Prediction",
    "Technical: AI Evolution in Sports Science",
    "Technical: Personality Psychology + ML",
    "Technical: Future of AI Sports Technology"
]

def generate_batch_plan():
    """Generate complete production plan"""
    plan = {
        "shorts": [],
        "long": []
    }
    
    # Shorts (80 videos)
    for category, topics in SHORTS_TOPICS.items():
        for i, topic in enumerate(topics):
            plan["shorts"].append({
                "id": f"short_{category}_{i+1:02d}",
                "type": "short",
                "category": category,
                "topic": topic,
                "duration": 30 if category == "tips" else 45 if category == "stories" else 30,
                "status": "pending"
            })
    
    # Long videos (20 videos)
    for i, topic in enumerate(LONG_TOPICS):
        video_type = "tutorial" if i < 10 else "case_study" if i < 15 else "deep_dive"
        plan["long"].append({
            "id": f"long_{i+1:02d}",
            "type": "long",
            "category": video_type,
            "topic": topic,
            "duration": 1200,  # 20 minutes
            "status": "pending"
        })
    
    # Save plan
    os.makedirs("data", exist_ok=True)
    with open("data/batch_plan.json", "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Batch plan created: {len(plan['shorts'])} shorts + {len(plan['long'])} long")
    return plan

if __name__ == "__main__":
    plan = generate_batch_plan()
    print(f"\n📊 Total: {len(plan['shorts']) + len(plan['long'])} videos")
