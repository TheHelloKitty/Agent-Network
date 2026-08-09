import os
import random
import json
import logging
import concurrent.futures

# Configure logging for audit trails
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AGENT-GOVERNANCE] - %(levelname)s - %(message)s')

class AgentNetworkGovernor:
    def __init__(self, max_steps_per_task=15, daily_token_budget=500000):
        self.max_steps = max_steps_per_task
        self.token_budget = daily_token_budget
        self.current_tokens_used = 0

    def check_circuit_breaker(self, current_step: int, task_name: str):
        if current_step >= self.max_steps:
            logging.error(f"CIRCUIT BREAKER TRIPPED: Task '{task_name}' exceeded maximum allowed steps ({self.max_steps}).")
            raise RuntimeError(f"Infinite loop detected in task: {task_name}")
        return True

    def track_token_usage(self, tokens_consumed: int):
        self.current_tokens_used += tokens_consumed
        if self.current_tokens_used > self.token_budget:
            logging.critical(f"TOKEN BUDGET EXHAUSTED: Swarm consumed {self.current_tokens_used} tokens.")
            raise PermissionError("Daily token budget reached.")
        return self.current_tokens_used

# Initialize the global governor
swarm_governor = AgentNetworkGovernor(max_steps_per_task=15, daily_token_budget=500000)

STATE_FILE = "swarm_memory.json"

def load_existing_swarm():
    """Loads all previously running agents from persistent memory."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                data = json.load(f)
                return data.get("all_agents", []), data.get("current_generation", 1)
            except json.JSONDecodeError:
                return [], 1
    return [], 1

def save_swarm_state(all_agents, generation_number):
    """Saves the cumulative active swarm state back to persistent storage."""
    with open(STATE_FILE, "w") as f:
        json.dump({"current_generation": generation_number, "all_agents": all_agents}, f, indent=4)

def spawn_next_generation():
    """Loads existing agents, increments generation, spawns 9 new ones, and accumulates them."""
    existing_agents, last_generation = load_existing_swarm()
    next_generation = last_generation + 1
    
    print(f"--- Initiating Spawning Sequence for Generation {next_generation} ---")
    print(f"Loaded {len(existing_agents)} active agents from previous generations.")
    
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
        print(f"Spawned & Added: {agent_profile['agent_id']} ({agent_profile['pen_name']}) | Niche: {agent_profile['assigned_niche']}")
    
    cumulative_swarm = existing_agents + new_agents
    save_swarm_state(cumulative_swarm, next_generation)
    
    print(f"Total Cumulative Active Swarm Size: {len(cumulative_swarm)} agents running.")
    return cumulative_swarm

def execute_product_pipeline_concurrently(agents):
    print(f"--- Executing Concurrent Product Generation for {len(agents)} Agents ---")
    os.makedirs("agent_outputs", exist_ok=True)
    
    def process_single_agent(agent):
        file_path = f"agent_outputs/{agent['agent_id']}_product.md"
        content = f"# Generated Asset by {agent['pen_name']} (Generation {agent.get('generation', 1)})\n\n"
        content += f"**Target Niche:** {agent['assigned_niche']}\n"
        content += f"**Personality:** {agent['personality']}\n"
        content += f"**Tone:** {agent['tone']}\n"
        content += f"**Profile / Quirks:** {agent['physical_profile']}\n"
        content += f"**Status:** {agent['status']}\n\n"
        content += "## Product Blueprint\n"
        content += "> Executed concurrently via multi-threaded swarm architecture.\n"
        
        with open(file_path, "w") as file:
            file.write(content)
        return agent['agent_id']

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_single_agent, agent) for agent in agents]
        concurrent.futures.wait(futures)
            
    print(f"SUCCESS: All {len(agents)} active agents completed execution concurrently.")

# --- MAIN SWARM EXECUTION LOOP ---
step_count = 0
task_identifier = "Cumulative_Agent_Generation_Pipeline"
task_completed = False

while not task_completed:
    step_count += 1
    
    swarm_governor.check_circuit_breaker(step_count, task_identifier)
    
    print(f"\n[SYSTEM] Executing Swarm Step {step_count}...")
    
    active_cumulative_swarm = spawn_next_generation()
    swarm_governor.track_token_usage(tokens_consumed=4500)
    
    execute_product_pipeline_concurrently(active_cumulative_swarm)
    swarm_governor.track_token_usage(tokens_consumed=12500 * (len(active_cumulative_swarm) // 9))
    
    print(f"\n[SYSTEM] Cumulative Generation Run Complete. Total Active Fleet: {len(active_cumulative_swarm)} agents.")
    task_completed = True
