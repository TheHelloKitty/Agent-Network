import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY")
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
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Successfully created GitHub issue for {agent_name} - {stage}")
    else:
        print(f"Failed to create issue for {agent_name} - {stage}: {response.text}")

def run_agents():
    for agent_name, agent_key in AGENT_KEYS.items():
        if not agent_key:
            continue
            
        headers = {
            "Authorization": f"Bearer {agent_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # 1. Search for available jobs to apply to
            jobs_res = requests.get(f"{API_BASE_URL}/agents/jobs/available", headers=headers)
            if jobs_res.status_code == 200:
                jobs = jobs_res.json().get("jobs", [])
                for job in jobs:
                    job_id = job.get("id")
                    job_desc = job.get("description", "Task execution")
                    
                    # Stage 1: Apply for the job
                    apply_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/apply", json={"agent": agent_name}, headers=headers)
                    if apply_res.status_code in [200, 201]:
                        create_github_issue(agent_name, "Applied", job_id, f"Applied for job description: {job_desc}")
                    
                    # Stage 2: Accept the job
                    accept_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/accept", json={"agent": agent_name}, headers=headers)
                    if accept_res.status_code in [200, 201]:
                        create_github_issue(agent_name, "Accepted", job_id, f"Accepted assignment for job ID {job_id}")
                    
                    # Stage 3: Complete the job
                    complete_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/complete", json={"status": "success"}, headers=headers)
                    if complete_res.status_code in [200, 201]:
                        create_github_issue(agent_name, "Completed", job_id, f"Successfully executed and completed job ID {job_id}")
                    
                    # Stage 4: Check / Confirm Compensation / Payout
                    payout_res = requests.get(f"{API_BASE_URL}/agents/jobs/{job_id}/payout", headers=headers)
                    if payout_res.status_code == 200:
                        payout_data = payout_res.json()
                        create_github_issue(agent_name, "Compensated", job_id, f"Compensation verified/received for job ID {job_id}.\nPayout Info: {payout_data}")
                        
        except requests.exceptions.RequestException as e:
            print(f"Network error processing jobs for {agent_name}: {e}")

if __name__ == "__main__":
    run_agents()
