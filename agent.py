import json

# Load or define your Toku fleet directly in your agent initialization
FLEET_CONFIG_PATH = "fleet_config.json"

def load_toku_fleet():
    try:
        with open(FLEET_CONFIG_PATH, "r") as f:
            fleet_data = json.load(f)
            return fleet_data["agents"]
    except FileNotFoundError:
        # Fallback dictionary or inline registration if JSON isn't local yet
        return []

class TokuFleetManager:
    def __init__(self):
        self.agents = load_toku_fleet()
        print(f"Loaded {len(self.agents)} agents into the Toku Fleet.")

# Example instantiation inside agent.py
if __name__ == "__main__":
    manager = TokuFleetManager()
