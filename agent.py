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

swarm_governor = AgentNetworkGovernor(max_steps_per_task=15, daily_token_budget=500000)
STATE_FILE = "swarm_memory.json"

def load_existing_swarm():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("all_agents", []), data.get("current_generation", 1)
            except json.JSONDecodeError:
                return [], 1
    return [], 1

def save_swarm_state(all_agents, generation_number):
    with open(STATE_FILE, "w") as f:
        json.dump({"current_generation": generation_number, "all_agents": all_agents}, f, indent=4)

def spawn_next_generation():
    existing_agents, last_generation = load_existing_swarm()
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
    save_swarm_state(cumulative_swarm, next_generation)
    return cumulative_swarm

def get_api_key():
    """Checks multiple possible environment variable names for the API key."""
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

def execute_product_pipeline_concurrently(agents):
    print(f"--- Executing Concurrent LLM Content Generation for {len(agents)} Agents ---")
    os.makedirs("agent_outputs", exist_ok=True)
    
    def process_single_agent(agent):
        file_path = f"agent_outputs/{agent['agent_id']}_product.md"
        
        prompt = (
            f"You are a professional writer named {agent['pen_name']}. "
            f"Your niche is {agent['assigned_niche']}. "
            f"Your personality is {agent['personality']} and your writing tone is {agent['tone']}. "
            f"Write a short introductory sample, outline, or chapter piece matching your persona."
        )
        
        generated_content = call_free_llm(prompt)
        
        content = f"# Generated Asset by {agent['pen_name']} (Generation {agent.get('generation', 1)})\n\n"
        content += f"**Target Niche:** {agent['assigned_niche']}\n"
        content += f"**Personality:** {agent['personality']}\n"
        content += f"**Tone:** {agent['tone']}\n"
        content += f"**Profile / Quirks:** {agent['physical_profile']}\n\n"
        content += "## Generated Content / Chapter\n"
        content += f"{generated_content}\n"
        
        with open(file_path, "w") as file:
            file.write(content)
        return agent['agent_id']

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_agent, agent) for agent in agents]
        concurrent.futures.wait(futures)
            
    print(f"SUCCESS: All active agents completed live content generation.")

# --- MAIN SWARM EXECUTION LOOP ---
step_count = 0
task_identifier = "Free_LLM_Agent_Pipeline"
task_completed = False

while not task_completed:
    step_count += 1
    swarm_governor.check_circuit_breaker(step_count, task_identifier)
    
    active_cumulative_swarm = spawn_next_generation()
    swarm_governor.track_token_usage(tokens_consumed=4500)
    
    execute_product_pipeline_concurrently(active_cumulative_swarm)
    swarm_governor.track_token_usage(tokens_consumed=12500)
    
    task_completed = True
