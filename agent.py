import os
import json
import requests

# 1. Get X (Twitter) OAuth 2.0 Credentials from Environment
client_id = os.environ.get("X_CLIENT_ID")
client_secret = os.environ.get("X_CLIENT_SECRET")

x_broadcast_status = "Skipped (Credentials Missing)"

def post_to_x(text_content):
    if not client_id or not client_secret:
        return "Skipped (Missing X Secrets)"
    
    try:
        # Request OAuth 2.0 Token from X
        token_url = "https://api.x.com/2/oauth2/token"
        auth_data = {
            "grant_type": "client_credentials"
        }
        response = requests.post(token_url, data=auth_data, auth=(client_id, client_secret))
        
        if response.status_code != 200:
            return f"Auth Failed: {response.text}"
            
        token_json = response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            return "Auth Failed: No access token returned"
            
        # Post tweet using X API v2
        tweet_url = "https://api.x.com/2/tweets"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {"text": text_content}
        
        tweet_response = requests.post(tweet_url, headers=headers, json=payload)
        if tweet_response.status_code == 201:
            return "Successfully Posted Live!"
        else:
            return f"Post Failed: {tweet_response.status_code} - {tweet_response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"

# Execute live broadcast for agent update
agent_tweet = "🚀 9-Agent Daily Update: Systems operational, Base-Sepolia wallet synced, and network broadcasting active!"
x_broadcast_status = post_to_x(agent_tweet)

# Build Agent Report Body for GitHub Issue
report_body = f"""🚀 **9-Agent Daily Post & Memory Sync (Live X Broadcast)**

**X (Twitter) Broadcast Status:** {x_broadcast_status}

---

🤖 **Kairo Jenkins (@kairo-tech)**
**Content:** Daily update from Kairo Jenkins!
**Broadcast Status:** {x_broadcast_status}
**Persona Evolution:** Evolving engagement strategy.
"""

# Post a Brand-New GitHub Issue Tracking Log
github_token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY")

if github_token and repo:
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {
        "title": "🚀 9-Agent Daily Broadcast Report - Live X Integration",
        "body": report_body
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully created a brand-new daily report issue!")
    else:
        print(f"Failed to create issue: {response.status_code} - {response.text}")
