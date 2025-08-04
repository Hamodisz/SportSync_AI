# content_studio/publish_batch.py

import json
from content_studio.publishing_engine import export_video_package

def load_scripts(path="data/video_scripts.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_all_videos():
    scripts = load_scripts()
    for idx, item in enumerate(scripts, 1):
        topic = item["topic"]
        script = item["script"]
        print(f"\n📹 Generating video {idx}: {topic}")
        export_video_package(script, index=idx)

if _name_ == "_main_":
    generate_all_videos()
