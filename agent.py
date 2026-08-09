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

# 2. DEFINING THE 9 AGENTS & REVENUE NICHES
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

# 3. AGENT EXECUTION & SELF-IMPROVEMENT LOOP
network_reports = []

for agent in agents:
    prompt = f"""
    You are {agent['name']}, a {agent['role']}.
    Monetization Target: {agent['niche']}.
    
    Task:
    1. Generate 1 actionable, revenue-generating piece of content or digital asset proposal for today.
    2. Suggest 1 key improvement or 'learned adaptation' for your persona based on current trends.
    
    Keep response brief, structured, and high-value.
    """
    
    payload = {
        "model": "openrouter/free",
        "messages": [
            {"role": "system", "content": f"You are {agent['name']}. Your goal is to autonomously generate value and adapt your skillset."},
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload).json()
        output = res.get('choices', [{}])[0].get('message', {}).get('content', 'Error generating response.')
    except Exception as e:
        output = f"Execution failed: {e}"
        
    network_reports.append(f"### 🤖 {agent['name']} ({agent['role']})\n**Niche:** {agent['niche']}\n\n{output}\n\n---")

# 4. AGGREGATE FINAL REPORT
full_report = "# 🌐 9-Agent Network Autonomous Sync & Monetization Report\n\n" + "\n\n".join(network_reports)
print(full_report)

# 5. POST TO GITHUB ISSUES FOR REPOSITORY LOGGING
if github_token and repo:
    issue_url = f"https://api.github.com/repos/{repo}/issues"
    issue_headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    issue_data = {
        "title": "9-Agent Network Daily Batch Output & Evolution Log",
        "body": full_report
    }
    requests.post(issue_url, headers=issue_headers, json=issue_data)
