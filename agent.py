import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
API_BASE_URL = "https://api.toku.agency/v1"

# Map each agent name to its respective secret environment variable
AGENT_KEYS = {
    "Spin-zhc-translate": os.environ.get("KEY_ZHC_TRANSLATE"),
    "Spin-ClawdFM": os.environ.get("KEY_CLAWDFM"),
    "Spin-pulse": os.environ.get("KEY_PULSE"),
    "Spin-prism": os.environ.get("KEY_PRISM"),
    "Spin-ember": os.environ.get("KEY_EMBER")
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
            # Adjust the endpoint route if your verification path differs
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
