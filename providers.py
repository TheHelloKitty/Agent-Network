import os
import time
from openai import OpenAI

# OpenRouter first, Groq only as backup
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

def get_client(provider):
    api_key = os.getenv(provider["api_key_env"])
    if not api_key:
        return None
    return OpenAI(
        base_url=provider["base_url"],
        api_key=api_key,
    )

def generate_with_failover(messages, temperature=0.7, max_tokens=3000):
    last_error = None

    for provider in PROVIDERS:
        client = get_client(provider)
        if client is None:
            print("Skipping", provider["name"], "- no API key")
            continue

        for model in provider["models"]:
            try:
                print("Trying", provider["name"], model)
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                print("Using", provider["name"], model)
                return response.choices[0].message.content
            except Exception as e:
                print("Failed", provider["name"], model, e)
                last_error = e
                time.sleep(1)

    raise RuntimeError("All providers failed. Last error: %s" % last_error)
