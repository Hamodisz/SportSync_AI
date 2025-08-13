# -- coding: utf-8 --
import argparse, time, os
from typing import List
from core.core_engine import run_full_generation

TOPICS: List[str] = [
    "Start your sport today",
    "Discipline vs motivation",
    "Build momentum daily",
    "Small steps, big change",
    "Train smarter, not harder",
    "Consistency beats perfection",
    "Morning energy routine",
    "First 1km run",
    "Focus over intensity",
    "Strength from routine"
]

TEMPLATE = """Title: {topic}

Scene 1: Visual hook related to "{topic}"
Scene 2: Body motion / close-up detail
Scene 3: Outcome or tiny win
Outro: Call to action to try 10 minutes today
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=4)
    parser.add_argument("--lang", default="en")
    args = parser.parse_args()

    print("🚀 Batch start")
    for i in range(args.count):
        topic = TOPICS[i % len(TOPICS)]
        script = TEMPLATE.format(topic=topic)
        res = run_full_generation(
            user_data={"topic": topic, "traits": {"tone": "motivational"}},
            lang=args.lang,
            image_duration=4,
            override_script=script,
            mute_if_no_voice=True,
            skip_cleanup=True
        )
        print(f"[{i+1}/{args.count}] ▶ {topic} →", res.get("video"), "err:", res.get("error"))
        time.sleep(2)
    print("✅ Batch done")

if _name_ == "_main_":
    main()
