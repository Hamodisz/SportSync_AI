# ComfyUI على الكلاود (RunPod) — خط سير سريع

## المتطلبات
- حساب RunPod (أو أي سيرفر GPU).
- CUDA جاهزة (قالب ComfyUI أسهل).
- ffmpeg مثبت.

## الهيكلة المقترحة
project/
  jobs/
  outputs/
  videos/{long,shorts}
  audio/voiceovers/
  markers/
  scripts/

## التشغيل على RunPod
1) أنشئ Pod من قالب **ComfyUI**.
2) حط Start Command: `scripts/start_comfy_runpod.sh`
3) ثبّت من ComfyUI-Manager:
   - VideoHelperSuite
   - ComfyUI-Impact-Pack
4) احفظ الـ Workflow كـ JSON داخل `project/jobs/*.json`.

## دفع دفعات (Batch) للـ API
```bash
cd project/scripts
COMFY=http://127.0.0.1:8188 python comfy_batch_submit.py --jobs ../jobs --out ../outputs
