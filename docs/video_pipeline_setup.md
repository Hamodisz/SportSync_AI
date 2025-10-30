# Video Pipeline Setup

## Local (macOS/Linux, CPU-only)

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r video_pipeline/requirements.local.txt
```

* تأكد من وجود `ffmpeg` على جهازك (`brew install ffmpeg` أو `sudo apt install ffmpeg`).
* المخرجات تكتب في مسار تملك صلاحية الكتابة عليه (مثل `outputs/`).

## RunPod / GPU Worker

داخل الـ container (Ubuntu-based):

```bash
apt-get update && apt-get install -y ffmpeg pkg-config
pip install --upgrade pip
pip install -r video_pipeline/requirements.runpod.txt
```

* هذا الملف يسحب كل متطلبات مشروعي Git الخارجيين (shorts + longform)، بما فيها حزم CUDA (`nvidia-*`, `torch`, `triton`).
* تأكد من إختيار صورة RunPod مع CUDA 12 ومتاجر cudnn ملائمة.

## تشغيل سريع

```bash
python3 video_pipeline/generate.py --mode longform   --script-text "TITLE: قصة اختبار###TEXT: هذه فقرة تجريبية"   --output outputs/sample_longform.mp4

python3 video_pipeline/generate.py --mode shorts   --youtube-url "https://youtu.be/<video_id>"   --output outputs/sample_shorts.mp4
```

> لو أحد الأوامر فشل يعود مباشرة للـ placeholder، فتأكد من مراجعة اللوج لمعرفة الاعتماديات الناقصة.
