import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

def get_existing_gumroad_products(token):
    """Fetches existing product names from Gumroad to prevent duplicates."""
    url = f"https://api.gumroad.com/v2/products?access_token={token}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("success"):
                return {p["name"] for p in data.get("products", [])}
    except Exception as e:
        print(f"Warning: Could not fetch existing Gumroad products: {e}")
    return set()

def create_gumroad_product(name, description, price_cents, token):
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
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("Error: GUMROAD_ACCESS_TOKEN not found.")
        exit(1)

    # 1. Fetch live products from Gumroad to check against
    existing_product_names = get_existing_gumroad_products(token)

    # 2. Gather active items produced by your agent network run
    generation_products = [
        {
            "name": "B2B Supply Chain Workflows Masterclass & Guide by Operator-845",
            "description": "B2B Supply Chain Workflows Masterclass & Guide generated automatically by Operator-845.",
            "price_cents": 3555
        },
        {
            "name": "Sci-Fi Short Stories Masterclass & Guide by Operator-425",
            "description": "Sci-Fi Short Stories Masterclass & Guide generated automatically by Operator-425.",
            "price_cents": 1817
        },
        {
            "name": "Real Estate Email Templates Masterclass & Guide by Operator-552",
            "description": "Real Estate Email Templates Masterclass & Guide generated automatically by Operator-552.",
            "price_cents": 3520
        },
        {
            "name": "Children's Books Masterclass & Guide by Operator-493",
            "description": "Children's Books Masterclass & Guide generated automatically by Operator-493.",
            "price_cents": 4646
        },
        {
            "name": "B2B Supply Chain Workflows Masterclass & Guide by Operator-962",
            "description": "B2B Supply Chain Workflows Masterclass & Guide generated automatically by Operator-962.",
            "price_cents": 3090
        }
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    new_uploads_count = 0
    issue_body_lines = [f"### 🚀 Gumroad Sync & Publish Log\n* **Timestamp:** {timestamp}\n"]

    for prod in generation_products:
        name = prod["name"]
        
        # Check if it already exists on Gumroad
        if name in existing_product_names:
            print(f"Skipping (already exists on Gumroad): {name}")
            issue_body_lines.append(f"- ⏭️ **Skipped (Already Exists):** {name}")
            continue

        result = create_gumroad_product(
            name=name,
            description=prod["description"],
            price_cents=prod["price_cents"],
            token=token
        )
        
        if result and "product" in result:
            new_uploads_count += 1
            p_url = result["product"].get("short_url", "Check Gumroad dashboard")
            issue_body_lines.append(f"- ✅ **Published:** {name} [${prod['price_cents']/100:.2f}] - [View on Gumroad]({p_url})")
        else:
            issue_body_lines.append(f"- ❌ **Failed:** {name} [${prod['price_cents']/100:.2f}]")

    # ALWAYS create an issue on every run so you have a direct status report
    issue_title = f"📊 Gumroad Run Status: {new_uploads_count} New Product(s) Published"
    create_github_issue(issue_title, "\n".join(issue_body_lines))
