# agents/marketing/video_pipeline/orchestrator.py
"""
Orchestrator for turning an insight record -> final video using repo assets.
Uses existing modules if importable, otherwise falls back to calling scripts via subprocess.

Usage:
  python agents/marketing/video_pipeline/orchestrator.py --index 0

Outputs:
  content_studio/ai_video/final_video.mp4 (overwritten)
  tmp/ (metadata, audio files)
"""

import argparse
import json
import logging
import subprocess
from pathlib import Path
import sys
import shlex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# استخدام نفس Python interpreter الحالي (أكثر أماناً من "python" العام)
PYTHON_CMD = sys.executable

# Paths in your repo (use exactly the structure you provided)
ROOT = Path(__file__).resolve().parents[4]  # go from agents/... up to repo root
INSIGHTS_PATH = ROOT / "data" / "insights_log.json"
IMAGES_DIR = ROOT / "content_studio" / "ai_images" / "outputs"
VOICE_SCRIPT = ROOT / "content_studio" / "ai_voice" / "voice_generator.py"
VIDEO_COMPOSER_SCRIPT = ROOT / "content_studio" / "ai_video" / "generate_final_video.py"
VIDEO_COMPOSER_MODULE = "content_studio.ai_video.video_composer"
FINAL_VIDEO_OUT = ROOT / "content_studio" / "ai_video" / "final_video.mp4"
TMP_DIR = ROOT / "tmp"

# helper: run external command and stream logs (FIXED: no shell=True)
def run_cmd(cmd_list, cwd=None, env=None):
    """
    تشغيل أمر خارجي بشكل آمن

    Args:
        cmd_list: قائمة الأمر والمعاملات (List[str]) - آمن من Command Injection
                  مثال: ["python", "script.py", "--arg", "value"]
        cwd: مجلد العمل (اختياري)
        env: متغيرات البيئة (اختياري)

    ⚠️ SECURITY FIX: تم إزالة shell=True لمنع Command Injection
    """
    if isinstance(cmd_list, str):
        # للتوافق الخلفي: حوّل string إلى list بشكل آمن
        cmd_list = shlex.split(cmd_list)

    cmd_display = ' '.join(shlex.quote(str(x)) for x in cmd_list)
    logging.info("Running: %s", cmd_display)

    proc = subprocess.Popen(
        cmd_list,  # list بدون shell=True - آمن!
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for line in proc.stdout:
        print(line, end="")

    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"Command failed ({proc.returncode}): {cmd_display}")

    return proc.returncode

def load_insight(index=0):
    if not INSIGHTS_PATH.exists():
        raise FileNotFoundError(f"Insights file not found: {INSIGHTS_PATH}")
    data = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Insights file is empty or not a list.")
    if index < 0 or index >= len(data):
        raise IndexError("index out of range for insights file.")
    return data[index]

def try_import(module_name, attr=None):
    try:
        mod = __import__(module_name, fromlist=['*'])
        if attr:
            return getattr(mod, attr)
        return mod
    except Exception as e:
        logging.warning("Could not import %s: %s", module_name, e)
        return None

def generate_script_from_repo(insight):
    """
    Try to use repository's script generator:
    - agents.marketing.video_pipeline.script_writer or content_studio/generate_script
    Fallback: build a tiny script locally.
    """
    # 1) try agents implementation
    mod = try_import("agents.marketing.video_pipeline.script_writer")
    if mod and hasattr(mod, "build_script_from_insight"):
        logging.info("Using agents.marketing.video_pipeline.script_writer.build_script_from_insight")
        return mod.build_script_from_insight(insight)

    # 2) try content_studio.generate_script.script_generator
    mod2 = try_import("content_studio.generate_script.script_generator")
    if mod2 and hasattr(mod2, "generate"):
        logging.info("Using content_studio.generate_script.script_generator.generate")
        # assume the function returns dict with keys hook, insight, cta or similar
        return mod2.generate(insight)

    # fallback: simple built-in script
    logging.info("Falling back to built-in prompt engine (simple)")
    hook = insight.get("recommendation", "Discover your sport").split("/")[0]
    insight_text = insight.get("notes", "") + " — توصية: " + insight.get("recommendation", "")
    cta = "تابعنا لمزيد من التوصيات."
    return {"hook": hook, "insight": insight_text, "cta": cta}

def produce_voice(script_text, out_path: Path):
    """
    Try to call the repo's voice generator or fallback to system TTS (pyttsx3).
    Expected voice generator interface:
      content_studio.ai_voice.voice_generator.generate(text, out_path)
    or a CLI at content_studio/ai_voice/voice_generator.py that accepts args.
    """
    # 1) attempt import and call
    vg = try_import("content_studio.ai_voice.voice_generator")
    if vg and hasattr(vg, "generate"):
        logging.info("Using content_studio.ai_voice.voice_generator.generate")
        try:
            # function signature could be generate(text, outpath) or generate_voice(...)
            # try common names
            if vg.generate.__code__.co_argcount >= 2:
                vg.generate(script_text, str(out_path))
            else:
                # try named alternative
                if hasattr(vg, "generate_voice"):
                    vg.generate_voice(script_text, str(out_path))
                else:
                    raise RuntimeError("voice_generator.generate signature unexpected")
            return out_path
        except Exception as e:
            logging.warning("voice generator import failed during call: %s", e)

    # 2) try CLI script
    if VOICE_SCRIPT.exists():
        logging.info("Calling voice script via CLI: %s", VOICE_SCRIPT)
        cmd_list = [PYTHON_CMD, str(VOICE_SCRIPT), "--text", script_text, "--out", str(out_path)]
        run_cmd(cmd_list, cwd=str(ROOT))
        return out_path

    # 3) fallback to local pyttsx3
    try:
        import pyttsx3
        logging.info("Using local pyttsx3 for TTS (fallback)")
        engine = pyttsx3.init()
        engine.save_to_file(script_text, str(out_path))
        engine.runAndWait()
        if out_path.exists():
            return out_path
    except Exception as e:
        logging.warning("Local TTS failed: %s", e)

    logging.error("No TTS method succeeded. Skipping audio.")
    return None

def build_metadata_for_renderer(insight, script, images_rel, audio_rel=None):
    """
    Build tmp/metadata.json compatible with Remotion or your renderer.
    images_rel: list of image paths relative to remotion/ (like ../content_studio/ai_images/outputs/scene_1.png)
    audio_rel: optional path relative to remotion/
    """
    meta = {
        "title": script.get("hook", ""),
        "subtitle": script.get("cta", ""),
        "seconds": float(insight.get("seconds_per_image", 1.2)),
        "fps": 30,
        "images": images_rel,
        "animation": {},   # repo-specific mapping can be left empty or filled by motion_mapper
        "narration_text": script.get("insight", "")
    }
    if audio_rel:
        meta["audio"] = audio_rel
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    meta_path = TMP_DIR / "metadata.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Wrote metadata: %s", meta_path)
    return meta_path

def render_video_with_repo_tools(meta_path):
    """
    Try to use existing composer modules first; if not available, try to call the composer script.
    Prefer modules for speed.
    """
    # 1) try import composer module
    composer = try_import("content_studio.ai_video.video_composer")
    if composer and hasattr(composer, "compose_from_metadata"):
        logging.info("Using content_studio.ai_video.video_composer.compose_from_metadata")
        # assume function signature compose_from_metadata(metadata_path, out_path)
        try:
            composer.compose_from_metadata(str(meta_path), str(FINAL_VIDEO_OUT))
            return FINAL_VIDEO_OUT
        except Exception as e:
            logging.warning("composer.compose_from_metadata failed: %s", e)

    # 2) try CLI script
    if VIDEO_COMPOSER_SCRIPT.exists():
        cmd_list = [PYTHON_CMD, str(VIDEO_COMPOSER_SCRIPT), "--meta", str(meta_path), "--out", str(FINAL_VIDEO_OUT)]
        run_cmd(cmd_list, cwd=str(ROOT))
        return FINAL_VIDEO_OUT

    # 3) fallback: try advanced_video_pipeline if present
    adv = try_import("logic.advanced_video_pipeline")
    if adv and hasattr(adv, "build_video"):
        logging.info("Using logic.advanced_video_pipeline.build_video fallback")
        # read metadata and call build_video with images dir and audio
        m = json.loads(meta_path.read_text(encoding="utf-8"))
        images_dir = IMAGES_DIR
        audio = None
        if m.get("audio"):
            audio = ROOT / m["audio"].lstrip("../")
        adv.build_video(images_dir=images_dir, out_path=FINAL_VIDEO_OUT, seconds_per_image=m.get("seconds",1.2),
                        fps=m.get("fps",30), music_path=audio, title=m.get("title",""), subtitle=m.get("subtitle",""))
        return FINAL_VIDEO_OUT

    raise RuntimeError("No available renderer/composer found in repo.")

def main(index=0):
    logging.info("Starting orchestrator (index=%s)", index)
    insight = load_insight(index)
    logging.info("Loaded insight id: %s topic: %s", insight.get("id","?"), insight.get("topic","?"))

    # 1) generate script (hook/insight/cta)
    script = generate_script_from_repo(insight)
    logging.info("Script generated: hook=%s", script.get("hook","")[:60])

    # 2) prepare images list (relative to remotion - but we will keep them repo-relative too)
    images = sorted(list(IMAGES_DIR.glob("scene_*.png")))
    if not images:
        raise FileNotFoundError(f"No scene images found in {IMAGES_DIR}")
    # remotion expects images like "../content_studio/ai_images/outputs/scene_1.png" from remotion/
    images_rel = [ "../" + str(p.relative_to(ROOT)).replace("\\\\","/") for p in images ]

    # 3) produce voice narration (optional)
    TMP_DIR.mkdir(exist_ok=True)
    audio_out = TMP_DIR / "audio_tts.mp3"
    tts_path = produce_voice(script.get("insight",""), audio_out)
    audio_rel = None
    if tts_path and Path(tts_path).exists():
        # remotion relative path
        audio_rel = "../" + str(Path(tts_path).relative_to(ROOT)).replace("\\\\","/")
        logging.info("TTS audio available at %s", audio_rel)
    else:
        logging.info("No TTS audio produced; continuing without narration")

    # 4) build metadata
    meta_path = build_metadata_for_renderer(insight, script, images_rel, audio_rel=audio_rel)

    # 5) render using repo tools
    out_video = render_video_with_repo_tools(meta_path)
    logging.info("Final video produced: %s", out_video)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--index", type=int, default=0, help="Index into data/insights_log.json")
    args = p.parse_args()
    main(index=args.index)
