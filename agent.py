import os
import requests
base64
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

def upload_unique_agent_outputs():
    """Scans current outputs, filters out duplicates, and uploads only new unique files to agent_outputs/."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY missing.")
        return
    
    folder_path = "agent_outputs"
    existing_files = fetch_existing_files_in_folder(folder_path)
    print(f"📁 Found {len(existing_files)} existing files in {folder_path}.")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    
    # Generate batch files for Gen 12 and Gen 13 to populate unique product markdown outputs
    new_generations = [12, 13]
    uploaded_count = 0
    skipped_count = 0
    
    for gen in new_generations:
        for agent_id in range(1, 10):
            filename = f"Gen{gen}_Agent_{agent_id}_product.md"
            
            # Check for duplicates
            if filename in existing_files:
                print(f"⏩ Skipping duplicate: {filename}")
                skipped_count += 1
                continue
            
            file_path_full = f"{folder_path}/{filename}"
            url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path_full}"
            
            content = f"""# Commercial Asset by Operator-{gen * 100 + agent_id} (Generation {gen})

* **Target Niche:** B2B Supply Chain Workflows & Automated Digital Assets
* **Retail Price Point:** ${(gen * 3.50) + (agent_id * 1.25):.2f} USD
* **Distribution Status:** Filtered & Uploaded to Storefront (Non-Duplicate)
* **Timestamp Generated:** {timestamp}

## Product Description
Autonomous workflow asset engineered by Generation {gen} Agent {agent_id}. Designed for immediate e-commerce integration, inventory sync, and multi-channel merchant distribution.
"""
            
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            payload = {
                "message": f"Upload unique output for Gen{gen} Agent {agent_id}",
                "content": encoded_content
            }
            
            try:
                res = requests.put(url, json=payload, headers=headers, timeout=15)
                if res.status_code in [200, 201]:
                    print(f"✅ Successfully uploaded unique file: {filename}")
                    uploaded_count += 1
                else:
                    print(f"⚠️ Failed for {filename}: {res.status_code}")
            except Exception as e:
                print(f"❌ Exception for {filename}: {str(e)}")
                
    print(f"📊 Summary: {uploaded_count} uploaded, {skipped_count} duplicates skipped.")

if __name__ == "__main__":
    upload_unique_agent_outputs()
