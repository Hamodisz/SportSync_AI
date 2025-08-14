from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from core.core_engine import run_full_generation

DEFAULT_4_SCENES = """Title: Start your sport today

Scene 1: Sunrise over a quiet track - "Every beginning is a step."
Scene 2: Shoes hitting the ground - "Start with one simple move."
Scene 3: A calm smile - "Consistency beats perfection."
Scene 4: Closing scene - "Give it 10 minutes today."
"""


def main() -> int:
    res = run_full_generation(
        user_data={"topic": "sanity", "traits": {"tone": "neutral"}},
        lang="en",
        image_duration=2,
        override_script=DEFAULT_4_SCENES,
        mute_if_no_voice=True,
        skip_cleanup=False,
    )
    vp = res.get("video")
    if vp:
        p = Path(vp).resolve()
        if p.exists() and p.stat().st_size > 0:
            print(str(p))
            return 0
        else:
            print(str(p))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
