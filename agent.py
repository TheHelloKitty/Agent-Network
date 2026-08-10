import os
import json
import urllib.request
import urllib.error
import urllib.parse

def create_gumroad_product(name, description, price_cents):
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        print("Error: GUMROAD_ACCESS_TOKEN not found in environment variables.")
        return None

    url = "https://api.gumroad.com/v2/products"
    
    payload = {
        "access_token": token,
        "name": name,
        "description": description,
        "price": price_cents,
        "published": "true"
    }
    
    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            print(f"SUCCESS: Created product '{name}' on Gumroad!")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error: {e.code} - {error_body}")
    except Exception as e:
        print(f"Error: {str(e)}")
        
    return None

if __name__ == "__main__":
    create_gumroad_product(
        name="Swarm Digital Asset Package", 
        description="Generated automatically by your agent network.", 
        price_cents=1000
    )
