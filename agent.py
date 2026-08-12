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

def create_github_issue(agent_name, title, details):
    if not GITHUB_TOKEN or not REPO_NAME:
        return
    
    url = f"https://api.github.com/repos/{REPO_NAME}/issues"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "title": f"[{agent_name}] {title}",
        "body": details
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"Successfully created GitHub issue for {agent_name}")
    else:
        print(f"Failed to create issue for {agent_name}: {response.text}")

def search_and_process_jobs():
    headers = {
        "Authorization": f"Bearer {TOKU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    for agent_name, agent_key in AGENT_KEYS.items():
        if not agent_key:
            continue
            
        # 1. Authenticate / Verify Agent
        verify_payload = {
            "name": agent_name,
            "agent_api_key": agent_key
        }
        
        try:
            auth_res = requests.post(f"{API_BASE_URL}/agents/verify", json=verify_payload, headers=headers)
            if auth_res.status_code not in [200, 201]:
                print(f"Authentication failed for {agent_name}")
                continue
                
            print(f"Authenticated: {agent_name}. Searching for available jobs...")
            
            # 2. Search/Poll for available jobs assigned to this agent
            jobs_res = requests.get(f"{API_BASE_URL}/agents/jobs/available", params={"agent": agent_name}, headers=headers)
            
            if jobs_res.status_code == 200:
                jobs = jobs_res.json().get("jobs", [])
                if not jobs:
                    print(f"No active jobs found for {agent_name}.")
                    continue
                    
                for job in jobs:
                    job_id = job.get("id")
                    job_desc = job.get("description", "Routine task execution")
                    print(f"Found job {job_id} for {agent_name}. Processing...")
                    
                    # 3. Accept and Execute Job
                    complete_res = requests.post(f"{API_BASE_URL}/agents/jobs/{job_id}/complete", json={"agent": agent_name}, headers=headers)
                    if complete_res.status_code in [200, 201]:
                        print(f"Job {job_id} completed successfully by {agent_name}!")
                        create_github_issue(
                            agent_name, 
                            f"Job Completed: {job_id}", 
                            f"Agent **{agent_name}** successfully searched, claimed, and completed job `{job_id}`.\n\nDescription: {job_desc}"
                        )
                    else:
                        print(f"Failed to complete job {job_id}: {complete_res.text}")
            else:
                print(f"Could not fetch jobs for {agent_name}: {jobs_res.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error processing {agent_name}: {e}")

if __name__ == "__main__":
    if not TOKU_API_KEY:
        print("Error: TOKU_API_KEY environment variable is missing.")
    else:
        search_and_process_jobs()
