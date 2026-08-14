from diffusers import FluxPipeline
import torch
from PIL import Image

# Load model (only needs to run once)
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()

def generate_profile(name="Rose Bloom", extra_details=""):
    prompt = (
        f"Photorealistic portrait of a beautiful 23-year-old woman named {name}, "
        f"long soft wavy rose-gold hair, warm brown eyes, soft seductive smile, "
        f"delicate features, soft glamorous makeup, looking at the camera, "
        f"high detail face, natural skin texture, professional profile picture, "
        f"soft lighting, clean background, {extra_details}"
    )

    image = pipe(
        prompt=prompt,
        guidance_scale=0.0,
        num_inference_steps=4,
        max_sequence_length=256,
        height=1024,
        width=1024
    ).images[0]

    filename = f"{name.lower().replace(' ', '_')}_profile.png"
    image.save(filename)
    display(image)          # shows the image in Colab
    print(f"✅ Saved as {filename}")
    return image

# Generate Rose Bloom
generate_profile("Rose Bloom")
