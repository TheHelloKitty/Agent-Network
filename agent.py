import os
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# --- GUMROAD FUNCTIONS ---
def get_existing_gumroad_products(token):
    url = f"https://api.gumroad.com/v2/products?access_token={token}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("success"):
                return {p["name"] for p in data.get("products", [])}
    except Exception as e:
        print(f"Warning: Could not fetch Gumroad products: {e}")
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
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Gumroad Error ({name}): {str(e)}")
    return None

# --- LEMON SQUEEZY FUNCTIONS ---
def get_existing_lemon_products(api_key):
    url = "https://api.lemonsqueezy.com/v1/products"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return {p["attributes"]["name"] for p in data.get("data", [])}
    except Exception as e:
        print(f"Warning: Could not fetch Lemon Squeezy products: {e}")
    return set()

def create_lemon_squeezy_product(name, description, api_key, store_id):
    url = "https://api.lemonsqueezy.com/v1/products"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }
    payload = {
        "data": {
            "type": "products",
            "attributes": {
                "name": name,
                "description": description
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(store_id)
                    }
                }
            }
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"Lemon Squeezy HTTP Error ({name}): {error_body}")
    except Exception as e:
        print(f"Lemon Squeezy Error ({name}): {str(e)}")
    return None

# --- GITHUB ISSUE LOGGER ---
def create_github_issue(title, body):
    repo = os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GITHUB_TOKEN")
    if not repo or not gh_token:
        print("GitHub environment variables missing, skipping issue.")
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

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    gumroad_token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    ls_api_key = os.environ.get("LEMON_SQUEEZY_API_KEY")
    ls_store_id = os.environ.get("LEMON_SQUEEZY_STORE_ID")

    if not gumroad_token:
        print("Error: GUMROAD_ACCESS_TOKEN not found.")
        exit(1)
    if not ls_api_key or not ls_store_id:
        print("Error: Lemon Squeezy API Key or Store ID not found in environment variables.")
        exit(1)

    existing_gumroad = get_existing_gumroad_products(gumroad_token)
    existing_lemon = get_existing_lemon_products(ls_api_key)

    generation_products = [
        {
            "name": "Autonomous B2B Industrial Lead Generation Swarm Kit by Operator-845",
            "description": "Complete production-ready Python & JSON multi-agent pipeline for scraping and qualifying large industrial facility leads.",
            "price_cents": 9700
        },
        {
            "name": "Commercial Lighting Retrofit ROI Calculator & Proposal Suite by Operator-425",
            "description": "Advanced spreadsheet models, client presentation templates, and energy-saving audit forms for commercial lighting contractors.",
            "price_cents": 7500
        },
        {
            "name": "Automated E-Commerce Storefront Migration & Setup Kit by Operator-552",
            "description": "Step-by-step technical blueprints, automated scripts, and product data mapping tools for fast storefront launches.",
            "price_cents": 12500
        },
        {
            "name": "High-Converting Cold Email & Outreach Sequence Library by Operator-493",
            "description": "Tested and proven multi-channel B2B outreach scripts designed specifically for high-ticket service and software sales.",
            "price_cents": 4900
        }
    ]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    gumroad_new = 0
    lemon_new = 0
    issue_lines = [f"### 💰 Multi-Storefront Revenue Sync Log\n* **Timestamp:** {timestamp}\n"]

    for prod in generation_products:
        name = prod["name"]
        price = prod["price_cents"]
        desc = prod["description"]
        issue_lines.append(f"#### 📄 {name} [${price/100:.2f}]")

        # Push to Gumroad if not present
        if name in existing_gumroad:
            issue_lines.append("- **Gumroad:** ⏭️ Skipped (Already Exists)")
        else:
            g_res = create_gumroad_product(name, desc, price, gumroad_token)
            if g_res and "product" in g_res:
                gumroad_new += 1
                g_url = g_res["product"].get("short_url", "#")
                issue_lines.append(f"- **Gumroad:** ✅ Published ([View]({g_url}))")
            else:
                issue_lines.append("- **Gumroad:** ⏭️ Skipped / Already Exists")

        # Push to Lemon Squeezy if not present
        if name in existing_lemon:
            issue_lines.append("- **Lemon Squeezy:** ⏭️ Skipped (Already Exists)")
        else:
            l_res = create_lemon_squeezy_product(name, desc, ls_api_key, ls_store_id)
            if l_res and "data" in l_res:
                lemon_new += 1
                issue_lines.append("- **Lemon Squeezy:** ✅ Published")
            else:
                issue_lines.append("- **Lemon Squeezy:** ⏭️ Skipped / Already Exists")

    issue_title = f"💰 Revenue Run: {gumroad_new} Gumroad / {lemon_new} Lemon Squeezy New"
    create_github_issue(issue_title, "\n".join(issue_lines))
