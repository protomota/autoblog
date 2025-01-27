import json
from urllib import request

#This is the ComfyUI api prompt format.

#If you want it for a specific workflow you can "enable dev mode options"
#in the settings of the UI (gear beside the "Queue Size: ") this will enable
#a button on the UI to save workflows in api format.

#keep in mind ComfyUI is pre alpha software so this format will change a bit.

#this is the one for the default workflow

# Configure logging
from ai_agents.core.config import logger


prompt_text = """
{
  "6": {
    "inputs": {
      "text": "An eerie cattle field at dusk, where the sun sets behind dark, ominous clouds casting long shadows. Abandoned, rusting farm equipment is scattered throughout the field, and a dilapidated wooden fence surrounds it. In the foreground, ghostly silhouettes of cattle are seen - their eyes glowing faintly in the dim light, hinting at something supernatural. A chilling mist rolls in from the edges of the field, partially obscuring a weathered barn in the background. The atmosphere is thick with tension and dread, with a haunting wind carrying distant, eerie sounds of moaning and whispers. The overall mood is unsettling, filled with a sense of foreboding and imminent danger.",
      "clip": [
        "38",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Positive Prompt)"
    }
  },
  "8": {
    "inputs": {
      "samples": [
        "31",
        0
      ],
      "vae": [
        "30",
        2
      ]
    },
    "class_type": "VAEDecode",
    "_meta": {
      "title": "VAE Decode"
    }
  },
  "9": {
    "inputs": {
      "filename_prefix": "ComfyUI",
      "images": [
        "8",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "27": {
    "inputs": {
      "width": 1280,
      "height": 720,
      "batch_size": 1
    },
    "class_type": "EmptySD3LatentImage",
    "_meta": {
      "title": "EmptySD3LatentImage"
    }
  },
  "30": {
    "inputs": {
      "ckpt_name": "flux1-dev-fp8.safetensors"
    },
    "class_type": "CheckpointLoaderSimple",
    "_meta": {
      "title": "Load Checkpoint"
    }
  },
  "31": {
    "inputs": {
      "seed": 358401552359234,
      "steps": 25,
      "cfg": 1,
      "sampler_name": "euler",
      "scheduler": "simple",
      "denoise": 1,
      "model": [
        "38",
        0
      ],
      "positive": [
        "6",
        0
      ],
      "negative": [
        "33",
        0
      ],
      "latent_image": [
        "27",
        0
      ]
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  },
  "33": {
    "inputs": {
      "text": "",
      "clip": [
        "38",
        1
      ]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Negative Prompt)"
    }
  },
  "38": {
    "inputs": {
      "lora_name": "aidmaMJ6.1-FLUX-v0.4.safetensors",
      "strength_model": 0.6,
      "strength_clip": 0.6,
      "model": [
        "30",
        0
      ],
      "clip": [
        "30",
        1
      ]
    },
    "class_type": "LoraLoader",
    "_meta": {
      "title": "Load LoRA"
    }
  }
}
"""

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
    request.urlopen(req)


prompt = json.loads(prompt_text)
#set the text prompt for our positive CLIPTextEncode
prompt["6"]["inputs"]["text"] = "a bottle with a beautiful rainbow galaxy inside it on top of a wooden table in the middle of a modern kitchen beside a plate of vegetables and mushrooms and a wine glasse that contains a planet earth with a plate with a half eaten apple pie on it"

#set the seed for our KSampler node
prompt["31"]["inputs"]["seed"] = 5


queue_prompt(prompt)