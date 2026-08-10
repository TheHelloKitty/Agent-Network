import os
import sys
from google import genai
import resend
import requests

# 1. Load secrets from GitHub environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

if not GEMINI_API_KEY:
  print("Error: GEMINI_API_KEY is missing.")
  sys.exit(1)

# 2. Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def run_agent_task():
  print("Running agent task with Gemini...")
  # Ask Gemini to generate a status update or summary using an active model
  response = client.models.generate_content(
      model="gemini-2.5-flash",
      contents=(
          "Write a short, friendly status report from an autonomous agent network"
          " indicating that all systems are operational."
      ),
  )
  return response.text


def send_discord_alert(message):
  if not DISCORD_WEBHOOK_URL:
    print("Discord webhook URL not found, skipping alert.")
    return

  payload = {"content": f"🤖 **Agent Network Alert**:\n{message}"}
  response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
  if response.status_code == 204:
    print("Discord alert sent successfully!")
  else:
    print(f"Failed to send Discord alert: {response.status_code}")


def send_email_report(report_text):
  if not RESEND_API_KEY:
    print("Resend API key not found, skipping email.")
    return

  resend.api_key = RESEND_API_KEY
  params = {
      "from": "Agent Network <onboarding@resend.dev>",
      "to": ["delivered@resend.dev"],  # Update to your email when ready
      "subject": "Agent Network Daily Report",
      "html": f"<p>{report_text}</p>",
  }

  try:
    email = resend.Emails.send(params)
    print("Email report sent successfully via Resend!")
  except Exception as e:
    print(f"Failed to send email: {e}")


if __name__ == "__main__":
  # Execute agent tasks and trigger integrations
  task_output = run_agent_task()
  print(f"\nAgent Output:\n{task_output}\n")

  send_discord_alert(task_output)
  send_email_report(task_output)
