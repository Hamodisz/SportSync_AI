# smoke_test_backend_gpt.py
from core.backend_gpt import generate_sport_recommendation

answers = {
    "aim": {"answer": "أبغى هدوء وتنفس وتركيز أكثر من الأدرينالين"},
    "style": {"answer": "أفضل فردي وفيه لمسة ألغاز وخداع بصري"},
    "tools": {"answer": "لو في VR كويس لكن مو شرط"},
}

cards = generate_sport_recommendation(answers, lang="العربية")
for i, c in enumerate(cards, 1):
    print(f"\n=== CARD {i} ===\n{c}\n")
