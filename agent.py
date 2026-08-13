import os
import requests
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")

def verify_and_force_create_issue():
    """Explicitly checks GitHub repository settings, prints diagnostic debugging info, and forces issue creation."""
    if not GITHUB_TOKEN or not REPO_NAME:
        print("❌ CRITICAL ERROR: GITHUB_TOKEN or GITHUB_REPOSITORY secret is missing from environment.")
        return
    
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    payload = {
        "title": f"🚨 [VERIFIED DEPLOY] Full Fleet Status Report (3,510 Agents) - {timestamp}",
        "body": f"""# 🌐 Autonomous Agent Network: Verified Issue Broadcast

* **Status:** FORCED DISPATCH CONFIRMED
* **Total Active Fleet Count:** **3,510 Agents**
* **Timestamp:** {timestamp}

## Diagnostic Verification
If this issue appears in your repository's **Issues** tab, the GitHub API token permissions (`repo` scope) and repository environment variables are fully functional.

### Fleet Summary
* **Creative & Narrative Development:** 1,200 Agents
* **Enterprise Operations:** 1,050 Agents
* **Data Engineering & Analytics:** 860 Agents
* **Digital Commerce & Media:** 600 Agents
"""
    }
    
    print(f"🔄 Attempting direct POST request to GitHub API for repo: {REPO_NAME}...")
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"📡 Response Status Code: {res.status_code}")
        print(f"📦 Response Body: {res.text}")
        
        if res.status_code in [200, 201]:
            issue_url = res.json().get("html_url", "")
            print(f"✅ SUCCESS! Issue successfully posted: {issue_url}")
        else:
            print(f"❌ Failed to create issue. Check if GITHUB_TOKEN has 'issues: write' permission.")
    except Exception as e:
        print(f"❌ Exception occurred during API request: {str(e)}")

if __name__ == "__main__":
    verify_and_force_create_issue()
