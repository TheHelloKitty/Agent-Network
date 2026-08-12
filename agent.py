DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

def send_discord_notification(message):
    if not DISCORD_WEBHOOK_URL:
        return
    requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
