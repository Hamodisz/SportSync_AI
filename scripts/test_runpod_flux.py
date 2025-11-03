#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/test_runpod_flux.py
---------------------------
اختبار سريع لـ RunPod Flux Integration

Usage:
    python scripts/test_runpod_flux.py
    python scripts/test_runpod_flux.py --prompt "your custom prompt"
    python scripts/test_runpod_flux.py --batch  # multiple images
"""

import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# تحميل المتغيرات البيئية من .env
load_dotenv()

# إضافة جذر المشروع للمسار
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.runpod_flux_client import RunPodFluxClient, enhance_prompt_for_sport


def test_single_image(prompt: str, width: int = 1024, height: int = 1024):
    """اختبار توليد صورة واحدة"""
    print("\n" + "=" * 60)
    print("🧪 RunPod Flux - Single Image Test")
    print("=" * 60)

    try:
        # إنشاء العميل
        print("\n📡 Connecting to RunPod...")
        client = RunPodFluxClient()
        print("✅ Client initialized")

        # توليد الصورة
        print(f"\n🎨 Generating image...")
        print(f"   Prompt: {prompt}")
        print(f"   Size: {width}x{height}")

        result = client.generate_image(
            prompt=prompt,
            width=width,
            height=height,
            steps=25,
            cfg_scale=7.5
        )

        # معالجة النتيجة
        if result.get("success"):
            print("\n✅ Success!")
            print(f"   Seed: {result.get('seed', 'N/A')}")

            # حفظ الصورة
            output_dir = Path("outputs/test_runpod")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"test_{result['seed']}.png"

            client.save_image(result["image_b64"], output_path)
            print(f"   Saved to: {output_path}")

            return True
        else:
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_images(count: int = 3):
    """اختبار توليد batch من الصور"""
    print("\n" + "=" * 60)
    print(f"🧪 RunPod Flux - Batch Test ({count} images)")
    print("=" * 60)

    try:
        # بروماتات رياضية متنوعة
        prompts = [
            "A serene morning at a running track, cinematic, professional photography, 8k",
            "Athlete meditating before competition, calm focus, high quality, detailed",
            "Dynamic basketball court scene, motion blur, energetic, cinematic lighting",
            "Gym interior with sunlight streaming through windows, motivational atmosphere",
            "Runner's feet hitting the ground, slow motion effect, athletic, powerful",
        ][:count]

        # إنشاء العميل
        print("\n📡 Connecting to RunPod...")
        client = RunPodFluxClient()
        print("✅ Client initialized")

        # توليد الـ batch
        results = client.generate_batch(
            prompts=prompts,
            width=1024,
            height=1920,  # portrait للـ YouTube Shorts
            steps=20,  # أسرع للاختبار
            delay_between=1.0
        )

        # حفظ النتائج
        output_dir = Path("outputs/test_runpod_batch")
        output_dir.mkdir(parents=True, exist_ok=True)

        success_count = 0
        for i, (result, prompt) in enumerate(zip(results, prompts), 1):
            if result.get("success"):
                output_path = output_dir / f"batch_{i}_{result['seed']}.png"
                client.save_image(result["image_b64"], output_path)
                success_count += 1

        # ملخص
        print("\n" + "=" * 60)
        print(f"📊 Batch Results:")
        print(f"   Success: {success_count}/{count}")
        print(f"   Output: {output_dir}")
        print("=" * 60)

        return success_count == count

    except Exception as e:
        print(f"\n💥 Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_enhancement():
    """اختبار تحسين البرومبت"""
    print("\n" + "=" * 60)
    print("🧪 Prompt Enhancement Test")
    print("=" * 60)

    test_cases = [
        ("A quiet gym in the morning", "en"),
        ("مضمار جري عند الغروب", "ar"),
        ("Basketball court", "en"),
    ]

    for original, lang in test_cases:
        enhanced = enhance_prompt_for_sport(original, lang)
        print(f"\n  Original: {original}")
        print(f"  Enhanced: {enhanced}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Test RunPod Flux Integration")
    parser.add_argument(
        "--prompt",
        default="A serene morning at a running track, professional photography, cinematic, 8k",
        help="Custom prompt for single image test"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1024,
        help="Image width"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=1024,
        help="Image height"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Run batch test (3 images)"
    )
    parser.add_argument(
        "--batch-count",
        type=int,
        default=3,
        help="Number of images in batch test"
    )
    parser.add_argument(
        "--enhancement-only",
        action="store_true",
        help="Test only prompt enhancement (no API calls)"
    )

    args = parser.parse_args()

    # تشغيل الاختبارات
    try:
        if args.enhancement_only:
            success = test_prompt_enhancement()
        elif args.batch:
            success = test_batch_images(count=args.batch_count)
        else:
            success = test_single_image(
                prompt=args.prompt,
                width=args.width,
                height=args.height
            )

        # النتيجة النهائية
        print("\n" + "=" * 60)
        if success:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. Check errors above.")
        print("=" * 60 + "\n")

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
