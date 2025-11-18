"""
SportSync AI - Data Storage System
For academic research and system validation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Storage directory
STORAGE_DIR = Path(__file__).parent.parent / "data" / "responses"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def save_response(data: Dict[str, Any]) -> str:
    """
    Save user response for research study
    Returns: filename of saved response
    """
    try:
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"response_{timestamp}.json"
        filepath = STORAGE_DIR / filename

        # Add metadata
        data["saved_at"] = datetime.utcnow().isoformat()
        data["version"] = "1.0"

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filename

    except Exception as e:
        print(f"Storage error: {str(e)}")
        return ""

def load_all_responses() -> List[Dict[str, Any]]:
    """
    Load all saved responses for analysis
    """
    responses = []

    try:
        if not STORAGE_DIR.exists():
            return responses

        for filepath in sorted(STORAGE_DIR.glob("response_*.json")):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    responses.append(data)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                continue

        return responses

    except Exception as e:
        print(f"Load error: {str(e)}")
        return responses

def get_statistics() -> Dict[str, Any]:
    """
    Calculate statistics from all responses
    """
    responses = load_all_responses()

    if not responses:
        return {
            "total_responses": 0,
            "message": "No data yet"
        }

    # Calculate statistics
    total = len(responses)
    languages = {}
    profile_types = {}
    recommended_sports = {}
    has_consent = 0
    has_additional_info = 0

    for resp in responses:
        # Language distribution
        lang = resp.get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1

        # Profile types
        profile = resp.get("analysis_summary", {}).get("profile_type", "unknown")
        profile_types[profile] = profile_types.get(profile, 0) + 1

        # Recommended sports
        for rec in resp.get("recommendations", []):
            sport = rec.get("sport", "unknown")
            recommended_sports[sport] = recommended_sports.get(sport, 0) + 1

        # Consent
        if resp.get("research_consent"):
            has_consent += 1

        # Additional info
        if resp.get("additional_info", "").strip():
            has_additional_info += 1

    return {
        "total_responses": total,
        "consent_rate": f"{(has_consent / total * 100):.1f}%",
        "languages": languages,
        "profile_types": dict(sorted(profile_types.items(), key=lambda x: x[1], reverse=True)),
        "top_sports": dict(sorted(recommended_sports.items(), key=lambda x: x[1], reverse=True)[:10]),
        "additional_info_rate": f"{(has_additional_info / total * 100):.1f}%",
        "date_range": {
            "first": responses[0].get("saved_at", "unknown") if responses else None,
            "last": responses[-1].get("saved_at", "unknown") if responses else None
        }
    }

def export_to_csv() -> str:
    """
    Export responses to CSV format for analysis
    Returns: CSV string
    """
    responses = load_all_responses()

    if not responses:
        return "No data to export"

    # CSV header
    csv_lines = [
        "timestamp,session_id,language,profile_type,sport1,sport2,sport3,"
        "consent,has_additional_info,answers_count"
    ]

    # CSV rows
    for resp in responses:
        recommendations = resp.get("recommendations", [])
        sports = [rec.get("sport", "") for rec in recommendations[:3]]
        while len(sports) < 3:
            sports.append("")

        row = [
            resp.get("saved_at", ""),
            resp.get("session_id", ""),
            resp.get("language", ""),
            resp.get("analysis_summary", {}).get("profile_type", ""),
            sports[0],
            sports[1],
            sports[2],
            "yes" if resp.get("research_consent") else "no",
            "yes" if resp.get("additional_info", "").strip() else "no",
            str(len(resp.get("answers", [])))
        ]

        csv_lines.append(",".join(f'"{item}"' for item in row))

    return "\n".join(csv_lines)
