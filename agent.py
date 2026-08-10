import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

def post_to_webhook(webhook_url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url, 
        data=data, 
        headers={"Content-Type": "application/json"}, 
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status == 204 or response.status == 200
    except Exception as e:
        print(f"Webhook broadcast error: {e}")
    return False

if __name__ == "__main__":
    print("Initializing automated traffic and channel publisher...")
    
    webhook_url = os.environ.get("DISCORD_OR_SLACK_WEBHOOK_URL")
    batch_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    marketing_broadcast = {
        "content": f"🚨 **New High-Ticket Asset Drop!** ({batch_timestamp})\n"
                   "Our autonomous agent swarm has successfully published the latest versioned production kits across Gumroad and Lemon Squeezy.\n\n"
                   "💡 **Featured Kits Live Now:**\n"
                   "• Autonomous B2B Industrial Lead Gen Swarm Kit\n"
                   "• Commercial Lighting Retrofit ROI Suite\n"
                   "• Automated E-Commerce Storefront Migration Kit\n"
                   "• High-Converting Cold Email & Outreach Library\n\n"
                   "🔗 Check your store dashboards for direct checkout URLs and start driving traffic!"
    }
    
    print("\n" + "="*40)
    print("📢 TRAFFIC BROADCAST PREVIEW")
    print("="*40)
    print(marketing_broadcast["content"])
    print("="*40)
    
    if webhook_url:
        success = post_to_webhook(webhook_url, marketing_broadcast)
        if success:
            print("✅ Broadcast successfully sent to connected channels!")
        else:
            print("❌ Failed to deliver broadcast via webhook.")
    else:
        print("ℹ️ No webhook URL configured (DISCORD_OR_SLACK_WEBHOOK_URL). Run preview printed above.")
