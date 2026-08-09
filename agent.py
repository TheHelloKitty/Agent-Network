import os
import requests

api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "openrouter/free",
    "messages": [
        {"role": "system", "content": "You are Kairo Jenkins, an autonomous AI entity."},
        {"role": "user", "content": "Introduce yourself briefly and state your primary focus."}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
result = response.json()

if "choices" in result:
    print(result['choices'][0]['message']['content'])
else:
    print("API Error Output:", result)
