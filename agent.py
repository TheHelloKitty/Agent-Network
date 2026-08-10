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
    repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")
    
    if not repo or not gh_token:
        print("GitHub environment variables missing, skipping issue creation.")
        return

    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {"title": title, "body": body}
    
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
    # List of generated products from Generation 17 to upload
    generation_products = [
        {
            "name": "B2B Supply Chain Workflows Masterclass & Guide by Operator-845",
            "description": "Comprehensive B2B Supply Chain Workflows Masterclass & Guide generated automatically by Operator-845.",
            "price_cents": 3555
        },
        {
            "name": "Sci-Fi Short Stories Masterclass & Guide by Operator-425",
            "description": "Comprehensive Sci-Fi Short Stories Masterclass & Guide generated automatically by Operator-425.",
            "price_cents": 1817
        },
        {
            "name": "Real Estate Email Templates Masterclass & Guide by Operator-552",
            "description": "Comprehensive Real Estate Email Templates Masterclass & Guide generated automatically by Operator-552.",
            "price_cents": 3520
        },
        {
            "name": "Children's Books Masterclass & Guide by Operator-493",
            "description": "Comprehensive Children's Books Masterclass & Guide generated automatically by Operator-493.",
            "price_cents": 4646
        },
        {
            "name": "B2B Supply Chain Workflows Masterclass & Guide by Operator-962",
            "description": "Comprehensive B2B Supply Chain Workflows Masterclass & Guide generated automatically by Operator-962.",
            "price_cents": 3090
        }
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    success_count = 0
    issue_body_lines = [f"### Agent Generation 17 Gumroad Upload Log\n* **Timestamp:** {timestamp}\n"]

    for prod in generation_products:
        result = create_gumroad_product(
            name=prod["name"],
            description=prod["description"],
            price_cents=prod["price_cents"]
        )
        
        if result and "product" in result:
            success_count += 1
            p_url = result["product"].get("short_url", "Check Gumroad dashboard")
            issue_body_lines.append(f"- ✅ **Uploaded:** {prod['name']} [${prod['price_cents']/100:.2f}] - [View on Gumroad]({p_url})")
        else:
            issue_body_lines.append(f"- ❌ **Failed:** {prod['name']} [${prod['price_cents']/100:.2f}]")

    issue_title = f"🚀 Generation 17 Upload Summary: {success_count}/{len(generation_products)} Live on Gumroad"
    create_github_issue(issue_title, "\n".join(issue_body_lines))
