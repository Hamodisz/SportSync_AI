# ComfyUI على الكلاود (RunPod) — خط سير سريع

## المتطلبات
- حساب RunPod (أو أي سيرفر GPU).
- CUDA جاهزة (مع قالب ComfyUI في RunPod أسهل).
- ffmpeg مثبت (السكريبت ينزّله لو مش موجود).

## الهيكلة المقترحة
project/
jobs/ # ملفات الـ workflow JSON (ComfyUI)
outputs/ # مخرجات الصور/الفيديو من ComfyUI
videos/
long/ # فيديوهات طويلة جاهزة
shorts/ # الشورتس الناتجة
audio/
voiceovers/ # تعليق صوتي
markers/
markers.sample.json
markers.sample.xml
scripts/
start_comfy_runpod.sh
comfy_batch_submit.py
make_long_video.sh
cut_shorts.py


## التشغيل على RunPod (أقصر طريق)
1) أنشئ Pod من قالب **ComfyUI** (GPU نوع L4 أو T4 كفاية كبداية).
2) في خانة Start Command للصورة، الصق ملف `scripts/start_comfy_runpod.sh`.
3) شغل الـ Pod → سيفتح ComfyUI على المنفذ 8188.
4) افتح واجهة ComfyUI (من Dashboard) وثبّت من ComfyUI-Manager:
   - **VideoHelperSuite**
   - **ComfyUI-Impact-Pack**
5) ابني أو حمّل Workflow، ثم **Save (API)** وخزّنه كـ JSON داخل `project/jobs/*.json`.

## دفع دفعات (Batch) للـ API
على السيرفر/البود:
```bash
cd project/scripts
COMFY=http://127.0.0.1:8188 python comfy_batch_submit.py --jobs ../jobs --out ../outputs

cd project/scripts
bash make_long_video.sh ../outputs/images ../audio/voiceovers/vo_001.mp3 ../videos/long/long_001.mp4 600

python cut_shorts.py --long ../videos/long/long_001.mp4 --markers ../markers/markers.sample.json --out ../videos/shorts --vertical

python cut_shorts.py --long ../videos/long/long_001.mp4 --markers ../markers/markers.sample.xml --out ../videos/shorts --vertical
