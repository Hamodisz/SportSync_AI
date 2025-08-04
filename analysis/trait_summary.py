import json

def summarize_traits(traits: list) -> list:
    if not traits:
        return []

    summarized = []
    for t in traits:
        if isinstance(t, str):
            summarized.append(t.strip())
        elif isinstance(t, dict):
            summarized.append(json.dumps(t, ensure_ascii=False))
    return summarized
