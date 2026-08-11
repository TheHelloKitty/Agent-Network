import os
import requests

TOKU_API_KEY = os.environ.get("TOKU_API_KEY")
API_BASE_URL = "https://api.toku.agency/v1"  # Adjust base URL if needed based on your configuration

def fetch_agent_metrics():
    headers = {
        "Authorization": f"Bearer {TOKU_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/agents/performance", headers=headers)
        response.raise_for_status()
        return response.json().get("agents", [])
    except requests.exceptions.RequestException as e:
        print(f"Error communicating with Toku API: {e}")
        return []

def rank_top_earners(agents):
    # Sort agents by total lifetime earnings or payout volume descending
    sorted_agents = sorted(agents, key=lambda x: x.get("total_earnings", 0.0), reverse=True)
    
    print("\n--- TOP 10 TOKU EARNERS ---")
    for i, agent in enumerate(sorted_agents[:10], 1):
        name = agent.get("name", "Unknown Agent")
        earnings = agent.get("total_earnings", 0.0)
        success_rate = agent.get("success_rate", 0.0)
        tasks_completed = agent.get("tasks_completed", 0)
        
        print(f"{i}. {name} | Earned: ${earnings:,.2f} | Success Rate: {success_rate}% | Tasks: {tasks_completed}")

if __name__ == "__main__":
    if not TOKU_API_KEY:
        print("Error: TOKU_API_KEY environment variable is missing.")
    else:
        agent_data = fetch_agent_metrics()
        if agent_data:
            rank_top_earners(agent_data)
        else:
            print("No performance data returned from the API.")
