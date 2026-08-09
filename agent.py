import os
import requests

# Retrieve secret key safely from environment
api_key = os.getenv("OPENROUTER_API_KEY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "deepseek/deepseek-chat",
    "messages": [
        {"role": "system", "content": "You are Kairo Jenkins, a micro-space architectural designer."},
        {"role": "user", "content": "Share a quick tip about spatial optimization in a 200 sq ft off-grid home."}
    ]
}

response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
print(response.json()['choices'][0]['message']['content'])
