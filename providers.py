import os
import time
import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct",
    "google/gemma-2-9b-it",
    "mistralai/mistral-7b-instruct",
]
GROQ_MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "gemma2-9b-it",
]
GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
    "gemini-1.5-flash",
]

def _openai_chat(url, key, model, messages, temperature, max_tokens):
    r = requests.post(
        url,
        headers={"Authorization": "Bearer %s" % key, "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError("%s %s %s" % (model, r.status_code, r.text[:240]))
    return r.json()["choices"][0]["message"]["content"]

def _messages_to_gemini(messages):
    system_parts = []
    contents = []
    for m in messages:
        role = m.get("role")
        text = m.get("content") or ""
        if role == "system":
            system_parts.append(text)
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": text}]})
        else:
            contents.append({"role": "user", "parts": [{"text": text}]})
    if not contents:
        contents = [{"role": "user", "parts": [{"text": "Continue."}]}]
    payload = {"contents": contents, "generationConfig": {}}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
    return payload

def _gemini_chat(key, model, messages, temperature, max_tokens):
    payload = _messages_to_gemini(messages)
    payload["generationConfig"] = {"temperature": temperature, "maxOutputTokens": max_tokens}
    r = requests.post(
        GEMINI_URL.format(model=model),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if r.status_code >= 400:
        raise RuntimeError("gemini %s %s %s" % (model, r.status_code, r.text[:240]))
    parts = ((((r.json().get("candidates") or [{}])[0].get("content") or {}).get("parts")) or [])
    text = "".join(p.get("text") or "" for p in parts)
    if not text.strip():
        raise RuntimeError("gemini empty")
    return text

def generate_with_failover(messages, temperature=0.8, max_tokens=800):
    errors = []
    or_key = os.getenv("OPENROUTER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if or_key:
        for model in OPENROUTER_MODELS:
            try:
                print("try openrouter", model)
                return _openai_chat(OPENROUTER_URL, or_key, model, messages, temperature, max_tokens)
            except Exception as e:
                errors.append(str(e))
                time.sleep(1)

    if gemini_key:
        for model in GEMINI_MODELS:
            try:
                print("try gemini", model)
                return _gemini_chat(gemini_key, model, messages, temperature, max_tokens)
            except Exception as e:
                errors.append(str(e))
                time.sleep(1)
    else:
        print("gemini skipped: no GEMINI_API_KEY in env")

    if groq_key:
        for model in GROQ_MODELS:
            try:
                print("try groq", model)
                return _openai_chat(GROQ_URL, groq_key, model, messages, temperature, max_tokens)
            except Exception as e:
                errors.append(str(e))
                time.sleep(1)

    raise RuntimeError("All providers failed: " + " | ".join(errors[:8]))
