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
    
    task_completed = True # <--- Stops the loop immediately after 1 generation
