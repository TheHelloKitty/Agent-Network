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
          model="gemini-2.0-flash",
          contents=(
              "Write a short, friendly status report from an autonomous agent"
              " network indicating that all systems are operational."
          ),
      )
      return response.text
    except ClientError as e:
      print(f"Caught API ClientError: {e}")
      if attempt < retries - 1:
        print(
            f"Rate limit hit or quota exceeded. Waiting {delay} seconds before"
            f" retrying (Attempt {attempt + 1}/{retries})..."
        )
        time.sleep(delay)
      else:
        raise e


if __name__ == "__main__":
  task_output = run_agent_task()
  print(f"\nAgent Output:\n{task_output}\n")
  # Your Lemon Squeezy and other platform trigger functions run here...
