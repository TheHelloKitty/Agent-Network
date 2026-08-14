import os
import requests
import base64
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def fetch_existing_files_in_folder(folder_path):
    """Fetches a list of all existing file names in a repository folder to prevent duplicates."""
    if not GITHUB_TOKEN or not REPO_NAME:
        return set()
    
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{folder_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            items = res.json()
            return {item["name"] for item in items if item["type"] == "file"}
    except Exception:
        pass
    return set()

def upload_next_generation_storefront_exports():
    """Scans storefront exports, determines the next generation number, filters duplicates, and pushes new files."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY missing.")
        return
    
    folder_path = "storefront_exports"
    existing_files = fetch_existing_files_in_folder(folder_path)
    print(f"📁 Found {len(existing_files)} existing files in {folder_path}.")
    
    # Determine next generation dynamically (max found + 1, starting from 18 if not found)
    max_gen = 17
    for fname in existing_files:
        if fname.startswith("Gen") and "_Agent_" in fname:
            try:
                gen_num = int(fname.split("_")[0].replace("Gen", ""))
                if gen_num > max_gen:
                    max_gen = gen_num
            except ValueError:
                pass
                
    next_gen = max_gen + 1
    print(f"🚀 Target Next Generation for Export: Gen{next_gen}")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    uploaded_count = 0
    skipped_count = 0
    
    # Generate full complement of 9 agent exports for the next generation
    for agent_id in range(1, 10):
        filename = f"Gen{next_gen}_Agent_{agent_id}_listing.json"
        
        # Check for duplicates explicitly
        if filename in existing_files:
            print(f"⏩ Skipping duplicate: {filename}")
            skipped_count += 1
            continue
        
        file_path_full = f"{folder_path}/{filename}"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path_full}"
        
        content = f"""{{
  "generation": {next_gen},
  "agent_id": "Agent_{agent_id}",
  "network": "NEURAL-GRID-RECURSIVE",
  "channel": "Storefront Direct Sync",
  "timestamp": "{timestamp}",
  "status": "LIVE_AND_DE-DUPLICATED",
  "product_details": {{
    "title": "Autonomous Workflow Module Gen {next_gen} - Node {agent_id}",
    "price_usd": {(next_gen * 2.00) + (agent_id * 1.25):.2f},
    "inventory": {1000 + (agent_id * 75)},
    "description": "Unique storefront listing generated autonomously with strict duplicate checks."
  }}
}}"""
        
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Upload unique storefront export for Gen{next_gen} Agent {agent_id}",
            "content": encoded_content
        }
        
        try:
            res = requests.put(url, json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                print(f"✅ Successfully uploaded unique file: {filename}")
                uploaded_count += 1
            else:
                print(f"⚠️ Failed for {filename}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"❌ Exception for {filename}: {str(e)}")
            
    print(f"📊 Summary: {uploaded_count} uploaded, {skipped_count} duplicates skipped.")

if __name__ == "__main__":
    upload_next_generation_storefront_exports()
