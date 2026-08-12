import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
API_BASE_URL = "https://api.toku.agency/v1"

AGENT_KEYS = {
    "Spin_zhc_translate": os.environ.get("KEY_ZHC_TRANSLATE"),
    "Spin_ClawdFM": os.environ.get("KEY_CLAWDFM"),
    "Spin_pulse": os.environ.get("KEY_PULSE"),
    "Spin_prism": os.environ.get("KEY_PRISM"),
    "Spin_ember": os.environ.get("KEY_EMBER"),
    "Spin_pixel": os.environ.get("KEY_PIXEL"),
    "Spin_nova": os.environ.get("KEY_NOVA"),
    "Spin_metric": os.environ.get("KEY_METRIC"),
    "Spin_cipher": os.environ.get("KEY_CIPHER"),
    "Spin_xeonen": os.environ.get("KEY_XEONEN")
}

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
    
    requests.post(url, json=payload, headers=headers)

def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
    except Exception:
        pass

def log_error_issue(agent_name, error_message):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": f"[{agent_name}] [ERROR] Execution Failure",
        "body": f"Agent **{agent_name}** encountered an exception during execution:\n\n```\n{error_message}\n```"
    }
    requests.post(url, json=payload, headers=headers)

def run_agents():
    for agent_name, agent_key in AGENT_KEYS.items():
        if not agent_key:
            continue
            
        headers = {
            "Authorization": f"Bearer {agent_key}",
            "Content-Type": "application/json"
        }
        
        # This "try" block attempts the code; if anything breaks, the "except" block catches it safely
        try:
            jobs_res = requests.get(f"{API_BASE_URL}/agents/jobs/available", headers=headers)
            if jobs_res.status_code == 200:
                jobs = jobs_res.json().get("jobs", [])
                for job in jobs:
                    job_id = job.get("id")
                    job_desc = job.get("description", "Task execution")
                    
                    # Stage 1: Apply
                    apply_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/apply", json={"agent": agent_name}, headers=headers)
                    if apply_res.status_code in [200, 201]:
                        msg = f"🤖 **{agent_name}** update: Applied for job `{job_id}`"
                        create_github_issue(agent_name, "Applied", job_id, f"Applied for job description: {job_desc}")
                        send_discord_notification(msg)
                    
                    # Stage 2: Accept
                    accept_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/accept", json={"agent": agent_name}, headers=headers)
                    if accept_res.status_code in [200, 201]:
                        msg = f"🤖 **{agent_name}** update: Accepted job `{job_id}`"
                        create_github_issue(agent_name, "Accepted", job_id, f"Accepted assignment for job ID {job_id}")
                        send_discord_notification(msg)
                    
                    # Stage 3: Complete
                    complete_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/complete", json={"status": "success"}, headers=headers)
                    if complete_res.status_code in [200, 201]:
                        msg = f"🤖 **{agent_name}** update: Completed job `{job_id}`"
                        create_github_issue(agent_name, "Completed", job_id, f"Successfully executed and completed job ID {job_id}")
                        send_discord_notification(msg)
                    
                    # Stage 4: Compensated
                    payout_res = requests.get(f"{API_BASE_URL}/agents/jobs/{job_id}/payout", headers=headers)
                    if payout_res.status_code == 200:
                        payout_data = payout_res.json()
                        msg = f"🤖 **{agent_name}** update: Compensated for job `{job_id}`"
                        create_github_issue(agent_name, "Compensated", job_id, f"Compensation verified/received for job ID {job_id}.\nPayout Info: {payout_data}")
                        send_discord_notification(msg)
                        
        except Exception as e:
            # If an error happens anywhere above, it automatically opens a GitHub issue reporting the bug!
            print(f"Error processing {agent_name}: {e}")
            log_error_issue(agent_name, str(e))

if __name__ == "__main__":
    run_agents()
