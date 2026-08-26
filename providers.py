import os
import time
from openai import OpenAI

PROVIDERS = [
    {
        "name": "openrouter",
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "google/gemma-2-9b-it:free",
            "meta-llama/llama-3.3-70b-instruct",
            "qwen/qwen-2.5-72b-instruct",
        ],
    },
    {
        "name": "groq",
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1",
        "models": [
            "openai/gpt-oss-20b",
            "openai/gpt-oss-120b",
            "qwen/qwen3.6-27b",
        ],
    },
]

TOKEN_TRIES = [800, 500, 300]

def get_client(provider):
    api_key = os.getenv(provider["api_key_env"])
    if not api_key:
        return None
    return OpenAI(
        base_url=provider["base_url"],
        api_key=api_key,
    )

def is_credit_or_limit_error(err):
    text = str(err).lower()
    return (
        "402" in text
        or "429" in text
        or "credit" in text
        or "rate limit" in text
        or "max_tokens" in text
        or "tokens per day" in text
        or "can only afford" in text
    )

def generate_with_failover(messages, temperature=0.7, max_tokens=800):
    last_error = None
    requested = [max_tokens] + [t for t in TOKEN_TRIES if t < max_tokens]

    for provider in PROVIDERS:
        client = get_client(provider)
        if client is None:
            print("Skipping", provider["name"], "- no API key")
            continue

        for model in provider["models"]:
            for tokens in requested:
                try:
                    print("Trying", provider["name"], model, "tokens", tokens)
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=tokens,
                    )
                    content = response.choices[0].message.content
                    if content and content.strip():
                        print("Using", provider["name"], model, "tokens", tokens)
                        return content
                    print("Empty response from", provider["name"], model)
                except Exception as e:
                    print("Failed", provider["name"], model, e)
                    last_error = e
                    if is_credit_or_limit_error(e):
                        time.sleep(1)
                        continue
                    time.sleep(1)

    raise RuntimeError("All providers failed. Last error: %s" % last_error)
