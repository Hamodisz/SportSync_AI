# -- coding: utf-8 --
from core.runpod_client import comfy_runsync

# أبسط وركفلو FLUX يولّد صورة واحدة 512x512 ويحفظها (Base64 في المخرجات)
workflow = {
  "27": {"class_type":"EmptySD3LatentImage","inputs":{"width":512,"height":512,"batch_size":1}},
  "30": {"class_type":"CheckpointLoaderSimple","inputs":{"ckpt_name":"flux1-dev-fp8.safetensors"}},
  "6":  {"class_type":"CLIPTextEncode","inputs":{"text":"a simple cute robot logo, minimal, vector style","clip":["30",1]}},
  "35": {"class_type":"FluxGuidance","inputs":{"guidance":3.5,"conditioning":["6",0]}},
  "33": {"class_type":"CLIPTextEncode","inputs":{"text":"","clip":["30",1]}},
  "31": {"class_type":"KSampler","inputs":{
      "seed":123456789, "steps":10, "cfg":1, "sampler_name":"euler",
      "scheduler":"simple", "denoise":1, "model":["30",0],
      "positive":["35",0], "negative":["33",0], "latent_image":["27",0]
  }},
  "8":  {"class_type":"VAEDecode","inputs":{"samples":["31",0],"vae":["30",2]}},
  "40": {"class_type":"SaveImage","inputs":{"filename_prefix":"ComfyUI","images":["8",0]}}
}

resp = comfy_runsync(workflow)
print(resp)  # فيه base64 للصورة داخل output
