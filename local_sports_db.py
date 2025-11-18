"""
Local Sports Database
Offline fallback for sports recommendations
Uses Z-score matching to find best sports from local database
"""

import json
import os
from typing import Dict, List
import math

class LocalSportsDatabase:
    """Local sports database for offline recommendations"""

    def __init__(self, db_path: str = "data/sports_database.json"):
        self.db_path = db_path
        self.database = None
        self.load_database()

    def load_database(self):
        """Load sports database from file"""
        try:
            if os.path.exists(self.db_path):
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    self.database = json.load(f)
                print(f"✓ Loaded {self.database['total_sports']} sports from local database")
            else:
                print(f"⚠️  Database not found at {self.db_path}")
                self.database = None
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            self.database = None

    def calculate_z_score_distance(self, z1: Dict[str, float], z2: Dict[str, float]) -> float:
        """
        Calculate Euclidean distance between two Z-score profiles
        Lower distance = better match
        """
        distance = 0.0
        for axis in z1:
            if axis in z2:
                distance += (z1[axis] - z2[axis]) ** 2
        return math.sqrt(distance)

    def find_best_matches(
        self,
        user_z_scores: Dict[str, float],
        num_matches: int = 3,
        category_filter: str = None
    ) -> List[Dict]:
        """
        Find best matching sports from local database
        Uses Z-score distance matching
        """
        if not self.database:
            print("⚠️  Database not loaded, cannot find matches")
            return []

        sports = self.database['sports']

        # Filter by category if specified
        if category_filter:
            sports = [s for s in sports if s['category'] == category_filter]

        # Calculate distances for all sports
        sport_distances = []
        for sport in sports:
            distance = self.calculate_z_score_distance(user_z_scores, sport['z_scores'])
            sport_distances.append((sport, distance))

        # Sort by distance (best matches first)
        sport_distances.sort(key=lambda x: x[1])

        # Return top N matches
        best_matches = []
        for sport, distance in sport_distances[:num_matches]:
            match_score = max(0, 100 - (distance * 20))  # Convert distance to match score
            best_matches.append({
                "sport": sport,
                "distance": round(distance, 3),
                "match_score": round(match_score, 1)
            })

        return best_matches

    def generate_recommendations(
        self,
        user_z_scores: Dict[str, float],
        num_recommendations: int = 3,
        lang: str = "ar"
    ) -> List[Dict]:
        """
        Generate sport recommendations using local database
        Offline alternative to web-based recommendations
        """
        print(f"🔍 Searching local database for {num_recommendations} recommendations...")

        matches = self.find_best_matches(user_z_scores, num_matches=num_recommendations * 3)

        if not matches:
            print("❌ No matches found in local database")
            return []

        # Ensure diversity by selecting from different categories
        recommendations = []
        used_categories = set()

        for match in matches:
            sport = match['sport']
            category = sport['category']

            # Try to avoid duplicate categories (unless we need to)
            if category in used_categories and len(recommendations) < num_recommendations:
                continue

            # Build recommendation
            rec = {
                "sport_name": sport['name_ar'] if lang == 'ar' else sport['name_en'],
                "sport_name_en": sport['name_en'],
                "sport_name_ar": sport['name_ar'],
                "category": category,
                "z_scores": sport['z_scores'],
                "match_score": match['match_score'],
                "difficulty": sport.get('difficulty', 'intermediate'),
                "physical_intensity": sport.get('physical_intensity', 'medium'),
                "mental_demand": sport.get('mental_demand', 'medium'),
                "source": "local_database",
                "confidence": "HIGH" if match['match_score'] > 80 else "MEDIUM",
                "is_offline": True
            }

            recommendations.append(rec)
            used_categories.add(category)

            if len(recommendations) >= num_recommendations:
                break

        # If we don't have enough, fill with best remaining matches
        if len(recommendations) < num_recommendations:
            for match in matches:
                sport = match['sport']
                if len(recommendations) >= num_recommendations:
                    break

                # Skip if already added
                if any(r['sport_name_en'] == sport['name_en'] for r in recommendations):
                    continue

                rec = {
                    "sport_name": sport['name_ar'] if lang == 'ar' else sport['name_en'],
                    "sport_name_en": sport['name_en'],
                    "sport_name_ar": sport['name_ar'],
                    "category": sport['category'],
                    "z_scores": sport['z_scores'],
                    "match_score": match['match_score'],
                    "difficulty": sport.get('difficulty', 'intermediate'),
                    "physical_intensity": sport.get('physical_intensity', 'medium'),
                    "mental_demand": sport.get('mental_demand', 'medium'),
                    "source": "local_database",
                    "confidence": "HIGH" if match['match_score'] > 80 else "MEDIUM",
                    "is_offline": True
                }
                recommendations.append(rec)

        print(f"✓ Generated {len(recommendations)} recommendations from local database")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['sport_name_en']} (match: {rec['match_score']}%, {rec['category']})")

        return recommendations

    def get_sports_by_category(self, category: str) -> List[Dict]:
        """Get all sports in a specific category"""
        if not self.database:
            return []
        return [s for s in self.database['sports'] if s['category'] == category]

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        if not self.database:
            return {"error": "Database not loaded"}

        return {
            "total_sports": self.database['total_sports'],
            "categories": self.database['categories'],
            "category_counts": self.database['category_counts'],
            "version": self.database['version']
        }


# Test function
def test_local_db():
    """Test local sports database"""
    print("=" * 60)
    print("LOCAL SPORTS DATABASE TEST")
    print("=" * 60)

    # Initialize database
    db = LocalSportsDatabase()

    if not db.database:
        print("❌ Database not loaded!")
        return

    # Show stats
    stats = db.get_database_stats()
    print(f"\n📊 Database Stats:")
    print(f"  Total Sports: {stats['total_sports']}")
    print(f"  Categories: {len(stats['categories'])}")
    for cat, count in sorted(stats['category_counts'].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {cat}: {count}")

    # Test 1: High adrenaline seeker
    print("\n" + "=" * 60)
    print("TEST 1: High Adrenaline Seeker")
    print("=" * 60)
    z_scores = {
        "calm_adrenaline": 0.9,
        "solo_group": -0.4,
        "technical_intuitive": 0.5,
        "control_freedom": 0.8,
        "repeat_variety": 0.9,
        "compete_enjoy": 0.4,
        "sensory_sensitivity": 0.8
    }
    recommendations = db.generate_recommendations(z_scores, num_recommendations=5, lang="en")
    print(f"\n✓ Got {len(recommendations)} recommendations")

    # Test 2: Calm, mindful person
    print("\n" + "=" * 60)
    print("TEST 2: Calm, Mindful Person")
    print("=" * 60)
    z_scores = {
        "calm_adrenaline": -0.8,
        "solo_group": -0.5,
        "technical_intuitive": 0.3,
        "control_freedom": 0.9,
        "repeat_variety": 0.3,
        "compete_enjoy": -0.7,
        "sensory_sensitivity": 0.7
    }
    recommendations = db.generate_recommendations(z_scores, num_recommendations=5, lang="ar")
    print(f"\n✓ Got {len(recommendations)} recommendations")

    # Test 3: Team player, competitive
    print("\n" + "=" * 60)
    print("TEST 3: Team Player, Competitive")
    print("=" * 60)
    z_scores = {
        "calm_adrenaline": 0.6,
        "solo_group": 0.9,
        "technical_intuitive": 0.4,
        "control_freedom": 0.3,
        "repeat_variety": 0.5,
        "compete_enjoy": 0.9,
        "sensory_sensitivity": 0.6
    }
    recommendations = db.generate_recommendations(z_scores, num_recommendations=5, lang="en")
    print(f"\n✓ Got {len(recommendations)} recommendations")

    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    test_local_db()
