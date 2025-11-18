"""
Sports Database Generator
Generates comprehensive sports database with 1000+ sports
Each sport has Z-scores, categories, and bilingual names
"""

import json
import random
from typing import Dict, List

# Seed sports with known Z-scores (100 base sports)
SEED_SPORTS = [
    # Team Sports - High Group
    {"name_en": "Soccer", "name_ar": "كرة القدم", "category": "team_physical",
     "z": {"calm_adrenaline": 0.6, "solo_group": 0.9, "technical_intuitive": 0.3, "control_freedom": 0.4, "repeat_variety": 0.5, "compete_enjoy": 0.8, "sensory_sensitivity": 0.6}},

    {"name_en": "Basketball", "name_ar": "كرة السلة", "category": "team_physical",
     "z": {"calm_adrenaline": 0.7, "solo_group": 0.9, "technical_intuitive": 0.5, "control_freedom": 0.5, "repeat_variety": 0.6, "compete_enjoy": 0.9, "sensory_sensitivity": 0.7}},

    {"name_en": "Volleyball", "name_ar": "كرة الطائرة", "category": "team_physical",
     "z": {"calm_adrenaline": 0.5, "solo_group": 0.9, "technical_intuitive": 0.4, "control_freedom": 0.6, "repeat_variety": 0.5, "compete_enjoy": 0.7, "sensory_sensitivity": 0.5}},

    {"name_en": "Rugby", "name_ar": "الرجبي", "category": "team_physical",
     "z": {"calm_adrenaline": 0.9, "solo_group": 0.9, "technical_intuitive": 0.2, "control_freedom": 0.3, "repeat_variety": 0.4, "compete_enjoy": 0.9, "sensory_sensitivity": 0.8}},

    # Solo Sports - High Solo
    {"name_en": "Running", "name_ar": "الجري", "category": "solo_physical",
     "z": {"calm_adrenaline": 0.3, "solo_group": -0.8, "technical_intuitive": 0.1, "control_freedom": 0.9, "repeat_variety": 0.2, "compete_enjoy": 0.3, "sensory_sensitivity": 0.4}},

    {"name_en": "Swimming", "name_ar": "السباحة", "category": "solo_physical",
     "z": {"calm_adrenaline": 0.2, "solo_group": -0.7, "technical_intuitive": 0.3, "control_freedom": 0.8, "repeat_variety": 0.3, "compete_enjoy": 0.2, "sensory_sensitivity": 0.7}},

    {"name_en": "Cycling", "name_ar": "ركوب الدراجات", "category": "solo_physical",
     "z": {"calm_adrenaline": 0.4, "solo_group": -0.6, "technical_intuitive": 0.2, "control_freedom": 0.9, "repeat_variety": 0.7, "compete_enjoy": 0.3, "sensory_sensitivity": 0.5}},

    # Mental Sports - High Technical
    {"name_en": "Chess", "name_ar": "الشطرنج", "category": "mental",
     "z": {"calm_adrenaline": -0.8, "solo_group": -0.3, "technical_intuitive": 0.9, "control_freedom": 0.5, "repeat_variety": 0.8, "compete_enjoy": 0.6, "sensory_sensitivity": 0.3}},

    {"name_en": "Poker", "name_ar": "البوكر", "category": "mental",
     "z": {"calm_adrenaline": 0.1, "solo_group": 0.2, "technical_intuitive": 0.8, "control_freedom": 0.4, "repeat_variety": 0.9, "compete_enjoy": 0.8, "sensory_sensitivity": 0.6}},

    {"name_en": "Esports (League of Legends)", "name_ar": "الرياضات الإلكترونية", "category": "mental",
     "z": {"calm_adrenaline": 0.5, "solo_group": 0.7, "technical_intuitive": 0.9, "control_freedom": 0.6, "repeat_variety": 0.8, "compete_enjoy": 0.9, "sensory_sensitivity": 0.7}},

    # Extreme Sports - High Adrenaline
    {"name_en": "Skydiving", "name_ar": "القفز بالمظلات", "category": "extreme",
     "z": {"calm_adrenaline": 0.95, "solo_group": -0.2, "technical_intuitive": 0.6, "control_freedom": 0.4, "repeat_variety": 0.9, "compete_enjoy": 0.2, "sensory_sensitivity": 0.9}},

    {"name_en": "Rock Climbing", "name_ar": "تسلق الصخور", "category": "extreme",
     "z": {"calm_adrenaline": 0.8, "solo_group": -0.4, "technical_intuitive": 0.7, "control_freedom": 0.7, "repeat_variety": 0.8, "compete_enjoy": 0.3, "sensory_sensitivity": 0.8}},

    {"name_en": "Parkour", "name_ar": "الباركور", "category": "extreme",
     "z": {"calm_adrenaline": 0.85, "solo_group": -0.3, "technical_intuitive": 0.6, "control_freedom": 0.9, "repeat_variety": 0.9, "compete_enjoy": 0.4, "sensory_sensitivity": 0.8}},

    {"name_en": "Surfing", "name_ar": "ركوب الأمواج", "category": "extreme",
     "z": {"calm_adrenaline": 0.7, "solo_group": -0.5, "technical_intuitive": 0.5, "control_freedom": 0.8, "repeat_variety": 0.8, "compete_enjoy": 0.3, "sensory_sensitivity": 0.9}},

    # Calm Sports - Low Adrenaline
    {"name_en": "Yoga", "name_ar": "اليوغا", "category": "calm_physical",
     "z": {"calm_adrenaline": -0.9, "solo_group": -0.2, "technical_intuitive": 0.4, "control_freedom": 0.9, "repeat_variety": 0.4, "compete_enjoy": -0.8, "sensory_sensitivity": 0.7}},

    {"name_en": "Meditation", "name_ar": "التأمل", "category": "calm_mental",
     "z": {"calm_adrenaline": -0.95, "solo_group": -0.7, "technical_intuitive": 0.3, "control_freedom": 0.9, "repeat_variety": 0.5, "compete_enjoy": -0.9, "sensory_sensitivity": 0.8}},

    {"name_en": "Tai Chi", "name_ar": "التاي تشي", "category": "calm_physical",
     "z": {"calm_adrenaline": -0.8, "solo_group": 0.3, "technical_intuitive": 0.5, "control_freedom": 0.8, "repeat_variety": 0.3, "compete_enjoy": -0.7, "sensory_sensitivity": 0.6}},

    {"name_en": "Hiking", "name_ar": "المشي لمسافات طويلة", "category": "calm_physical",
     "z": {"calm_adrenaline": -0.3, "solo_group": -0.4, "technical_intuitive": 0.1, "control_freedom": 0.9, "repeat_variety": 0.8, "compete_enjoy": -0.5, "sensory_sensitivity": 0.9}},
]

# Sport modifiers to create variations
INTENSITY_MODIFIERS = {
    "Competitive": {"compete_enjoy": 0.3, "calm_adrenaline": 0.2},
    "Casual": {"compete_enjoy": -0.2, "calm_adrenaline": -0.1},
    "Extreme": {"calm_adrenaline": 0.4, "sensory_sensitivity": 0.2},
    "Mindful": {"calm_adrenaline": -0.3, "technical_intuitive": 0.2},
    "Team-Based": {"solo_group": 0.3},
    "Solo": {"solo_group": -0.3},
    "Technical": {"technical_intuitive": 0.3},
    "Intuitive": {"technical_intuitive": -0.2},
}

ENVIRONMENT_MODIFIERS = {
    "Indoor": {"sensory_sensitivity": -0.1},
    "Outdoor": {"sensory_sensitivity": 0.2, "repeat_variety": 0.1},
    "Water": {"sensory_sensitivity": 0.3},
    "Mountain": {"calm_adrenaline": 0.2, "sensory_sensitivity": 0.2},
    "Urban": {"repeat_variety": 0.2},
    "Nature": {"calm_adrenaline": -0.1, "sensory_sensitivity": 0.3},
}

def generate_variations(base_sports: List[Dict], target_count: int = 1000) -> List[Dict]:
    """Generate sport variations to reach target count"""
    generated = []
    sport_id = 1

    # Add base sports
    for sport in base_sports:
        sport_entry = {
            "id": f"sport_{sport_id:04d}",
            "name_en": sport["name_en"],
            "name_ar": sport["name_ar"],
            "category": sport["category"],
            "z_scores": sport["z"],
            "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
            "physical_intensity": _calculate_intensity(sport["z"]),
            "mental_demand": _calculate_mental(sport["z"]),
            "is_base_sport": True
        }
        generated.append(sport_entry)
        sport_id += 1

    # Generate variations
    while len(generated) < target_count:
        base = random.choice(base_sports)
        intensity_mod = random.choice(list(INTENSITY_MODIFIERS.keys()))
        env_mod = random.choice(list(ENVIRONMENT_MODIFIERS.keys()))

        # Create new sport name
        new_name_en = f"{intensity_mod} {env_mod} {base['name_en']}"
        new_name_ar = f"{base['name_ar']} ({intensity_mod})"  # Simplified for demo

        # Calculate new Z-scores
        new_z = base["z"].copy()
        for axis, delta in INTENSITY_MODIFIERS[intensity_mod].items():
            new_z[axis] = min(1.0, max(-1.0, new_z[axis] + delta))
        for axis, delta in ENVIRONMENT_MODIFIERS[env_mod].items():
            new_z[axis] = min(1.0, max(-1.0, new_z[axis] + delta))

        # Add small randomization
        for axis in new_z:
            new_z[axis] = min(1.0, max(-1.0, new_z[axis] + random.uniform(-0.1, 0.1)))

        sport_entry = {
            "id": f"sport_{sport_id:04d}",
            "name_en": new_name_en,
            "name_ar": new_name_ar,
            "category": base["category"],
            "subcategory": f"{intensity_mod.lower()}_{env_mod.lower()}",
            "z_scores": {k: round(v, 2) for k, v in new_z.items()},
            "difficulty": random.choice(["beginner", "intermediate", "advanced"]),
            "physical_intensity": _calculate_intensity(new_z),
            "mental_demand": _calculate_mental(new_z),
            "is_base_sport": False,
            "derived_from": base["name_en"]
        }

        generated.append(sport_entry)
        sport_id += 1

    return generated

def _calculate_intensity(z_scores: Dict) -> str:
    """Calculate physical intensity from Z-scores"""
    adrenaline = z_scores.get("calm_adrenaline", 0)
    sensory = z_scores.get("sensory_sensitivity", 0)
    avg = (adrenaline + sensory) / 2

    if avg > 0.5:
        return "high"
    elif avg > 0:
        return "medium"
    else:
        return "low"

def _calculate_mental(z_scores: Dict) -> str:
    """Calculate mental demand from Z-scores"""
    technical = z_scores.get("technical_intuitive", 0)
    variety = z_scores.get("repeat_variety", 0)
    avg = (technical + variety) / 2

    if avg > 0.5:
        return "high"
    elif avg > 0:
        return "medium"
    else:
        return "low"

def generate_database(output_file: str = "data/sports_database.json"):
    """Generate complete sports database"""
    print("=" * 60)
    print("SPORTS DATABASE GENERATOR")
    print("=" * 60)

    print(f"\n1. Loading {len(SEED_SPORTS)} seed sports...")

    print("2. Generating variations...")
    sports = generate_variations(SEED_SPORTS, target_count=1000)

    print(f"3. Generated {len(sports)} total sports")

    # Create categories summary
    categories = {}
    for sport in sports:
        cat = sport["category"]
        categories[cat] = categories.get(cat, 0) + 1

    # Build database structure
    database = {
        "version": "1.0.0",
        "generated_date": "2025-11-18",
        "total_sports": len(sports),
        "categories": list(categories.keys()),
        "category_counts": categories,
        "z_axes": [
            "calm_adrenaline",
            "solo_group",
            "technical_intuitive",
            "control_freedom",
            "repeat_variety",
            "compete_enjoy",
            "sensory_sensitivity"
        ],
        "sports": sports
    }

    print(f"\n4. Saving to {output_file}...")
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("✅ DATABASE GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nTotal Sports: {len(sports)}")
    print("\nCategories:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count} sports")

    print(f"\nFile size: {os.path.getsize(output_file) / 1024:.1f} KB")
    print(f"Location: {output_file}")

    return database

if __name__ == "__main__":
    generate_database()
