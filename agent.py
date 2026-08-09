import os
import random
import logging

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

def spawn_next_generation(generation_number=2):
    print(f"--- Initiating Spawning Sequence for Generation {generation_number} ---")
    
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
            "agent_id": f"Gen{generation_number}_Agent_{i}",
            "pen_name": f"Operator-{random.randint(100, 999)}",
            "assigned_niche": random.choice(niches),
            "personality": random.choice(personalities),
            "tone": random.choice(tones),
            "physical_profile": random.choice(physical_traits),
            "status": "Awaiting Execution"
        }
        new_agents.append(agent_profile)
        print(f"Spawned: {agent_profile['pen_name']} | Niche: {agent_profile['assigned_niche']} | Persona: {agent_profile['personality']}")
        
    return new_agents

def execute_product_pipeline(agents):
    print("--- Executing Product Generation Pipeline ---")
    os.makedirs("agent_outputs", exist_ok=True)
    
    for agent in agents:
        file_path = f"agent_outputs/{agent['agent_id']}_product.md"
        
        content = f"# Generated Asset by {agent['pen_name']}\n\n"
        content += f"**Target Niche:** {agent['assigned_niche']}\n"
        content += f"**Personality:** {agent['personality']}\n"
        content += f"**Tone:** {agent['tone']}\n"
        content += f"**Profile / Quirks:** {agent['physical_profile']}\n\n"
        content += "## Product Blueprint\n"
        content += "> Created automatically with distinct persona governance.\n"
        
        with open(file_path, "w") as file:
            file.write(content)
            
        print(f"SUCCESS: {agent['pen_name']} generated asset -> {file_path}")

# --- MAIN SWARM EXECUTION LOOP ---
step_count = 0
task_identifier = "Daily_Agent_Generation_Pipeline"
task_completed = False

while not task_completed:
    step_count += 1
    
    swarm_governor.check_circuit_breaker(step_count, task_identifier)
    
    print(f"\n[SYSTEM] Executing Swarm Step {step_count}...")
    
    active_swarm = spawn_next_generation(generation_number=2)
    swarm_governor.track_token_usage(tokens_consumed=4500)
    
    execute_product_pipeline(active_swarm)
    swarm_governor.track_token_usage(tokens_consumed=12500)
    
    print("\n[SYSTEM] Daily Generation and Execution Complete.")
    task_completed = True
