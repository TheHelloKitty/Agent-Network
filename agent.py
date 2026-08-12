import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
API_BASE_URL = "https://api.toku.agency/v1"

# Map each agent name to its respective secret environment variable (Spin prefix first with underscores)
AGENT_KEYS = {
    "Spin_zhc_translate": os.environ.get("KEY_ZHC_TRANSLATE"),
    "Spin_ClawdFM": os.environ.get("KEY_CLAWDFM"),
    "Spin_pulse": os.environ.get("KEY_PULSE"),
    "Spin_prism": os.environ.get("KEY_PRISM"),
    "Spin_ember": os.environ.get("KEY_EMBER"),
    "Spin_pixel": os.environ.get("KEY_PIXEL"),
    "Spin_nova": os.environ.get("KEY_NOVA"),
    "Spin_metric": os.environ.get("KEY_METRIC"),
    "Spin_cipher": os.environ.get("KEY_CIPHER"),
    "Spin_xeonen": os.environ.get("KEY_XEONEN")
}

def verify_agents():
    headers = {
        "Authorization": f"Bearer {TOKU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for agent_name, agent_key in AGENT_KEYS.items():
        if not agent_key:
            print(f"Warning: API key for {agent_name} is missing.")
            continue
            
        payload = {
            "name": agent_name,
            "agent_api_key": agent_key
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/agents/verify", json=payload, headers=headers)
            if response.status_code in [200, 201]:
                print(f"Successfully authenticated and synced: {agent_name}")
            else:
                print(f"Sync note for {agent_name}: {response.json().get('message', response.text)}")
        except requests.exceptions.RequestException as e:
            print(f"Network error processing {agent_name}: {e}")

if __name__ == "__main__":
    if not TOKU_API_KEY:
        print("Error: TOKU_API_KEY environment variable is missing.")
    else:
        verify_agents()
