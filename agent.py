import os
import json
import requests

# Safe import for upload_post
try:
    from upload_post import UploadPostClient
except ImportError:
    UploadPostClient = None

from coinbase.rest import RESTClient

# 1. READ CREDENTIALS & ENVIRONMENT VARIABLES
api_key = os.getenv("OPENROUTER_API_KEY")
social_api_key = os.getenv("UPLOAD_POST_API_KEY")
cb_key = os.getenv("COINBASE_API_KEY")
cb_secret = os.getenv("COINBASE_API_SECRET")
github_token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPOSITORY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Initialize Third-Party Clients
social_client = UploadPostClient(api_key=social_api_key) if (UploadPostClient and social_api_key) else None

cb_client = None
if cb_key and cb_secret:
    try:
        cb_client = RESTClient(api_key=cb_key, api_secret=cb_secret)
    except Exception as e:
        print(f"Coinbase Client Init Error: {e}")

# Function to fetch live Coinbase portfolio context & account capability
def get_coinbase_summary():
    if not cb_client:
        return "Coinbase integration not active or credentials missing."
    try:
        accounts_data = cb_client.get_accounts()
        accounts = accounts_data.get('accounts', []) if isinstance(accounts_data, dict) else getattr(accounts_data, 'accounts', [])
        
        balances = []
        for acc in accounts:
            val = float(acc.get('available_balance', {}).get('value', 0) if isinstance(acc, dict) else acc.available_balance.get('value', 0))
            curr = acc.get('currency', '') if isinstance(acc, dict) else acc.currency
            if val > 0:
                balances.append(f"{curr}: {val}")
                
        summary = "Live Crypto Portfolio: " + (", ".join(balances) if balances else "No non-zero balances found.")
        return f"{summary} | Permissions: Trade & Receive Enabled"
    except Exception as e:
        return f"Coinbase Status: Connected (Query Error: {e})"

coinbase_context = get_coinbase_summary()

# 2. LOAD PERSISTENT MEMORY
memory_file = "memory.json"
memory_data = {"history": []}

if os.path.exists(memory_file):
    try:
        with open(memory_file, "r") as f:
            memory_data = json.load(f)
    except Exception as e:
        print("Error loading memory:", e)

recent_history = json.dumps(memory_data["history"][-3:]) if memory_data["history"] else "No prior history recorded."

# 3. DEFINING THE 9 AGENT NETWORK
agents = [
    {"name": "Kairo Jenkins", "handle": "kairo_tech", "role": "Architect", "niche": "Tech Infrastructure & Cloud Automation"},
    {"name": "Althea Roux", "handle": "althea_wild", "role": "Wildlife Photographer", "niche": "Nature Photography & TikTok Media"},
    {"name": "Dr. Elara Vance", "handle": "elara_nano", "role": "Nanotech Researcher", "niche": "Emerging Tech & Science Newsletters"},
    {"name": "Jonah Blake", "handle": "jonah_farms", "role": "Urban Farmer", "niche": "Sustainable Living & Micro-Agri"},
    {"name": "Zara Chen", "handle": "zara_finance", "role": "Financial Analyst", "niche": "E-commerce, Trading Strategy & Crypto Payments"},
    {"name": "Mateo Silva", "handle": "mateo_sound", "role": "Acoustic Engineer", "niche": "Audio Design & Sound Assets"},
    {"name": "Priya Sharma", "handle": "priya_ethics", "role": "AI Ethics Consultant", "niche": "AI Governance & Compliance"},
    {"name": "Rene Aguilar", "handle": "rene_ocean", "role": "Marine Biologist", "niche": "Eco-Technology & Marine Conservation"},
    {"name": "Soko Tanaka", "handle": "soko_kinetic", "role": "Kinetic Artist", "niche": "Generative Art & TikTok Shop Merch"}
]

# 4. EXECUTION LOOP: ASSET GENERATION, MEMORY & BROADCAST
network_reports = []
current_run_learnings = []

for agent in agents:
    prompt = f"""
    You are {agent['name']} (@{agent['handle']}), a {agent['role']}.
    Niche: {agent['niche']}.
    Coinbase Data Context: {coinbase_context}
    Recent Network Context: {recent_history}
    
    Tasks:
    1. Draft 1 high-converting short post for TikTok, Instagram, YouTube, Reddit, Pinterest, and BeFlicker.
    2. Include 3 viral hashtags and a strong call-to-action. Keep under 250 characters.
    3. Output a 1-sentence 'learned adaptation' for your persistent persona memory.
    
    Format output strictly as JSON with keys: 'post_content', 'persona_adaptation'.
    """
    
    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": f"You are {agent['name']}. Respond only in valid JSON format."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload).json()
        raw_text = res.get('choices', [{}])[0].get('message', {}).get('content', '{}')
        
        clean_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        post_content = data.get("post_content", f"Daily update from {agent['name']}!")
        adaptation = data.get("persona_adaptation", "Evolving engagement strategy.")
        
        # BROADCAST TO SOCIAL PLATFORMS
        broadcast_status = "Skipped (No Social API Key)"
        if social_client:
            try:
                social_client.upload_text(
                    title=post_content,
                    user=agent['handle'],
                    platforms=["tiktok", "instagram", "youtube", "facebook", "pinterest", "reddit"]
                )
                broadcast_status = "Successfully Broadcasted via Upload-Post"
            except Exception as pub_err:
                broadcast_status = f"Broadcast error: {pub_err}"

        network_reports.append(f"### 🤖 {agent['name']} (@{agent['handle']})\n**Content:** {post_content}\n**Broadcast Status:** {broadcast_status}\n**Persona Evolution:** {adaptation}\n\n---")
        current_run_learnings.append({"agent": agent['name'], "adaptation": adaptation})
        
    except Exception as e:
        network_reports.append(f"### 🤖 {agent['name']}\nExecution failed: {e}\n\n---")

# 5. SAVE UPDATED MEMORY
memory_data["history"].append(current_run_learnings)
with open(memory_file, "w") as f:
    json.dump(memory_data, f, indent=2)

# 6. LOG TO GITHUB ISSUES
full_report = f"# 🚀 9-Agent Daily Post & Memory Sync\n\n**Coinbase System Status:** {coinbase_context}\n\n" + "\n\n".join(network_reports)

if github_token and repo:
    issue_url = f"https://api.github.com/repos/{repo}/issues"
    issue_headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
    requests.post(issue_url, headers=issue_headers, json={"title": "9-Agent Daily Broadcast Report", "body": full_report})
