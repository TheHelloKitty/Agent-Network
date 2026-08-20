GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
    "llama-3.3-70b-versatile",  # leftover, in case it comes back
]

def generate_with_fallback(messages, temperature=0.9, max_tokens=8000):
    last_error = None

    for model in GROQ_MODELS:
        try:
            print(f"Trying model: {model}")
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print(f"✅ Using model: {model}")
            return response
        except Exception as e:
            print(f"❌ {model} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")
