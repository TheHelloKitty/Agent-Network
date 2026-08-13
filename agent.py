import os
import requests

# Load environment variables for the agent network
LEMON_SQUEEZY_API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
LEMON_SQUEEZY_STORE_ID = os.getenv("LEMON_SQUEEZY_STORE_ID")

def fetch_store_data():
    if not LEMON_SQUEEZY_API_KEY or not LEMON_SQUEEZY_STORE_ID:
        print("Missing Lemon Squeezy credentials in environment variables.")
        return None

    url = f"https://api.lemonsqueezy.com/v1/stores/{LEMON_SQUEEZY_STORE_ID}"
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}"
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        store_data = response.json().get("data", {})
        print(f"Successfully connected to store: {store_data.get('attributes', {}).get('name')}")
        return store_data
    else:
        print(f"Error fetching store: {response.status_code} - {response.text}")
        return None

def main():
    # Main agent execution loop integration
    print("Initializing agent network...")
    store_info = fetch_store_data()
    # Add your remaining agent execution logic here

if __name__ == "__main__":
    main()
