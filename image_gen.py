import os
import time
from pathlib import Path
import requests

FAL_KEY = os.getenv("FAL_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")

def save_image(content, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(content)
    print("Saved", out_path)
    return out_path

def generate_fal(prompt, out_path):
    if not FAL_KEY:
        raise RuntimeError("FAL_KEY missing")
    r = requests.post(
        "https://fal.run/fal-ai/flux/schnell",
        headers={"Authorization": "Key %s" % FAL_KEY, "Content-Type": "application/json"},
        json={"prompt": prompt, "image_size": "square_hd", "num_images": 1},
        timeout=120,
    )
    r.raise_for_status()
    url = r.json()["images"][0]["url"]
    img = requests.get(url, timeout=60)
    img.raise_for_status()
    return save_image(img.content, out_path)

def generate_hf(prompt, out_path):
    if not HF_TOKEN:
        raise RuntimeError("HUGGINGFACE_TOKEN missing")
    r = requests.post(
        "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell",
        headers={"Authorization": "Bearer %s" % HF_TOKEN},
        json={"inputs": prompt},
        timeout=180,
    )
    if r.status_code != 200:
        raise RuntimeError("HF image failed: %s %s" % (r.status_code, r.text[:300]))
    return save_image(r.content, out_path)

def generate_image(prompt, out_path):
    errors = []
    if FAL_KEY:
        try:
            return generate_fal(prompt, out_path)
        except Exception as e:
            errors.append(str(e))
    if HF_TOKEN:
        try:
            return generate_hf(prompt, out_path)
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError("Image generation failed: %s" % " | ".join(errors))

def cover_prompt(title, category="romance"):
    return (
        "Photorealistic book cover, no text, cinematic lighting, "
        "commercial ebook cover mood for a %s story titled '%s', "
        "high detail, clean composition, adult audience, not childish"
    ) % (category, title)

def profile_prompt(name="Rose Bloom"):
    return (
        "Photorealistic portrait of a beautiful woman named %s, "
        "long wavy dark hair, nose piercing, crescent moon tattoo, "
        "soft seductive smile, looking at camera, warm lighting, "
        "clean background, high detail face"
    ) % name

if __name__ == "__main__":
    generate_image(
        cover_prompt("Second Chance Harbor", "romance"),
        "storefront_exports/covers/second_chance_harbor.png"
    )
    time.sleep(2)
    generate_image(
        profile_prompt("Rose Bloom"),
        "storefront_exports/profiles/rose_bloom.png"
    )
