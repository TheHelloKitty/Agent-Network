import os
import requests

# Retrieve your existing API key from environment variables
api_key = os.environ.get("LEMONSQUEEZY_API_KEY")

if api_key:
    url = "https://api.lemonsqueezy.com/v1/stores"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        stores = response.json().get("data", [])
        print(f"Successfully connected! Found {len(stores)} store(s):")
        for store in stores:
            store_id = store.get("id")
            store_name = store.get("attributes", {}).get("name")
            print(f"-> Store Name: {store_name} | Store ID: {store_id}")
    else:
        print(f"API Error: {response.status_code} - {response.text}")
else:
    print("LEMONSQUEEZY_API_KEY environment variable is missing.")
