import os
import requests
import base64
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

def test_twitter_connection():
    """Tests if the Twitter/X API connection works using the provided bearer token."""
    if not TWITTER_BEARER_TOKEN:
        return "Twitter Bearer Token is missing from environment secrets."
    
    # Simple lookup or connection check against X API v2 (e.g., checking rate limit or a public endpoint)
    url = "https://api.x.com/2/users/by/username/xdevelopers"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return "✅ Twitter API connection is ACTIVE and working!"
        else:
            return f"⚠️ Twitter API responded with status {res.status_code}: {res.text}"
    except Exception as e:
        return f"❌ Twitter API connection failed: {str(e)}"

def run_viral_content_and_twitter_audit():
    """Generates brand new viral content items and tests Twitter integration, committing outputs to GitHub."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY missing.")
        return
    
    twitter_status = test_twitter_connection()
    print(twitter_status)
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    folder_path = "viral_content"
    
    # Create brand new viral content assets to fix the 'nothing new' issue
    viral_assets = [
        {
            "hook": "POV: You automated your entire business so you can spend all day playing XCOM and hanging out with your cats. 🐾✨",
            "caption": "The autonomous agent network is running 3,500 nodes deep. No manual data entry, just pure recursive scaling. Get the framework today!",
            "platform": "TikTok & Instagram Reels"
        },
        {
            "hook": "Stop manually updating your vendor ledgers. Let 3,500 autonomous AI agents do it while you sleep. 🤖💼",
            "caption": "Scale your commercial workflows instantly. Real-time background synchronization built for modern operators.",
            "platform": "Twitter / X & LinkedIn"
        }
    ]
    
    uploaded_count = 0
    for idx, asset in enumerate(viral_assets, start=1):
        filename = f"Viral_Content_Asset_{idx}_{timestamp.split()[0].replace('-', '')}.json"
        file_path_full = f"{folder_path}/{filename}"
        url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path_full}"
        
        content = f"""{{
  "asset_id": {idx},
  "type": "New Viral Marketing Content",
  "hook": "{asset['hook']}",
  "caption": "{asset['caption']}",
  "target_platform": "{asset['platform']}",
  "twitter_integration_status": "{twitter_status}",
  "timestamp": "{timestamp}"
}}"""
        
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": f"Add brand new viral content asset {idx}",
            "content": encoded_content
        }
        
        try:
            res = requests.put(url, json=payload, headers=headers, timeout=15)
            if res.status_code in [200, 201]:
                print(f"✅ Created new viral asset: {filename}")
                uploaded_count += 1
            else:
                print(f"⚠️ Failed for {filename}: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"❌ Exception for {filename}: {str(e)}")
            
    print(f"📊 Viral Content Generation Complete: {uploaded_count} new assets created.")

if __name__ == "__main__":
    run_viral_content_and_twitter_audit()
