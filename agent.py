import os
from coinbase.rest import RESTClient

# Initialize Coinbase credentials from environment variables
COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")

def get_coinbase_balance():
    if not COINBASE_API_KEY or not COINBASE_API_SECRET:
        return "Coinbase credentials not configured."
    try:
        client = RESTClient(api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET)
        accounts = client.get_accounts()
        balance_summary = []
        for account in accounts.get("accounts", []):
            available = account.get("available_balance", {})
            amount = available.get("value", "0")
            currency = account.get("currency", "")
            if float(amount) > 0:
                balance_summary.append(f"{currency}: {amount}")
        return ", ".join(balance_summary) if balance_summary else "All balances are $0.00"
    except Exception as e:
        return f"Error fetching Coinbase balance: {e}"

if __name__ == "__main__":
    print("Running Revenue Agent...")
    balance_report = get_coinbase_balance()
    print(f"Coinbase Status -> {balance_report}")
