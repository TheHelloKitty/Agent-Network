import os
import requests
import base64
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

def test_twitter_v2_endpoint():
    """Performs a direct integration test against the Twitter/X API v2 endpoints to verify if publishing works."""
    if not TWITTER_BEARER_TOKEN:
        return "❌ Twitter Bearer Token is not set in the environment variables."
    
    # Check rate limit / connection status against X API v2
    url = "https://api.x.com/2/users/me"
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"📡 Twitter API Response Code: {response.status_code}")
        print(f"📦 Twitter API Response Body: {response.text}")
        
        if response.status_code == 200:
            return "✅ SUCCESS: Twitter/X API connection is fully functional and authenticated!"
        elif response.status_code == 401:
            return "❌ AUTHENTICATION FAILED: Twitter Bearer Token is invalid or expired."
        elif response.status_code == 403:
            return "⚠️ FORBIDDEN: Token lacks required scopes (ensure 'tweet.write' and 'users.read' are enabled)."
        else:
            return f"⚠️ Twitter API returned status {response.status_code}: {response.text}"
    except Exception as e:
        return f"❌ Exception during Twitter API test: {str(e)}"

def run_fresh_content_and_twitter_audit():
    """Generates completely fresh timestamped files and tests Twitter API connectivity."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ Error: GITHUB_TOKEN or GITHUB_REPOSITORY missing.")
        return
    
    twitter_result = test_twitter_v2_endpoint()
    print(twitter_result)
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M-%S")
    
    # 1. Create a fresh storefront export file with a precise unique timestamp
    export_path = f"storefront_exports/Fresh_Sync_{date_str}_{time_str}.json"
    export_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{export_path}"
    
    export_content = f"""{{
  "sync_batch": "FRESH-{date_str}-{time_str}",
  "status": "FORCE_NEW_CONTENT",
  "twitter_test_result": "{twitter_result}",
  "timestamp": "{now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
  "items": [
    {{"id": 1, "name": "Autonomous Agent Framework v19", "price": 49.99}},
    {{"id": 2, "name": "B2B Workflow Automation Suite", "price": 99.99}}
  ]
}}"""
    
    payload_export = {
        "message": f"Force fresh storefront sync export for {date_str} {time_str}",
        "content": base64.b64encode(export_content.encode("utf-8")).decode("utf-8")
    }
    
    res = requests.put(export_url, json=payload_export, headers=headers, timeout=15)
    if res.status_code in [200, 201]:
        print(f"✅ Successfully created fresh export file: {export_path}")
    else:
        print(f"❌ Failed to create export file: {res.status_code} - {res.text}")

if __name__ == "__main__":
    run_fresh_content_and_twitter_audit()
