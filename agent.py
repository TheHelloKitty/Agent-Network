import os
import sys
import time
from google import genai
from google.genai.errors import ClientError
import resend
import requests

# 1. Load secrets from GitHub environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")

if not GEMINI_API_KEY:
  print("Error: GEMINI_API_KEY is missing.")
  sys.exit(1)

# 2. Initialize the Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)


def run_agent_task(retries=5, delay=55):
  print("Running agent task with Gemini...")
  for attempt in range(retries):
    try:
      response = client.models.generate_content(
          model="gemini-3.5-flash",
          contents=(
              "Write a short, detailed operational status report from your"
              " autonomous agent network. Include clear sections for actual"
              " execution baselines versus estimated performance projections"
              " across your revenue pipelines."
          ),
      )
      return response.text
    except ClientError as e:
      print(f"Caught API ClientError: {e}")
      if attempt < retries - 1:
        time.sleep(delay)
      else:
        raise e


def create_github_issue(report_text):
  if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
    return
  url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues"
  headers = {
      "Authorization": f"Bearer {GITHUB_TOKEN}",
      "Accept": "vnd.github+json",
  }
  payload = {
      "title": f"Agent Run Report - {time.strftime('%Y-%m-%d %H:%M:%S')}",
      "body": f"### Autonomous Agent Network Report\n\n{report_text}",
  }
  requests.post(url, json=payload, headers=headers)


def send_discord_alert(message):
  if not DISCORD_WEBHOOK_URL:
    return
  payload = {"content": f"🤖 **Revenue Agent Swarm Report**:\n{message}"}
  requests.post(DISCORD_WEBHOOK_URL, json=payload)


def send_email_report(report_text):
  if not RESEND_API_KEY:
    return
  resend.api_key = RESEND_API_KEY
  params = {
      "from": "Agent Network <onboarding@resend.dev>",
      "to": ["delivered@resend.dev"],
      "subject": "Agent Network Execution Report",
      "html": f"<p>{report_text.replace(chr(10), '<br>')}</p>",
  }
  try:
    resend.Emails.send(params)
  except Exception as e:
    print(f"Failed to send email: {e}")


if __name__ == "__main__":
  task_output = run_agent_task()
  print(f"\nAgent Output:\n{task_output}\n")

  create_github_issue(task_output)
  send_discord_alert(task_output)
  send_email_report(task_output)
