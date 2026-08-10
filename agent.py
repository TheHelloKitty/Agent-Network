import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

def create_gumroad_product(name, description, price_cents):
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("Error: GUMROAD_ACCESS_TOKEN not found.")
        return None

    url = "https://api.gumroad.com/v2/products"
    
    payload = {
        "access_token": token,
        "name": name,
        "description": description,
        "price": price_cents,
        "published": "true"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"SUCCESS: Created product '{name}' on Gumroad!")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error: {e.code} - {error_body}")
    except Exception as e:
        print(f"Error: {str(e)}")
        
    return None

def create_github_issue(title, body):
    # Uses GitHub's built-in environment variables for your repo
    repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")
    
    if not repo or not gh_token:
        print("GitHub environment variables missing, skipping issue creation.")
        return

    url = f"https://api.github.com/repos/{repo}/issues"
    
    payload = {
        "title": title,
        "body": body
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {gh_token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            print("SUCCESS: Logged action to GitHub Issues!")
    except Exception as e:
        print(f"Failed to create GitHub Issue: {str(e)}")

if __name__ == "__main__":
    product_name = "Swarm Digital Asset Package"
    product_price = 1000 # $10.00 in cents
    description = "Generated automatically by your agent network."
    
    # 1. Attempt upload to Gumroad
    result = create_gumroad_product(
        name=product_name, 
        description=description, 
        price_cents=product_price
    )
    
    # 2. Log details to GitHub Issues based on success
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    if result and "product" in result:
        product_url = result["product"].get("short_url", "Check Gumroad dashboard")
        issue_title = f"🚀 Agent Uploaded: {product_name}"
        issue_body = f"""### Agent Action Log
* **Platform:** Gumroad
* **Product Name:** {product_name}
* **Price:** ${product_price / 100:.2f}
* **Product Link:** {product_url}
* **Timestamp:** {timestamp}
* **Status:** Successfully Published & Live
"""
    else:
        issue_title = f"⚠️ Agent Upload Failed: {product_name}"
        issue_body = f"""### Agent Error Log
* **Platform:** Gumroad
* **Product Name:** {product_name}
* **Timestamp:** {timestamp}
* **Status:** Failed to upload. Check workflow execution logs.
"""

    create_github_issue(issue_title, issue_body)
