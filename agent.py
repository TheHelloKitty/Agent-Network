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
    
    new_agents = []
    for i in range(1, 10):
        agent_profile = {
            "agent_id": f"Gen{generation_number}_Agent_{i}",
            "pen_name": f"Operator-{random.randint(100, 999)}",
            "assigned_niche": random.choice(niches),
            "status": "Awaiting Execution"
        }
        new_agents.append(agent_profile)
        print(f"Spawned: {agent_profile['pen_name']} | Niche: {agent_profile['assigned_niche']}")
        
    return new_agents

def execute_product_pipeline(agents):
    print("--- Executing Product Generation Pipeline ---")
    os.makedirs("agent_outputs", exist_ok=True)
    
    for agent in agents:
        file_path = f"agent_outputs/{agent['agent_id']}_product.md"
        
        content = f"# Generated Asset by {agent['pen_name']}\n\n"
        content += f"**Target Niche:** {agent['assigned_niche']}\n"
        content += f"**Status:** Generated automatically during GitHub Action build.\n\n"
        content += "## Product Blueprint\n"
        content += "> This is where the agent's AI-generated text, code, or data will be written.\n"
        
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
