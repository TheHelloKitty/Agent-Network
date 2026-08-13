import os
import requests
import base64
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def push_live_storefront_exports():
    """Commits fully populated JSON and Markdown storefront export listings directly to the repository."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY missing.")
        return
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Push 10 fully populated live storefront export files
    for i in range(1, 11):
        file_path = f"storefront_exports/Live_Gen18_Agent_{i}_export.json"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
        
        file_content = f"""{{
  "export_batch": "GEN-18-LIVE",
  "node_id": "Agent_{i}",
  "timestamp": "{timestamp}",
  "status": "READY_FOR_SYNC",
  "storefront_metadata": {{
    "title": "Autonomous Workflow Suite - Module {i}",
    "price": {19.99 + (i * 5)},
    "currency": "USD",
    "inventory_count": {500 + (i * 25)},
    "category": "Digital Commerce & Automation"
  }}
}}"""
        
        encoded_content = base64.b64encode(file_content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Push live storefront export for Gen18 Agent {i}",
            "content": encoded_content
        }
        
        try:
            res = requests.put(url, json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                print(f"✅ Successfully exported: {file_path}")
            else:
                print(f"🔄 Notice for {file_path} (Status {res.status_code}): {res.json().get('message', res.text)}")
        except Exception as e:
            print(f"❌ Exception for {file_path}: {str(e)}")

if __name__ == "__main__":
    push_live_storefront_exports()
