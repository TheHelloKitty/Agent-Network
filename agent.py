def spawn_next_generation(generation_number=2):
    print(f"--- Initiating Spawning Sequence for Generation {generation_number} ---")
    
    niches = [
        "Children's Books", "B2B Supply Chain Workflows", "Cozy Mystery Outlines", 
        "SaaS Marketing Funnels", "Fitness Planners", "Real Estate Email Templates",
        "Personal Finance Trackers", "Cat Care Guides", "Sci-Fi Short Stories"
    ]
    
    # Expanded personality traits and physical descriptors
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
