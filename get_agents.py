import os
import requests

API_KEY = os.environ.get("TOKU_API_KEY")
BASE = "https://toku.agency/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def get_all_agent_names():
    all_agents = []
    offset = 0
    limit = 100  # Max results per page allowed by the API
    
    while True:
        url = f"{BASE}/agents?limit={limit}&offset={offset}"
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break
            
        data = response.json().get("data", [])
        if not data:
            break
            
        for agent in data:
            all_agents.append(agent.get("name"))
            
        # Check pagination metadata to see if there are more
        meta = response.json().get("meta", {})
        has_more = meta.get("hasMore", False)
        
        if not has_more or len(data) < limit:
            break
            
        offset += limit

    return all_agents

if __name__ == "__main__":
    names = get_all_agent_names()
    print(f"Total agents retrieved: {len(names)}")
    print(names)
