# -*- coding: utf-8 -*-
"""
Main Batch Generator - SportSync AI
Produces 100 videos automatically
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

# Import our modules
import sys
sys.path.insert(0, '.')

from content_studio.generate_script.script_generator import generate_script
from content_studio.batch_production_engine import generate_batch_plan

class BatchVideoGenerator:
    def __init__(self, output_dir="outputs/batch_videos"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.plan = None
        self.stats = {
            "shorts_generated": 0,
            "long_generated": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def load_plan(self):
        """Load or create batch plan"""
        plan_path = Path("data/batch_plan.json")
        if plan_path.exists():
            with open(plan_path, "r", encoding="utf-8") as f:
                self.plan = json.load(f)
            print(f"✅ Loaded existing plan: {len(self.plan['shorts']) + len(self.plan['long'])} videos")
        else:
            self.plan = generate_batch_plan()
            print(f"✅ Created new plan")
        return self.plan
    
    def generate_short_script(self, video_info: Dict) -> str:
        """Generate script for short video (30-60 sec)"""
        prompt = f"""Create a SHORT video script (30-60 seconds) about:
{video_info['topic']}

Format: 3-5 quick scenes, each 1-2 lines.
Style: Engaging, emotional, visual.
Target: YouTube Shorts/TikTok audience.
"""
        try:
            script = generate_script(video_info['topic'], tone="emotional", lang="english")
            return script
        except Exception as e:
            print(f"❌ Error generating short script: {e}")
            self.stats["errors"] += 1
            return f"Error: {e}"
    
    def generate_long_script(self, video_info: Dict) -> str:
        """Generate script for long video (15-30 min)"""
        prompt = f"""Create a COMPLETE video script (15-20 minutes) about:
{video_info['topic']}

Structure:
- Hook (0-15 sec): Shocking opener
- Intro (15-120 sec): What viewer will learn
- Problem (2-7 min): Why this matters
- Solution (7-17 min): How AI solves it
- Proof (17-25 min): Results & testimonials
- CTA (25-30 min): Call to action

Make it educational, engaging, and visually descriptive.
"""
        try:
            script = generate_script(video_info['topic'], tone="educational", lang="english")
            return script
        except Exception as e:
            print(f"❌ Error generating long script: {e}")
            self.stats["errors"] += 1
            return f"Error: {e}"
    
    def generate_all_shorts(self, limit=None):
        """Generate all short videos"""
        shorts = self.plan['shorts'][:limit] if limit else self.plan['shorts']
        
        print(f"\n🎬 Generating {len(shorts)} SHORT videos...")
        print("="*70)
        
        for i, video in enumerate(shorts, 1):
            print(f"\n[{i}/{len(shorts)}] {video['topic']}")
            
            # Generate script
            script = self.generate_short_script(video)
            
            # Save script
            script_file = self.output_dir / f"shorts/{video['id']}_script.txt"
            script_file.parent.mkdir(parents=True, exist_ok=True)
            script_file.write_text(script, encoding="utf-8")
            
            # Update stats
            self.stats["shorts_generated"] += 1
            video["status"] = "script_ready"
            
            print(f"✅ Script saved: {script_file.name}")
            
            # Rate limiting (avoid API overload)
            if i % 10 == 0:
                print("⏸️  Cooling down 5 seconds...")
                time.sleep(5)
        
        print(f"\n✅ Generated {self.stats['shorts_generated']} short scripts!")
    
    def generate_all_long(self, limit=None):
        """Generate all long videos"""
        long_videos = self.plan['long'][:limit] if limit else self.plan['long']
        
        print(f"\n🎥 Generating {len(long_videos)} LONG videos...")
        print("="*70)
        
        for i, video in enumerate(long_videos, 1):
            print(f"\n[{i}/{len(long_videos)}] {video['topic']}")
            
            # Generate script
            script = self.generate_long_script(video)
            
            # Save script
            script_file = self.output_dir / f"long/{video['id']}_script.txt"
            script_file.parent.mkdir(parents=True, exist_ok=True)
            script_file.write_text(script, encoding="utf-8")
            
            # Update stats
            self.stats["long_generated"] += 1
            video["status"] = "script_ready"
            
            print(f"✅ Script saved: {script_file.name}")
            
            # Rate limiting
            if i % 5 == 0:
                print("⏸️  Cooling down 10 seconds...")
                time.sleep(10)
        
        print(f"\n✅ Generated {self.stats['long_generated']} long scripts!")
    
    def run_full_batch(self, shorts_limit=None, long_limit=None):
        """Run complete batch generation"""
        self.stats["start_time"] = time.time()
        
        print("\n" + "="*70)
        print("🚀 STARTING BATCH PRODUCTION")
        print("="*70)
        
        # Load plan
        self.load_plan()
        
        # Generate shorts
        self.generate_all_shorts(limit=shorts_limit)
        
        # Generate long videos
        self.generate_all_long(limit=long_limit)
        
        # Final stats
        self.stats["end_time"] = time.time()
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        print("\n" + "="*70)
        print("📊 BATCH PRODUCTION COMPLETE")
        print("="*70)
        print(f"✅ Shorts Generated: {self.stats['shorts_generated']}")
        print(f"✅ Long Generated: {self.stats['long_generated']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⏱️  Duration: {duration/60:.1f} minutes")
        print(f"📁 Output: {self.output_dir}")
        
        # Save updated plan
        with open("data/batch_plan.json", "w", encoding="utf-8") as f:
            json.dump(self.plan, f, ensure_ascii=False, indent=2)
        print("✅ Plan updated and saved")

if __name__ == "__main__":
    # Example: Generate first 5 shorts and 2 long videos (test run)
    generator = BatchVideoGenerator()
    generator.run_full_batch(shorts_limit=5, long_limit=2)
