from agents.marketing.content_creator import generate_content

user_data = """
- أذوب في التحديات الذهنية أكثر من الجسدية.
- أتضايق من القيود، وأحب أتعلم بطريقتي.
- أحب أقارن نفسي بنسختي السابقة، مو بالناس.
- ما أحب التكرار وأحب أتعلم شي عميق.
"""

results = generate_content(user_data, lang="ar")

for i, post in enumerate(results, 1):
    print(f"\n📌 منشور رقم {i}:\n{post}\n")
