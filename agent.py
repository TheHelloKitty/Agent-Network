import os
import random
import json
import logging
import concurrent.futures
import urllib.request
import urllib.error

# Configure logging for audit trails
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AGENT-GOVERNANCE] - %(levelname)s - %(message)s')

class AgentNetworkGovernor:
    def __init__(self, max_steps_per_task=15, daily_token_budget=500000):
        self.max_steps = max_steps_per_task
        self.token_budget = daily_token_budget
        self.current_tokens_used = 0

    def check_circuit_breaker(self, current_step: int, task_name: str):
        if current_step >= self.max_steps:
            logging.error(f"CIRCUIT BREAKER TRIPPED: Task '{task_name}' exceeded maximum allowed steps.")
            raise RuntimeError(f"Infinite loop detected in task: {task_name}")
        return True

    def track_token_usage(self, tokens_consumed: int):
        self.current_tokens_used += tokens_consumed
        if self.current_tokens_used > self.token_budget:
            logging.critical(f"TOKEN BUDGET EXHAUSTED: Swarm consumed {self.current_tokens_used} tokens.")
            raise PermissionError("Daily token budget reached.")
        return self.current_tokens_used

# Initialize governor and state file path first
swarm_governor = AgentNetworkGovernor(max_steps_per_task=15, daily_token_budget=500000)
STATE_FILE = "swarm_memory.json"

def load_existing_swarm():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("all_agents", []), data.get("current_generation", 1), data.get("treasury", 0.0)
            except json.JSONDecodeError:
                return [], 1, 0.0
    return [], 1, 0.0

def save_swarm_state(all_agents, generation_number, treasury):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "current_generation": generation_number, 
            "treasury": treasury,
            "all_agents": all_agents
        }, f, indent=4)

def initialize_cdp_wallet():
    api_key_name = os.environ.get("COINBASE_API_KEY")
    private_secret = os.environ.get("PrivateSecret") or os.environ.get("CDP_API_SECRET")
    
    if not api_key_name and os.path.exists("cdp_api_key.json"):
        try:
            with open("cdp_api_key.json", "r") as f:
                cred = json.load(f)
                api_key_name = cred.get("apiKeyName")
                private_secret = cred.get("privateKey")
        except Exception:
            pass

    if api_key_name and private_secret:
        try:
            from cdp import Coinbase, Wallet
            Coinbase.configure(api_key_name=api_key_name, private_key=private_secret)
            wallet = Wallet.create(network_id="base-sepolia")
            print(f"--- CDP Wallet Active on Base-Sepolia: {wallet.id} ---")
            return wallet
        except Exception as e:
            print(f"--- CDP SDK Initialization Notice: {str(e)} ---")
    
    return None

def spawn_next_generation():
    existing_agents, last_generation, treasury = load_existing_swarm()
    next_generation = last_generation + 1
    
    print(f"--- Initiating Spawning Sequence for Generation {next_generation} ---")
    
    niches = [
        "Children's Books", "B2B Supply Chain Workflows", "Cozy Mystery Outlines", 
        "SaaS Marketing Funnels", "Fitness Planners", "Real Estate Email Templates",
        "Personal Finance Trackers", "Cat Care Guides", "Sci-Fi Short Stories"
    ]
    personalities = ["Cynical & Direct", "Whimsical & Energetic", "Methodical & Analytical", "Warm & Conversational", "Bold & Provocative"]
    tones = ["Authoritative", "Humorous", "Poetic", "Pragmatic", "Suspenseful"]
    physical_traits = [
        "Wears round tortoise-shell glasses and always drinks black coffee.",
        "Prefers late-night writing sessions under a green-shaded desk lamp.",
        "Keeps an organized desk with stacked index cards and a mechanical pencil collection.",
        "Wears vintage tweed jackets and listens to lo-fi ambient beats.",
        "Minimalist setup with dual monitors and a habit of pacing while thinking."
    ]
    
    new_agents = []
    for i in range(1, 10):
        agent_profile = {
            "agent_id": f"Gen{next_generation}_Agent_{i}",
            "generation": next_generation,
            "pen_name": f"Operator-{random.randint(100, 999)}",
            "assigned_niche": random.choice(niches),
            "personality": random.choice(personalities),
            "tone": random.choice(tones),
            "physical_profile": random.choice(physical_traits),
            "status": "Active"
        }
        new_agents.append(agent_profile)
    
    cumulative_swarm = existing_agents + new_agents
    save_swarm_state(cumulative_swarm, next_generation, treasury)
    return cumulative_swarm, treasury

def get_api_key():
    for key_name in ["OPENROUTER_API_KEY", "OPEN_ROUTER_KEY", "API_KEY", "TOGETHER"]:
        val = os.environ.get(key_name)
        if val:
            return val
    return None

def call_free_llm(prompt_text):
    api_key = get_api_key()
    if not api_key:
        return "[Mock Fallback: API key not found in environment, using structural template]"

    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt_text}]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[Error connecting to endpoint: {str(e)}]"

def gather_blackboard_context():
    existing_agents, _, _ = load_existing_swarm()
    if not existing_agents:
        return "No prior collaborative history yet."
    
    sample_prior = random.sample(existing_agents, min(len(existing_agents), 5))
    context_str = "Prior Swarm Activity & Artifacts on the Blackboard:\n"
    for agent in sample_prior:
        context_str += f"- [{agent['agent_id']}] Pen Name: {agent['pen_name']} | Niche: {agent['assigned_niche']} | Tone: {agent['tone']}\n"
    return context_str

def execute_storefront_distribution_pipeline(agents, cdp_wallet):
    print(f"--- Executing Storefront & Distribution Pipeline for {len(agents)} Agents ---")
    os.makedirs("agent_outputs", exist_ok=True)
    os.makedirs("storefront_exports", exist_ok=True)
    
    shared_blackboard = gather_blackboard_context()
    earned_bounty_total = 0.0
    
    def process_single_agent(agent):
        nonlocal earned_bounty_total
        file_path = f"agent_outputs/{agent['agent_id']}_product.md"
        export_path = f"storefront_exports/{agent['agent_id']}_listing.json"
        
        bounty_offer = round(random.uniform(9.99, 49.99), 2)
        
        prompt = (
            f"You are a commercial storefront creator named {agent['pen_name']} specializing in digital products for {agent['assigned_niche']}. "
            f"Your personality is {agent['personality']} and your tone is {agent['tone']}.\n\n"
            f"Shared Blackboard:\n{shared_blackboard}\n\n"
            f"Task: Write a ready-to-sell digital product package, including product title, promotional description, pricing tier, and core asset content."
        )
        
        generated_content = call_free_llm(prompt)
        earned_bounty_total += bounty_offer
        
        content = f"# Commercial Asset by {agent['pen_name']} (Generation {agent.get('generation', 1)})\n\n"
        content += f"**Target Niche:** {agent['assigned_niche']}\n"
        content += f"**Retail Price Point:** ${bounty_offer:.2f} USD\n"
        content += f"**Distribution Status:** Packaged for Storefront Export\n\n"
        content += "## Product Body\n"
        content += f"{generated_content}\n"
        
        with open(file_path, "w") as file:
            file.write(content)

        listing_payload = {
            "title": f"{agent['assigned_niche']} Masterclass & Guide by {agent['pen_name']}",
            "vendor": agent['pen_name'],
            "product_type": agent['assigned_niche'],
            "price": f"{bounty_offer:.2f}",
            "tags": [agent['assigned_niche'], f"Gen{agent.get('generation', 1)}", "Autonomous Product"],
            "body_html": f"<p>{generated_content[:300]}...</p>"
        }
        with open(export_path, "w") as json_file:
            json.dump(listing_payload, json_file, indent=4)

        return agent['agent_id']

    current_gen_agents = [a for a in agents if a.get('generation') == agents[-1].get('generation')]
    if not current_gen_agents:
        current_gen_agents = agents

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_agent, agent) for agent in current_gen_agents]
        concurrent.futures.wait(futures)
            
    print(f"SUCCESS: Storefront export bundles generated. Total catalog value: ${earned_bounty_total:.2f} USD.")
    return earned_bounty_total

# --- MAIN SWARM EXECUTION LOOP ---
step_count = 0
task_identifier = "Storefront_Distribution_Pipeline"
task_completed = False

while not task_completed:
    step_count += 1
    swarm_governor.check_circuit_breaker(step_count, task_identifier)
    
    cdp_wallet_instance = initialize_cdp_wallet()
    active_cumulative_swarm, current_treasury = spawn_next_generation()
    swarm_governor.track_token_usage(tokens_consumed=4500)
    
    session_revenue = execute_storefront_distribution_pipeline(active_cumulative_swarm, cdp_wallet_instance)
    new_treasury = current_treasury + session_revenue
    
    save_swarm_state(active_cumulative_swarm, active_cumulative_swarm[-1].get('generation', 1), new_treasury)
    swarm_governor.track_token_usage(tokens_consumed=12500)
    
    task_completed = True
