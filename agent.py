import os
import requests

# --- ENVIRONMENT CONFIGURATION ---
YOU_API_KEY = os.environ.get("YOU_API_KEY")

def search_you_com(query_string: str):
    """Uses the You.com Search API to execute a live query."""
    if not YOU_API_KEY:
        print("❌ Error: YOU_API_KEY environment variable is missing.")
        return None
    
    url = "https://api.you.com/search"
    headers = {
        "X-API-Key": YOU_API_KEY
    }
    params = {
        "query": query_string
    }
    
    try:
        print(f"🔍 Querying You.com for: '{query_string}'...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Successfully retrieved search results!")
            return data
        else:
            print(f"❌ API Error [{response.status_code}]: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred during You.com request: {str(e)}")
    
    return None

if __name__ == "__main__":
    # Test query for your agents
    query = "$100"
    results = search_you_com(query)
    if results:
        print("\n--- Search Results Preview ---")
        print(str(results)[:500] + "...\n[Content Truncated]")
