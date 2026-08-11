import os
import requests

API_KEY = os.environ.get("TOKU_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
ISSUE_NUMBER = os.environ.get("ISSUE_NUMBER")

BASE = "https://toku.agency/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def get_all_agent_names():
    all_agents = []
    offset = 0
    limit = 100
    
    while True:
        url = f"{BASE}/agents?limit={limit}&offset={offset}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            break
        data = response.json().get("data", [])
        if not data:
            break
        for agent in data:
            all_agents.append(agent.get("name"))
        meta = response.json().get("meta", {})
        if not meta.get("hasMore", False) or len(data) < limit:
            break
        offset += limit
    return all_agents

def post_to_github(agent_list):
    if not GITHUB_TOKEN or not REPOSITORY or not ISSUE_NUMBER:
        print("GitHub environment variables missing.")
        return
        
    comment_body = f"### 🤖 Retrieved Agent List ({len(agent_list)} total)\n" + "\n".join([f"- {name}" for name in agent_list])
    
    url = "https://api.github.com/repos/{}/issues/{}/comments".format(REPOSITORY, ISSUE_NUMBER)
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(url, headers=headers, json={"body": comment_body})
    if response.status_code == 201:
        print("Successfully posted agent list to GitHub issue!")
    else:
        print("Failed to post comment: {}".format(response.text))

if __name__ == "__main__":
    names = get_all_agent_names()
    print("Total agents retrieved: {}".format(len(names)))
    post_to_github(names)
