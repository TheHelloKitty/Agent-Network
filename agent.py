import os
import json
import requests
import subprocess
import sys

# 1. Ensure cdp-sdk is installed and available
CDP_AVAILABLE = False
try:
    from cdp import Cdp, Wallet
    CDP_AVAILABLE = True
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cdp-sdk"])
        from cdp import Cdp, Wallet
        CDP_AVAILABLE = True
    except Exception:
        CDP_AVAILABLE = False

try:
    from upload_post import UploadPostClient
except ImportError:
    UploadPostClient = None

# 2. Initialize Coinbase CDP Wallet Context
cdp_context = "CDP SDK not available."
if CDP_AVAILABLE:
    try:
        Cdp.configure("955d09f4-d942-4272-89dc-5799d8d5c0bd", "T7FSym8hkHNYlfQWAUFzvlPi/HtjJllsF9BsE3QcPvXysaL1Gm/OopzgPa2NABll001B+TjivSK/eXQLP4kg==")
        wallet = Wallet.create()
        cdp_context = f"Active CDP Wallet Address: {wallet.get_address().getId()} | Network: Base-Sepolia | Connected Successfully"
    except Exception as e:
        cdp_context = f"CDP Init Error: {type(e).__name__}: {e}"

# 3. Build Agent Report Content
report_body = f"""🚀 **9-Agent Daily Post & Memory Sync (CDP Upgraded)**

**Coinbase CDP On-Chain Status:** {cdp_context}

---

🤖 **Kairo Jenkins (@kairo-tech)**
**Content:** Daily update from Kairo Jenkins!
**Broadcast Status:** Skipped (No Social API Key)
**Persona Evolution:** Evolving engagement strategy.

---

🤖 **Althea Roux (@althea-wild)**
**Content:** Daily update from Althea Roux!
**Broadcast Status:** Skipped (No Social API Key)
**Persona Evolution:** Evolving engagement strategy.
"""

# 4. Post a Brand-New GitHub Issue Every Time
github_token = os.environ.get("GITHUB_TOKEN")
repo = os.environ.get("GITHUB_REPOSITORY")

if github_token and repo:
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }
    url = f"https://api.github.com/repos/{repo}/issues"
    payload = {
        "title": "🚀 9-Agent Daily Broadcast Report - CDP Upgraded",
        "body": report_body
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print("Successfully created a brand-new daily report issue!")
    else:
        print(f"Failed to create issue: {response.status_code} - {response.text}")
else:
    print("GitHub token or repository environment variables missing.")
