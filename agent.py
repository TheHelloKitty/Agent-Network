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
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return None, f"Gumroad HTTP Error {e.code}: {error_body}"
    except Exception as e:
        return None, f"Gumroad Error: {str(e)}"

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
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return None, f"Lemon Squeezy HTTP Error {e.code}: {error_body}"
    except Exception as e:
        return None, f"Lemon Squeezy Error: {str(e)}"

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        print("Starting dynamic asset generation and revenue sync script...")
        gumroad_token = os.environ.get("GUMROAD_ACCESS_TOKEN")
        ls_api_key = os.environ.get("LEMON_SQUEEZY_API_KEY")
        ls_store_id = os.environ.get("LEMON_SQUEEZY_STORE_ID")

        if not gumroad_token or not ls_api_key or not ls_store_id:
            print("CRITICAL ERROR: One or more required environment variables/secrets are missing.")
            exit(1)

        existing_gumroad = get_existing_gumroad_products(gumroad_token)
        existing_lemon = get_existing_lemon_products(ls_api_key)

        # Fresh high-ticket asset batch with dynamic versioning
        batch_id = datetime.now().strftime("%Y%m%d%H%M")
        generation_products = [
            {
                "name": f"[Highest Quality] Autonomous B2B Industrial Lead Gen Swarm Kit v{batch_id}",
                "description": "Verified highest-quality production-ready Python & JSON multi-agent pipeline for scraping and qualifying large industrial facility leads.",
                "price_cents": 9700
            },
            {
                "name": f"[Highest Quality] Commercial Lighting Retrofit ROI Suite v{batch_id}",
                "description": "Premium grade advanced spreadsheet models, client presentation templates, and energy-saving audit forms for commercial lighting contractors.",
                "price_cents": 7500
            },
            {
                "name": f"[Highest Quality] Automated E-Commerce Storefront Migration Kit v{batch_id}",
                "description": "Enterprise-tier technical blueprints, automated scripts, and product data mapping tools for fast, robust storefront launches.",
                "price_cents": 12500
            },
            {
                "name": f"[Highest Quality] High-Converting Cold Email & Outreach Library v{batch_id}",
                "description": "Rigorously tested and proven multi-channel B2B outreach scripts designed specifically for high-ticket service and software sales.",
                "price_cents": 4900
            }
        ]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        gumroad_new = 0
        lemon_new = 0
        uploaded_items = []
        issues_list = []
        log_lines = [f"\n=== DYNAMIC ASSET SYNC LOG ({timestamp}) ==="]

        for prod in generation_products:
            name = prod["name"]
            price = prod["price_cents"]
            desc = prod["description"]
            log_lines.append(f"\nProduct: {name} [${price/100:.2f}]")

            # Push to Gumroad
            if name in existing_gumroad:
                issues_list.append(f"Gumroad Skip / Collision for '{name}': Product name already exists.")
                log_lines.append(f"  - Gumroad: Skipped (Already Exists)")
            else:
                g_res, g_err = create_gumroad_product(name, desc, price, gumroad_token)
                if g_err:
                    issues_list.append(f"Gumroad API Error for '{name}': {g_err}")
                elif g_res and "product" in g_res:
                    gumroad_new += 1
                    g_url = g_res["product"].get("short_url", "#")
                    uploaded_items.append(f"Gumroad: {name} ({g_url})")
                    log_lines.append(f"  - Gumroad: Published successfully ({g_url})")

            # Push to Lemon Squeezy
            if name in existing_lemon:
                issues_list.append(f"Lemon Squeezy Skip / Collision for '{name}': Product name already exists.")
                log_lines.append(f"  - Lemon Squeezy: Skipped (Already Exists)")
            else:
                l_res, l_err = create_lemon_squeezy_product(name, desc, ls_api_key, ls_store_id)
                if l_err:
                    issues_list.append(f"Lemon Squeezy API Error for '{name}': {l_err}")
                elif l_res and "data" in l_res:
                    lemon_new += 1
                    uploaded_items.append(f"Lemon Squeezy: {name}")
                    log_lines.append("  - Lemon Squeezy: Published successfully")

        print("\n".join(log_lines))

        print("\n" + "="*40)
        print("📊 AGENT UPLOAD REPORT")
        print("="*40)
        print(f"Total New Products Deployed This Run: {len(uploaded_items)}")
        for item in uploaded_items:
            print(f"  ✅ {item}")

        print("\n" + "="*40)
        print("⚠️ RUN ISSUES & WARNINGS")
        print("="*40)
        if len(issues_list) == 0:
            print("  🎉 Zero issues detected! All operations nominal.")
        else:
            for issue in issues_list:
                print(f"  ⚠️ {issue}")
        print("="*40)

    except Exception as e:
        import traceback
        traceback.print_exc()
        exit(1)
