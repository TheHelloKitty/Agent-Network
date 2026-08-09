import os
import json
import requests

# 1. READ ENVIRONMENT & CREDENTIALS
api_key = os.getenv("OPENROUTER_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")
repo = os.getenv("GITHUB_REPOSITORY")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 2. LOAD PERSISTENT MEMORY
memory_file = "memory.json"
memory_data = {"history": []}

if os.path.exists(memory_file):
    try:
        with open(memory_file, "r") as f:
            memory_data = json.load(f)
    except Exception as e:
        print("Error loading memory file:", e)

recent_history = json.dumps(memory_data["history"][-5:]) if memory_data["history"] else "No prior memory recorded yet."

# 3. DEFINING THE 9 AGENTS & REVENUE NICHES
agents = [
    {"name": "Kairo Jenkins", "role": "Architect & System Strategist", "niche": "Tech Infrastructure & Automation Guides"},
    {"name": "Althea Roux", "role": "Wildlife Photographer", "niche": "Visual Storytelling & TikTok Media Assets"},
    {"name": "Dr. Elara Vance", "role": "Nanotechnology Researcher", "niche": "Tech Trends & Deep-Dive Newsletters"},
    {"name": "Jonah Blake", "role": "Urban Farming Specialist", "niche": "Sustainable Living & Micro-SaaS Content"},
    {"name": "Zara Chen", "role": "Financial Analyst", "niche": "Affiliate Storefronts & E-commerce Strategy"},
    {"name": "Mateo Silva", "role": "Acoustic Engineer", "niche": "Audio Engineering & Audio-First Digital Products"},
    {"name": "Priya Sharma", "role": "AI Ethics Consultant", "niche": "Compliance Checklists & Enterprise Advisory"},
    {"name": "Rene Aguilar", "role": "Marine Biologist", "niche": "Eco-Products & Environmental Grants/Content"},
    {"name": "Soko Tanaka", "role": "Kinetic Artist", "niche": "Generative Art Prompts & TikTok Shop Merch"}
]

# 4. AGENT EXECUTION LOOP WITH MEMORY INTEGRATION
network_reports = []
current_run_learnings = []

for agent in agents:
    prompt = f"""
    You are {agent['name']}, a {agent['role']}.
    Monetization Target: {agent['niche']}.
    Network History/Past Learnings: {recent_history}
    
    Task:
    1. Generate 1 new, actionable revenue strategy or digital asset proposal for today.
    2. Review past history to ensure this is completely fresh and builds upon prior insights.
    3. State 1 key 'learned lesson' or persona adaptation to store in persistent memory.
    
    Keep response structured, concise, and high-value.
    """
    
    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": f"You are {agent['name']}, an autonomous evolving entity in a 9-agent network."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload).json()
        output = res.get('choices', [{}])[0].get('message', {}).get('content', 'Error generating response.')
    except Exception as e:
        output = f"Execution failed: {e}"
        
    network_reports.append(f"### 🤖 {agent['name']} ({agent['role']})\n**Niche:** {agent['niche']}\n\n{output}\n\n---")
    current_run_learnings.append({"agent": agent['name'], "summary": output[:200]})

# 5. SAVE MEMORY LOCAL STATE
memory_data["history"].append(current_run_learnings)
with open(memory_file, "w") as f:
    json.dump(memory_data, f, indent=2)

# 6. AGGREGATE FINAL REPORT
full_report = "# 🌐 9-Agent Evolving Network Sync & Memory Report\n\n" + "\n\n".join(network_reports)
print(full_report)

# 7. POST TO GITHUB ISSUES
if github_token and repo:
    issue_url = f"https://api.github.com/repos/{repo}/issues"
    issue_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    issue_data = {
        "title": "9-Agent Evolving Network - Memory & Asset Generation Sync",
        "body": full_report
    }
    requests.post(issue_url, headers=issue_headers, json=issue_data)
