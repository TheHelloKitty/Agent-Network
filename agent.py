from diffusers import FluxPipeline
import torch
import gc

# Clear any cached memory
gc.collect()
torch.cuda.empty_cache()

# Load pipeline with memory-efficient sequential CPU offloading instead of model offload
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.float16
)

# Use sequential cpu offload which saves significantly more VRAM on restricted environments
pipe.enable_sequential_cpu_offload()
pipe.vae.enable_tiling()

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
        height=512,
        width=512
    ).images[0]

    filename = f"{name.lower().replace(' ', '_')}_profile.png"
    image.save(filename)
    display(image)
    print(f"✅ Saved as {filename}")
    return image

# Generate Rose Bloom
generate_profile("Rose Bloom")
