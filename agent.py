import time
import logging

# Configure logging for audit trails
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [AGENT-GOVERNANCE] - %(levelname)s - %(message)s')

class AgentNetworkGovernor:
    def __init__(self, max_steps_per_task=15, daily_token_budget=500000):
        self.max_steps = max_steps_per_task
        self.token_budget = daily_token_budget
        self.current_tokens_used = 0
        self.step_counter = 0

    def check_circuit_breaker(self, current_step: int, task_name: str):
        """Trips the circuit breaker if an agent loop exceeds safe execution steps."""
        if current_step >= self.max_steps:
            logging.error(f"CIRCUIT BREAKER TRIPPED: Task '{task_name}' exceeded maximum allowed steps ({self.max_steps}). Forcing shutdown of current pipeline.")
            raise RuntimeError(f"Infinite loop detected in task: {task_name}. Execution halted by safety governance.")
        return True

    def track_token_usage(self, tokens_consumed: int):
        """Monitors and restricts daily token burn across the active swarm."""
        self.current_tokens_used += tokens_consumed
        if self.current_tokens_used > self.token_budget:
            logging.critical(f"TOKEN BUDGET EXHAUSTED: Swarm consumed {self.current_tokens_used} tokens, breaching the limit of {self.token_budget}.")
            raise PermissionError("Daily token budget reached. Swarm execution throttled.")
        return self.current_tokens_used

# Initialize the global governor for the swarm
swarm_governor = AgentNetworkGovernor(max_steps_per_task=15, daily_token_budget=500000)
