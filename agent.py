import os
import sys
import time
from coinbase.rest import RESTClient
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

# Coinbase API credentials (set these in GitHub Secrets as well)
COINBASE_API_KEY = os.environ.get("COINBASE_API_KEY")
COINBASE_API_SECRET = os.environ.get("COINBASE_API_SECRET")

if not GEMINI_API_KEY:
  print("Error: GEMINI_API_KEY is missing.")
  sys.exit(1)

# 2. Initialize Clients
client = genai.Client(api_key=GEMINI_API_KEY)


def get_real_coinbase_balances():
  """Fetches real account balances from Coinbase Advanced API."""
  if not COINBASE_API_KEY or not COINBASE_API_SECRET:
    return "Coinbase API credentials not configured in environment variables."

  try:
    cb_client = RESTClient(
        api_key=COINBASE_API_KEY, api_secret=COINBASE_API_SECRET
    )
    accounts_response = cb_client.get_accounts()

    balance_summary = []
    # Parse accounts safely using dot notation / dict structure from SDK
    accounts = getattr(accounts_response, "accounts", [])
    for acc in accounts:
      currency = getattr(acc, "currency", "UNKNOWN")
      available = getattr(acc, "available_balance", {})
      if isinstance(available, dict):
        val = available.get("value", "0")
      else:
        val = getattr(acc, "balance", "0")

      # Only list non-zero or active balances to keep it clean
      balance_summary.append(f"- {currency}: {val}")

    if not balance_summary:
      return "Connected successfully, but no active asset balances found."

    return "\n".join(balance_summary)
  except Exception as e:
    return f"Could not fetch live Coinbase data: {str(e)}"


def run_agent_estimation(real_balances_text, retries=5, delay=55):
  """Asks Gemini to analyze real data and provide estimates/projections."""
  prompt = f"""
    You are an autonomous operations and financial agent. 
    Here is the REAL-TIME account data fetched directly from Coinbase:
    {real_balances_text}

    Based on these real figures, write a detailed operational status report that includes:
    1. Real vs. Estimated breakdown.
    2. Estimated performance projections or yield forecasts for the next cycle.
    3. Active task and pipeline queues.
    Keep it professional and structured.
    """

  print("Generating agent estimation report with Gemini...")
  for attempt in range(retries):
    try:
      response = client.models.generate_content(
          model="gemini-3.5-flash", contents=prompt
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
      "title": f"Real & Estimated Report - {time.strftime('%Y-%m-%d %H:%M:%S')}",
      "body": f"### Hybrid Agent Report (Real + Estimated)\n\n{report_text}",
  }
  requests.post(url, json=payload, headers=headers)


def send_discord_alert(message):
  if not DISCORD_WEBHOOK_URL:
    return
  payload = {"content": f"🤖 **Hybrid Report (Real/Estimated)**:\n{message}"}
  requests.post(DISCORD_WEBHOOK_URL, json=payload)


def send_email_report(report_text):
  if not RESEND_API_KEY:
    return
  resend.api_key = RESEND_API_KEY
  params = {
      "from": "Agent Network <onboarding@resend.dev>",
      "to": ["delivered@resend.dev"],
      "subject": "Hybrid Agent Execution Report",
      "html": f"<p>{report_text.replace(chr(10), '<br>')}</p>",
  }
  try:
    resend.Emails.send(params)
  except Exception as e:
    print(f"Failed to send email: {e}")


if __name__ == "__main__":
  # 1. Grab actual numbers from Coinbase
  real_data = get_real_coinbase_balances()

  # 2. Feed real numbers into Gemini to generate estimates and analysis
  task_output = run_agent_estimation(real_data)
  print(f"\nAgent Output:\n{task_output}\n")

  # 3. Distribute reports
  create_github_issue(task_output)
  send_discord_alert(task_output)
  send_email_report(task_output)
