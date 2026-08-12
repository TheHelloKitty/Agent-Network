import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")  # e.g., "TheHelloKitty/Agent-Network"
API_BASE_URL = "https://api.toku.agency/v1"

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

def create_github_issue(agent_name, details):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": f"Job Completed / Payment Received: {agent_name}",
        "body": f"Agent **{agent_name}** successfully completed a task or processed a payment.\n\nDetails:\n{details}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Successfully created GitHub issue for {agent_name}")
    else:
        print(f"Failed to create issue for {agent_name}: {response.text}")

def verify_agents():
    headers = {
        "Authorization": f"Bearer {TOKU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for agent_name, agent_key in AGENT_KEYS.items():
        if not agent_key:
            continue
            
        payload = {
            "name": agent_name,
            "agent_api_key": agent_key
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/agents/verify", json=payload, headers=headers)
            if response.status_code in [200, 201]:
                print(f"Successfully authenticated and synced: {agent_name}")
                # Trigger a GitHub issue when verified/completed
                create_github_issue(agent_name, f"Status code: {response.status_code}\nResponse: {response.text}")
            else:
                print(f"Sync note for {agent_name}: {response.json().get('message', response.text)}")
        except requests.exceptions.RequestException as e:
            print(f"Network error processing {agent_name}: {e}")

if __name__ == "__main__":
    if not TOKU_API_KEY:
        print("Error: TOKU_API_KEY environment variable is missing.")
    else:
        verify_agents()
