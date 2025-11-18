"""
COMPREHENSIVE UNIQUENESS TEST
Tests that 3 different personality profiles get 3 COMPLETELY different sports
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.index import generate_unique_sports_with_ai
import json

print("="*80)
print("UNIQUENESS TEST: 3 Different Personalities → 3 Different Sports")
print("="*80)

# Profile 1: Adrenaline Junkie (High energy, solo, freedom-seeking)
profile1_z_scores = {
    "calm_adrenaline": 0.9,      # VERY HIGH adrenaline
    "solo_group": -0.8,           # VERY solo
    "technical_intuitive": 0.3,   # Slightly technical
    "control_freedom": 0.9,       # Maximum freedom
    "repeat_variety": 0.8,        # High variety
    "compete_enjoy": -0.5,        # Enjoys more than competes
    "sensory_sensitivity": 0.9    # High sensory
}

# Profile 2: Team Player Competitor (Moderate energy, group, structured)
profile2_z_scores = {
    "calm_adrenaline": 0.2,       # Low-moderate adrenaline
    "solo_group": 0.9,            # VERY group-oriented
    "technical_intuitive": -0.7,  # Very intuitive
    "control_freedom": -0.6,      # Prefers structure
    "repeat_variety": -0.4,       # Prefers routine
    "compete_enjoy": 0.8,         # Highly competitive
    "sensory_sensitivity": 0.3    # Low-moderate sensory
}

# Profile 3: Zen Individual (Calm, solo, mindful)
profile3_z_scores = {
    "calm_adrenaline": -0.9,      # VERY calm
    "solo_group": -0.7,           # Solo-oriented
    "technical_intuitive": 0.6,   # Technical
    "control_freedom": 0.2,       # Slight freedom preference
    "repeat_variety": -0.5,       # Prefers routine
    "compete_enjoy": -0.8,        # Non-competitive
    "sensory_sensitivity": 0.6    # Moderate-high sensory
}

profiles = [
    ("Adrenaline Junkie", profile1_z_scores),
    ("Team Player Competitor", profile2_z_scores),
    ("Zen Individual", profile3_z_scores)
]

all_sports = []
reasoning_insights = {
    "personality_type": "Test Profile",
    "core_drivers": ["test"],
    "hidden_motivations": ["test"]
}

print("\nTesting 3 different personalities...\n")

for i, (profile_name, z_scores) in enumerate(profiles, 1):
    print(f"\n{'='*80}")
    print(f"PROFILE {i}: {profile_name}")
    print(f"{'='*80}")

    # Show personality scores
    print("\nPersonality Z-Scores:")
    for axis, score in z_scores.items():
        bar = "█" * int(abs(score) * 10)
        direction = "→" if score > 0 else "←"
        print(f"  {axis:20s}: {direction} {bar} ({score:+.1f})")

    print("\nGenerating sports recommendations with web search...")
    print("(This may take 10-20 seconds due to web search)")

    try:
        sports = generate_unique_sports_with_ai(
            z_scores=z_scores,
            lang="en",
            reasoning_insights=reasoning_insights
        )

        print(f"\n✅ Generated {len(sports)} unique sports:")
        for j, sport in enumerate(sports, 1):
            sport_name = sport.get('sport_name', 'Unknown')
            match_score = sport.get('match_percentage', 0)
            print(f"  {j}. {sport_name} ({match_score}% match)")
            all_sports.append(sport_name)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80)
print("UNIQUENESS ANALYSIS")
print("="*80)

print(f"\nTotal sports generated: {len(all_sports)}")
print(f"Unique sports: {len(set(all_sports))}")
print(f"Duplicate sports: {len(all_sports) - len(set(all_sports))}")

print("\nAll recommended sports:")
for i, sport in enumerate(all_sports, 1):
    print(f"  {i}. {sport}")

# Check for duplicates
from collections import Counter
sport_counts = Counter(all_sports)
duplicates = {sport: count for sport, count in sport_counts.items() if count > 1}

if duplicates:
    print("\n⚠️  WARNING: Found duplicate sports:")
    for sport, count in duplicates.items():
        print(f"  - {sport} appeared {count} times")
else:
    print("\n✅ SUCCESS: All sports are unique!")

# Calculate uniqueness percentage
uniqueness_percentage = (len(set(all_sports)) / len(all_sports)) * 100 if all_sports else 0
print(f"\nUniqueness Score: {uniqueness_percentage:.1f}%")

if uniqueness_percentage >= 90:
    print("✅ EXCELLENT: System generates highly unique recommendations")
elif uniqueness_percentage >= 70:
    print("✓ GOOD: System generates mostly unique recommendations")
elif uniqueness_percentage >= 50:
    print("⚠️  FAIR: System has some duplicate recommendations")
else:
    print("❌ POOR: System generates too many duplicate recommendations")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
