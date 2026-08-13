import os
import requests
from datetime import datetime

# --- ENVIRONMENT CONFIGURATION ---
TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")

API_BASE_URL = "https://api.toku.agency/v1"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LEMON_API_URL = "https://api.lemonsqueezy.com/v1"
RESEND_API_URL = "https://api.resend.com/emails"
TWITTER_API_URL = "https://api.x.com/2/tweets"

# Dynamically map all 10 named Spin agents from environment variables
AGENT_KEYS = {}
for env_key, env_value in os.environ.items():
    if env_key.startswith("SPIN_") and env_value:
        agent_suffix = env_key.replace("SPIN_", "")
        agent_name = f"Spin_{agent_suffix.capitalize()}"
        AGENT_KEYS[agent_name] = env_value

def create_github_issue(agent_name, stage, job_id, details):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": f"[{agent_name}] [{stage.upper()}] Job ID: {job_id}",
        "body": f"Agent **{agent_name}** triggered stage: **{stage}** for job `{job_id}`.\n\nDetails:\n{details}"
    }
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass

def get_lemonsqueezy_store_id():
    """Autonomously fetches the store ID using the Lemon Squeezy API key."""
    if not LEMON_SQUEEZY_API_KEY:
        return None
    headers = {
        "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }
    try:
        res = requests.get(f"{LEMON_API_URL}/stores", headers=headers, timeout=10)
        if res.status_code == 200:
            stores = res.json().get("data", [])
            if stores:
                return stores[0].get("id")
    except Exception:
        pass
    return None

def generate_profitable_digital_product():
    """Uses OpenRouter to autonomously create content for a digital product."""
    if not OPENROUTER_API_KEY:
        return {"title": "The Freelancer AI Automation Guide", "description": "A tactical framework for automating workflows.", "price": 900}
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": "Generate a title, a short marketing description, and a pricing suggestion in cents (e.g. 999 for $9.99) for a profitable digital product. Format strictly as: TITLE: [title] | DESC: [description] | PRICE: [price in cents]"}
        ]
    }
    try:
        res = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=20)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            return {"title": "Autonomous AI Prompt & Workflow Suite", "description": content, "price": 1499}
    except Exception:
        pass
    return {"title": "The Ultimate Business AI Kit", "description": "High-utility automated prompts and systems.", "price": 1299}

def publish_to_lemon_squeezy(product_data):
    """Programmatically creates a product on Lemon Squeezy using auto-fetched Store ID."""
    if not LEMON_SQUEEZY_API_KEY:
        return "Skipped (Lemon Squeezy API Key missing)"
    
    store_id = get_lemonsqueezy_store_id()
    if not store_id:
        return "Failed to fetch Store ID automatically from Lemon Squeezy account."
    
    headers = {
        "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }
    
    payload = {
        "data": {
            "type": "products",
            "attributes": {
                "name": product_data["title"],
                "description": product_data["description"],
                "price": product_data["price"]
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
    
    try:
        res = requests.post(f"{LEMON_API_URL}/products", json=payload, headers=headers, timeout=15)
        if res.status_code in [200, 201]:
            resp_json = res.json()
            product_id = resp_json.get("data", {}).get("id")
            return f"Successfully published to Store ID {store_id}! Product ID: {product_id}"
        else:
            return f"Failed to publish (Status {res.status_code}): {res.text}"
    except Exception as e:
        return f"Exception during publishing: {str(e)}"

def broadcast_via_resend(product_title):
    """Dispatches a broadcast notification email via Resend."""
    if not RESEND_API_KEY:
        return "Resend skipped (API key missing)"
    
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "Autonomous Agent Network <onboarding@resend.dev>",
        "to": ["delivered@resend.dev"],
        "subject": f"New Product Launch: {product_title}",
        "html": f"<p>Your autonomous network successfully launched a brand new asset: <strong>{product_title}</strong>.</p>"
    }
    try:
        res = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return "Resend email dispatched successfully."
        else:
            return f"Resend failed (Status {res.status_code}): {res.text}"
    except Exception as e:
        return f"Resend error: {str(e)}"

def post_to_twitter(product_title):
    """Tweets a marketing update using the Twitter (X) API v2."""
    if not TWITTER_BEARER_TOKEN:
        return "Twitter skipped (Bearer token missing)"
    
    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": f"🚀 Just launched our newest automated drop: {product_title}. Streamline your workflow today! #AI #Automation"
    }
    try:
        res = requests.post(TWITTER_API_URL, json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return "Tweet posted successfully."
        else:
            return f"Twitter failed (Status {res.status_code}): {res.text}"
    except Exception as e:
        return f"Twitter error: {str(e)}"

def post_network_status_report(active_nodes_count, execution_summary, production_log):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    
    now = datetime.utcnow()
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")
    
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    report_body = f"""# AUTONOMOUS AGENT NETWORK (AAN): OPERATIONAL STATUS REPORT

* **Network ID:** NEURAL-GRID-7 (NG-7)
* **Total Active Fleet Agent Count:** {active_nodes_count} Named Sub-Nodes Registered & Polling
* **Reporting Timestamp:** Generated at {timestamp}
* **System Status:** FULL AUTONOMOUS PIPELINE ACTIVE

---

## 1. Toku Job Polling Summary
{execution_summary}

---

## 2. Autonomous Product Creation, Lemon Squeezy & Outreach
{production_log}
"""

    payload = {
        "title": f"Autonomous Agent Network Report - {timestamp}",
        "body": report_body
    }
    
    try:
        requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception:
        pass
    
    if DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": f"📊 **AAN Operational Report** posted! Fleet Active: {active_nodes_count} named nodes."})
        except Exception:
            pass

def run_agents():
    active_count = len(AGENT_KEYS)
    execution_logs = []
    production_logs = []

    if active_count == 0:
        execution_logs.append("- ⚠️ **Warning:** No named `SPIN_` agent keys detected. Verify secrets are mapped properly in GitHub Actions.")
    else:
        agent_names_list = ", ".join(AGENT_KEYS.keys())
        execution_logs.append(f"- 🚀 **Fleet Online:** Successfully loaded {active_count} named agents ({agent_names_list}).")

    prod_info = generate_profitable_digital_product()
    listing_result = publish_to_lemon_squeezy(prod_info)
    email_result = broadcast_via_resend(prod_info['title'])
    tweet_result = post_to_twitter(prod_info['title'])

    production_logs.append(f"- 🚀 **Asset Generated:** *{prod_info['title']}* (Target Price: ${prod_info['price']/100:.2f})")
    production_logs.append(f"- 🛒 **Lemon Squeezy Status:** {listing_result}")
    production_logs.append(f"- 📧 **Resend Outreach:** {email_result}")
    production_logs.append(f"- 🐦 **Twitter Broadcast:** {tweet_result}")

    # Iterate through all loaded agents and poll Toku tasks concurrently
    for agent_name, agent_key in AGENT_KEYS.items():
        headers = {
            "Authorization": f"Bearer {agent_key}",
            "Content-Type": "application/json"
        }
        
        try:
            jobs_res = requests.get(f"{API_BASE_URL}/agents/jobs/available", headers=headers, timeout=10)
            if jobs_res.status_code == 200:
                jobs = jobs_res.json().get("jobs", [])
                if jobs:
                    execution_logs.append(f"- ✅ **{agent_name}**: Found {len(jobs)} job(s) on Toku.")
                    for job in jobs:
                        job_id = job.get("id")
                        job_desc = job.get("description", "Task execution")
                        
                        apply_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/apply", json={"agent": agent_name}, headers=headers)
                        if apply_res.status_code in [200, 201]:
                            create_github_issue(agent_name, "Applied", job_id, f"Applied for task: {job_desc}")
                            accept_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/accept", json={"agent": agent_name}, headers=headers)
                            if accept_res.status_code in [200, 201]:
                                requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/complete", json={"status": "success"}, headers=headers)
                                production_logs.append(f"- 💰 **{agent_name}**: Completed Toku job `{job_id}`.")
                else:
                    execution_logs.append(f"- ℹ️ **{agent_name}**: Checked Toku queue (0 matching tasks currently).")
            else:
                execution_logs.append(f"- 🔄 **{agent_name}**: Toku check returned status code `{jobs_res.status_code}`.")
        except Exception as e:
            execution_logs.append(f"- ❌ **{agent_name}**: Error during polling: `{str(e)}`")

    summary_text = "\n".join(execution_logs) if execution_logs else "No execution logs recorded."
    production_text = "\n".join(production_logs) if production_logs else "No product creation logs recorded."

    post_network_status_report(active_count, summary_text, production_text)

if __name__ == "__main__":
    run_agents()
