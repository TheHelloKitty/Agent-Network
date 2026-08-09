import os
import requests

# Load credentials from environment variables
client_id = os.environ.get("X_CLIENT_ID")
client_secret = os.environ.get("X_CLIENT_SECRET")

def post_to_x(text_content):
    if not client_id or not client_secret:
        return "Skipped (Missing X Secrets)"
    
    try:
        # Request OAuth 2.0 Token from X using HTTP Basic Auth for credentials
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

def create_github_issue(title, body):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        print("Missing GitHub token or repository info for issue creation.")
        return
    
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": title,
        "body": body
    }
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code == 201:
        print("GitHub Issue created successfully!")
    else:
        print(f"Failed to create GitHub issue: {res.status_code} - {res.text}")

if __name__ == "__main__":
    # Generate report message
    tweet_text = "Daily update from Kairo Jenkins! Evolving engagement strategy."
    
    print("Attempting to post to X...")
    x_result = post_to_x(tweet_text)
    print(f"X Broadcast Status: {x_result}")
    
    # Construct the GitHub issue body
    issue_title = "🚀 9-Agent Daily Broadcast Report - Live X Integration"
    issue_body = f"""### 🚀 9-Agent Daily Post & Memory Sync (Live X Broadcast)

**X (Twitter) Broadcast Status:** {x_result}

---

🤖 **Kairo Jenkins (@kairo-tech)**
**Content:** {tweet_text}
**Broadcast Status:** {x_result}
**Persona Evolution:** Evolving engagement strategy.
"""
    
    # Automatically create the issue in your repository
    create_github_issue(issue_title, issue_body)
