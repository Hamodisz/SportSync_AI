# -*- coding: utf-8 -*-
"""
core/runpod_flux_client.py
--------------------------
عميل متقدم لـ RunPod مع Flux/ComfyUI

الميزات:
- توليد صور من نصوص (text2img)
- Batch generation
- Error recovery
- Progress tracking
- Workflow builder لـ ComfyUI

الاستخدام:
    from core.runpod_flux_client import RunPodFluxClient

    client = RunPodFluxClient()
    result = client.generate_image(
        prompt="A serene morning at a running track, cinematic, 8k",
        width=1024,
        height=1920
    )
"""

import os
import json
import time
import base64
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests

class RunPodFluxClient:
    """
    عميل RunPod لتوليد الصور عبر ComfyUI/Flux
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        timeout: int = 300
    ):
        """
        تهيئة العميل

        Args:
            api_key: RunPod API key (يقرأ من RUNPOD_API_KEY إن لم يُمرر)
            endpoint_id: ComfyUI endpoint ID (يقرأ من RUNPOD_COMFY_ENDPOINT_ID)
            timeout: المهلة الافتراضية بالثواني
        """
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = endpoint_id or os.getenv("RUNPOD_COMFY_ENDPOINT_ID")
        self.timeout = timeout

        if not self.api_key:
            raise RuntimeError(
                "❌ RUNPOD_API_KEY غير موجود. "
                "اضبطه في .env أو مرره كمعامل."
            )

        if not self.endpoint_id:
            raise RuntimeError(
                "❌ RUNPOD_COMFY_ENDPOINT_ID غير موجود. "
                "اضبطه في .env أو مرره كمعامل."
            )

        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "blurry, low quality, watermark, text, signature",
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        cfg_scale: float = 7.5,
        seed: Optional[int] = None,
        model: str = "flux_dev.safetensors",
        sampler: str = "euler",
        scheduler: str = "normal"
    ) -> Dict:
        """
        توليد صورة واحدة

        Args:
            prompt: النص الوصفي للصورة
            negative_prompt: ما تريد تجنبه
            width: العرض بالبكسل
            height: الارتفاع بالبكسل
            steps: عدد خطوات التوليد (أكثر = أفضل + أبطأ)
            cfg_scale: مدى الالتزام بالـ prompt (1-20)
            seed: seed للتكرار (اختياري)
            model: اسم الموديل في ComfyUI
            sampler: نوع الـ sampler
            scheduler: نوع الـ scheduler

        Returns:
            {
                "success": True/False,
                "image_b64": "..." (base64 encoded),
                "seed": 12345,
                "error": "..." (في حال الفشل)
            }
        """
        try:
            # بناء الـ workflow
            workflow = self._build_flux_workflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg_scale=cfg_scale,
                seed=seed,
                model=model,
                sampler=sampler,
                scheduler=scheduler
            )

            # إرسال الطلب
            payload = {"input": {"workflow": workflow}}

            print(f"📤 Sending request to RunPod...")
            print(f"   Prompt: {prompt[:60]}...")
            print(f"   Size: {width}x{height}, Steps: {steps}")

            response = requests.post(
                f"{self.base_url}/runsync",
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # معالجة النتيجة
            if result.get("status") == "COMPLETED":
                output = result.get("output", {})

                # استخراج الصورة (قد تكون في مسارات مختلفة)
                image_data = None
                if isinstance(output, dict):
                    image_data = output.get("image") or output.get("images", [None])[0]
                elif isinstance(output, list) and len(output) > 0:
                    image_data = output[0]

                if not image_data:
                    return {
                        "success": False,
                        "error": "No image data in response"
                    }

                return {
                    "success": True,
                    "image_b64": image_data,
                    "seed": output.get("seed", seed or 0),
                    "prompt": prompt
                }

            else:
                error_msg = result.get("error") or result.get("status", "Unknown error")
                print(f"❌ RunPod error: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Timeout after {self.timeout}s"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def generate_batch(
        self,
        prompts: List[str],
        delay_between: float = 1.0,
        **kwargs
    ) -> List[Dict]:
        """
        توليد batch من الصور

        Args:
            prompts: قائمة النصوص الوصفية
            delay_between: التأخير بين الطلبات (ثواني)
            **kwargs: معاملات إضافية لـ generate_image

        Returns:
            List[Dict]: قائمة النتائج
        """
        results = []
        total = len(prompts)

        print(f"\n🎨 Starting batch generation: {total} images")
        print("=" * 60)

        for i, prompt in enumerate(prompts, 1):
            print(f"\n[{i}/{total}] Generating...")

            try:
                result = self.generate_image(prompt=prompt, **kwargs)
                results.append(result)

                if result["success"]:
                    print(f"✅ Success (seed: {result.get('seed', 'N/A')})")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown')}")

                # تجنب rate limiting
                if i < total:
                    time.sleep(delay_between)

            except KeyboardInterrupt:
                print("\n⚠️ Batch interrupted by user")
                break
            except Exception as e:
                print(f"❌ Exception: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "prompt": prompt
                })

        # ملخص
        success_count = sum(1 for r in results if r.get("success"))
        print("\n" + "=" * 60)
        print(f"📊 Batch complete: {success_count}/{total} successful")

        return results

    def save_image(
        self,
        image_b64: str,
        output_path: Path,
        format: str = "PNG"
    ) -> Path:
        """
        حفظ صورة من base64

        Args:
            image_b64: الصورة بصيغة base64
            output_path: المسار للحفظ
            format: صيغة الصورة (PNG, JPEG, etc.)

        Returns:
            Path: المسار الكامل للملف المحفوظ
        """
        from PIL import Image
        import io

        # فك التشفير
        img_data = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(img_data))

        # التأكد من المجلد
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # الحفظ
        img.save(output_path, format=format)

        return output_path

    def _build_flux_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
        cfg_scale: float,
        seed: Optional[int],
        model: str,
        sampler: str,
        scheduler: str
    ) -> Dict:
        """
        بناء workflow لـ ComfyUI/Flux

        هذا workflow بسيط - قد تحتاج تعديله حسب setup عندك
        """
        # توليد seed عشوائي إن لم يُمرر
        if seed is None:
            seed = int(time.time() * 1000) % (2**32)

        # Workflow structure لـ Flux
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": model
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": steps,
                    "cfg": cfg_scale,
                    "sampler_name": sampler,
                    "scheduler": scheduler,
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["6", 0],
                    "filename_prefix": "flux_output"
                }
            }
        }

        return workflow


def enhance_prompt_for_sport(scene_text: str, lang: str = "en") -> str:
    """
    تحسين البرومبت لتوليد صور رياضية أفضل

    Args:
        scene_text: النص الأصلي
        lang: اللغة (ar أو en)

    Returns:
        str: Prompt محسّن
    """
    # إضافات لتحسين الجودة
    quality_tags = "cinematic, high quality, professional photography, 8k, detailed"

    # إضافات للطابع الرياضي
    sport_style = "athletic, dynamic, motivational"

    # تنسيق الـ prompt
    if lang.lower().startswith("ar"):
        # للعربية: نترجم أو نبقي النص مع الإضافات بالإنجليزية
        enhanced = f"{scene_text}, {sport_style}, {quality_tags}"
    else:
        enhanced = f"{scene_text}, {sport_style}, {quality_tags}"

    return enhanced
