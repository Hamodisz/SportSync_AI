cat > tools/deepseek_client.py <<'PY'
import os, requests, json, random

API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
MODEL    = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
API_KEY  = os.getenv("DEEPSEEK_API_KEY")

def _fallback_script(topic: str, n_scenes: int = 12):
    # Minimal offline generator when no API key
    rnd = random.Random(hash(topic) & 0xffffffff)
    scenes = []
    for i in range(n_scenes):
        scenes.append({
            "visual": f"{topic} — abstract athletic composition #{i+1}",
            "line":   f"Silent control • angle #{(i%5)+1}"
        })
    return {
        "title": f"{topic} — SportSync Flow",
        "scenes": scenes
    }

def chat(system_prompt: str, user_prompt: str, temperature=0.7, max_tokens=1200):
    if not API_KEY:
        # Return a fallback JSON string
        data = _fallback_script(topic=user_prompt.strip()[:64], n_scenes=12)
        return json.dumps(data, ensure_ascii=False)

    url = f"{API_BASE.rstrip('/')}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": [
            {"role":"system","content":system_prompt},
            {"role":"user","content":user_prompt}
        ],
        "temperature": float(temperature),
        "max_tokens": int(max_tokens)
    }
    r = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}",
                                    "Content-Type":"application/json"},
                      json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]
PY
