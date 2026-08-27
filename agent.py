import os
from pathlib import Path
import requests

FAL_KEY = os.getenv("FAL_KEY")
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")
HF_MODEL = "black-forest-labs/FLUX.1-schnell"

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
        headers={
            "Authorization": "Key %s" % FAL_KEY,
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "image_size": "square_hd",
            "num_images": 1,
        },
        timeout=120,
    )
    if r.status_code != 200:
        raise RuntimeError("Fal failed: %s %s" % (r.status_code, r.text[:400]))
    url = r.json()["images"][0]["url"]
    img = requests.get(url, timeout=60)
    img.raise_for_status()
    print("Used Fal")
    return save_image(img.content, out_path)

def generate_hf(prompt, out_path):
    if not HF_TOKEN:
        raise RuntimeError("HUGGINGFACE_TOKEN missing")
    urls = [
        "https://router.huggingface.co/hf-inference/models/%s" % HF_MODEL,
        "https://api-inference.huggingface.co/models/%s" % HF_MODEL,
    ]
    last = None
    for url in urls:
        r = requests.post(
            url,
            headers={
                "Authorization": "Bearer %s" % HF_TOKEN,
                "Content-Type": "application/json",
            },
            json={"inputs": prompt},
            timeout=180,
        )
        if r.status_code == 200:
            print("Used Hugging Face")
            return save_image(r.content, out_path)
        last = "%s %s" % (r.status_code, r.text[:300])
    raise RuntimeError("HF failed: %s" % last)

def generate_image(prompt, out_path):
    errors = []
    if FAL_KEY:
        try:
            return generate_fal(prompt, out_path)
        except Exception as e:
            print("Fal error:", e)
            errors.append(str(e))
    if HF_TOKEN:
        try:
            return generate_hf(prompt, out_path)
        except Exception as e:
            print("HF error:", e)
            errors.append(str(e))
    raise RuntimeError("Image generation failed: %s" % " | ".join(errors))

def cover_prompt(title, category="romance"):
    return (
        "Photorealistic book cover, no text on the cover, cinematic lighting, "
        "commercial ebook mood for a %s story titled '%s', "
        "high detail, clean composition"
    ) % (category, title)

def profile_prompt(name="Rose Bloom"):
    return (
        "Photorealistic portrait of a beautiful woman named %s, "
        "long wavy dark hair, nose piercing, crescent moon tattoo, "
        "soft smile, looking at camera, warm lighting, clean background, "
        "high detail face, professional profile picture"
    ) % name

if __name__ == "__main__":
    generate_image(
        cover_prompt("Second Chance Harbor", "romance"),
        "storefront_exports/covers/second_chance_harbor.png"
    )
    generate_image(
        profile_prompt("Rose Bloom"),
        "storefront_exports/profiles/rose_bloom.png"
    )
