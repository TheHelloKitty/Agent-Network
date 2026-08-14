import os
import requests

# Load environment variables for the agent network
LEMON_SQUEEZY_API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
LEMON_SQUEEZY_STORE_ID = os.getenv("LEMON_SQUEEZY_STORE_ID")

def create_initial_product():
    if not LEMON_SQUEEZY_API_KEY or not LEMON_SQUEEZY_STORE_ID:
        print("Missing Lemon Squeezy credentials in environment variables.")
        return None

    url = "https://api.lemonsqueezy.com/v1/products"
    headers = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}"
    }
    
    payload = {
        "data": {
            "type": "products",
            "attributes": {
                "name": "The Freelancer AI Automation Guide",
                "description": "An automated guide created by your agent network.",
                "price": 1900, # Price in cents ($19.00)
                "status": "published"
            },
            "relationships": {
                "store": {
                    "data": {
                        "type": "stores",
                        "id": str(LEMON_SQUEEZY_STORE_ID)
                    }
                }
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code in [200, 201]:
        product_data = response.json().get("data", {})
        print(f"Successfully created product: {product_data.get('attributes', {}).get('name')}")
        return product_data
    else:
        print(f"Error creating product: {response.status_code} - {response.text}")
        return None

def main():
    print("Initializing agent network and checking store activation...")
    create_initial_product()

if __name__ == "__main__":
    main()
