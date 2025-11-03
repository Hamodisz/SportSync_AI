# 🎬 Batch Video Production System

## Quick Start

### Generate 100 Videos Automatically

```bash
# Test run (5 shorts + 2 long)
python3 content_studio/batch_generator.py

# Full production (80 shorts + 20 long)
python3 << 'EOF'
from content_studio.batch_generator import BatchVideoGenerator
gen = BatchVideoGenerator()
gen.run_full_batch()  # No limits = generate all
EOF
```

## System Overview

```
content_studio/
├── batch_generator.py           # Main production engine
├── batch_production_engine.py   # Templates & planning
└── batch_templates.py           # Detailed templates (optional)

outputs/batch_videos/
├── shorts/                      # 80 short scripts (30-60s)
└── long/                        # 20 long scripts (15-30min)
```

## Templates

### Shorts (80 videos)
- **Quick Tips** (20): Sport psychology insights
- **Success Stories** (20): AI transformation stories
- **Comparisons** (20): VR vs Real comparisons
- **Challenges** (20): Interactive 60-second tests

### Long Videos (20 videos)
- **Tutorials** (10): Complete guides (20 min)
- **Case Studies** (5): Deep dives (25 min)
- **Technical** (5): Advanced topics (30 min)

## Production Stats

**Test Run Results:**
- Scripts Generated: 7 (5 shorts + 2 long)
- Time Taken: 1 minute
- Success Rate: 100%
- API Cost: ~$0.05

**Full Production Estimates:**
- Total Scripts: 100
- Estimated Time: 2-3 hours
- Estimated Cost: $3-5 (OpenRouter API)

## Custom Production

```python
from content_studio.batch_generator import BatchVideoGenerator

# Custom limits
gen = BatchVideoGenerator()
gen.run_full_batch(shorts_limit=10, long_limit=2)

# Or generate only shorts
gen.generate_all_shorts(limit=20)

# Or only long videos
gen.generate_all_long(limit=5)
```

## Output Format

Each generated script includes:
- Title
- Scene-by-scene breakdown
- Visual descriptions
- Narrator voiceover text
- Emotional tone
- Ready for video production

## Next Steps

After script generation:
1. Review scripts in `outputs/batch_videos/`
2. Run voiceover generation (gTTS or ElevenLabs)
3. Generate images (RunPod or Stock)
4. Composite videos (MoviePy)
5. Upload to YouTube

## Requirements

- Python 3.9+
- OpenRouter API key (or OpenAI)
- See `requirements.txt` for packages
