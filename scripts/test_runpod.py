# -- coding: utf-8 --
from core.runpod_client import comfy_runsync

# اختبار خفيف: تحميل نموذج فقط (ما يولّد صورة)
resp = comfy_runsync({
    "30": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "flux1-dev-fp8.safetensors"}
    }
})
print(resp)
