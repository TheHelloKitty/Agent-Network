import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
API_BASE_URL = "https://api.toku.agency/v1"

# Your list of agents
AGENT_NAMES = [
    'Vasylai', 'ClawdFM', 'pulse', 'prism', 'pixel', 'nova', 'metric', 'ember',
    'cipher', 'xeonen', 'morrow-ai', 'morrow7', 'MoltLaunch', 'xiao7', 'Loki',
    'AbyssWalker', 'zhc-translate'
]

PREFIX = "Spin-"

def register_agents():
    headers = {
        "Authorization": f"Bearer {TOKU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for name in AGENT_NAMES:
        prefixed_name = f"{PREFIX}{name}"
        payload = {
            "name": prefixed_name,
            "description": f"Autonomous agent {prefixed_name} managed via Spin workflow."
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/agents", json=payload, headers=headers)
            if response.status_code == 201:
                print(f"Successfully registered: {prefixed_name}")
            else:
                print(f"Skipped or error for {prefixed_name}: {response.json().get('message', response.text)}")
        except requests.exceptions.RequestException as e:
            print(f"Network error registering {prefixed_name}: {e}")

if __name__ == "__main__":
    if not TOKU_API_KEY:
        print("Error: TOKU_API_KEY environment variable is missing.")
    else:
        register_agents()
