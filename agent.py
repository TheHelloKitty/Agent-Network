import os
import requests
from coinbase.rest import RESTClient

# Initialize credentials
COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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

def check_paypal_connection():
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        return "PayPal credentials not configured."
    try:
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(url, auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET), headers=headers, data=data)
        
        if response.status_code == 200:
            return "Connected Successfully (Sandbox Access Token Acquired)"
        else:
            return f"Failed to connect: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error connecting to PayPal: {e}"

def send_discord_alert(message):
    if not DISCORD_WEBHOOK_URL:
        print("Discord Webhook URL not configured.")
        return
    payload = {"content": message}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            print("Discord alert sent successfully.")
        else:
            print(f"Failed to send Discord alert: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Discord alert: {e}")

if __name__ == "__main__":
    print("Running Revenue Agent Swarm...")
    
    balance_report = get_coinbase_balance()
    paypal_status = check_paypal_connection()
    
    report_message = (
        "🤖 **Revenue Agent Swarm Status Report**\n"
        f"• **Coinbase Status** -> {balance_report}\n"
        f"• **PayPal Status** -> {paypal_status}"
    )
    
    print(report_message)
    send_discord_alert(report_message)
