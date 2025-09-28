cat > tools/make_batch.py <<'PY'
import pathlib, json, math
from tools.generate_video import generate_video

TOPICS = [
  "SportSync identity: Tactical Stealth Flow",
  "Breath & Alignment: range precision",
  "Mind-trap puzzles in motion",
  "Angles & decision timing under pressure",
  "Calm-control line: steady rhythm",
  "Team sync: space reading & passing lanes",
  "VR variant: visual traps & feints",
  "Silent drivers: fast wins, low repetition",
  "Introvert solo mastery: grip & balance",
  "Adrenaline bursts with disciplined exits",
  "Precision & gaze stability for aim sports",
  "Flow without noise: stealth routes",
  "Decision clarity & tempo shifts",
  "Intuitive timing vs technical drilling",
  "Cognitive load: fewer errors, calmer head",
  "Short hooks: identity tease & payoff",
  "Angles over chasing motion",
  "Hidden intent till decisive beat",
  "Calm-adrenaline mixed scenarios",
  "Layer-Z motives in sport identity"
]

def main(mode="smoke"):
    out_root = pathlib.Path("outputs/videos")
    (out_root / "long").mkdir(parents=True, exist_ok=True)
    (out_root / "shorts").mkdir(parents=True, exist_ok=True)

    if mode == "smoke":
        long_count, shorts_per_long = 1, 4
    else:
        long_count, shorts_per_long = 20, 4

    # Longs
    for i in range(long_count):
        topic = TOPICS[i % len(TOPICS)]
        out = out_root / "long" / f"long_{i+1:03d}.mp4"
        print(f"[LONG] {i+1}/{long_count} -> {out}")
        meta = generate_video(topic, "long", str(out))
        # Shorts for this long
        for s in range(shorts_per_long):
            s_topic = f"{topic} — short v{s+1}"
            s_out = out_root / "shorts" / f"short_{i+1:03d}_{s+1:02d}.mp4"
            print(f"   [SHORT] {s+1}/{shorts_per_long} -> {s_out}")
            generate_video(s_topic, "short", str(s_out))

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["smoke","full"], default="smoke")
    args = p.parse_args()
    main(args.mode)
PY
