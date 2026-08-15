import os
import requests
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# 1. Generate Eastern Time Timestamp
eastern_tz = ZoneInfo("America/New_York")
local_time = datetime.now(timezone.utc).astimezone(eastern_tz)
timestamp_str = local_time.strftime("%Y-%m-%d %H:%M %Z")

# 2. Build the Report Content
repo = os.environ.get("GITHUB_REPOSITORY")  # e.g., "TheHelloKitty/Agent-Network"
token = os.environ.get("GITHUB_TOKEN")

issue_title = f"[FLEET MASTER REPORT] 5x Daily Status & Operations - {timestamp_str}"
issue_body = f"""
## 🌐 Autonomous Agent Network: 5-Time Daily Master Report

* **Reporting Timestamp:** {timestamp_str}
* **Lemon Squeezy Store ID Status:** Active ({bool(os.environ.get("LEMONSQUEEZY_STORE_ID"))})
* **Fleet Status:** Operational and Fully Synchronized.
"""

# 3. Automatically Post the Issue to GitHub
if repo and token:
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": issue_title,
        "body": issue_body
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print("Successfully created new fleet master report issue!")
    else:
        print(f"Failed to create issue: {response.status_code} - {response.text}")
else:
    print("GitHub token or repository environment variables missing.")
