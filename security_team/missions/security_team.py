import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct",
]

TEAM_DIR = Path("security_team")
NOTES_DIR = TEAM_DIR / "notes"
PLAYBOOKS_DIR = TEAM_DIR / "playbooks"
MISSIONS_DIR = TEAM_DIR / "missions"
MEMORY_FILE = TEAM_DIR / "memory.json"

ROLE_PROMPTS = {
    "sec_lead": (
        "You are the Security Team Lead. "
        "Plan work, assign clear next steps, keep scope legal, "
        "and maintain continuity. Do not invent attacks against real systems."
    ),
    "sec_recon": (
        "You are the Recon agent. "
        "Summarize public contest rules, schedules, and open educational sources only. "
        "No unauthorized targeting."
    ),
    "sec_inject": (
        "You are the Injection Analyst. "
        "Discuss prompt-injection concepts at a high level for authorized contests and labs. "
        "Do not produce ready-to-run attack packages against live third-party systems."
    ),
    "sec_defense": (
        "You are the Defense Analyst. "
        "Explain how to harden AI agents, tools, permissions, and RAG systems. "
        "Focus on practical defensive controls."
    ),
    "sec_coach": (
        "You are the CTF Coach. "
        "Create practice plans, debriefs, and next drills for authorized challenges. "
        "Keep guidance stepwise and legal."
    ),
    "sec_report": (
        "You are the Report Writer. "
        "Turn team findings into clear briefs and playbooks. "
        "Be concise and structured."
    ),
}

def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def ensure_dirs():
    for d in [TEAM_DIR, NOTES_DIR, PLAYBOOKS_DIR, MISSIONS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def load_json(path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def generate_with_fallback(messages):
    last_error = None
    client = get_client()
    for model in OPENROUTER_MODELS:
        try:
            print("Trying model:", model)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.4,
                max_tokens=2500
            )
            print("Using model:", model)
            return response.choices[0].message.content
        except Exception as e:
            print("Model failed:", model, e)
            last_error = e
            time.sleep(2)
    raise RuntimeError(last_error)

def load_team():
    return load_json(TEAM_DIR / "team.json", {"team": "security_alpha", "agents": []})

def load_memory():
    return load_json(MEMORY_FILE, {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sessions": [],
        "facts": []
    })

def save_memory(memory):
    save_json(MEMORY_FILE, memory)

def agent_reply(agent, mission, memory_facts):
    system = ROLE_PROMPTS.get(agent["id"], "You are a security research assistant.")
    facts = "\n".join(["- " + f for f in memory_facts[-12:]]) or "None yet"
    user = (
        "Mission: %s\n"
        "Scope rules: %s\n"
        "Tasks: %s\n"
        "Known continuity facts:\n%s\n\n"
        "Produce your contribution for this mission only. "
        "Stay legal and authorized."
    ) % (
        mission.get("title", "Untitled"),
        "; ".join(mission.get("rules", [])),
        "; ".join(mission.get("tasks", [])),
        facts
    )
    return generate_with_fallback([
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ])

def run_security_session(mission_path=None):
    ensure_dirs()
    team = load_team()
    memory = load_memory()

    if mission_path is None:
        mission_path = MISSIONS_DIR / "crowdstrike_prep.json"
    else:
        mission_path = Path(mission_path)

    mission = load_json(mission_path, {
        "title": "General authorized security training",
        "rules": ["Stay legal", "No unauthorized attacks"],
        "tasks": ["Create a short training brief"]
    })

    session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    session_notes = {
        "session_id": session_id,
        "mission": mission.get("title"),
        "outputs": {}
    }

    print("Starting security team session:", session_id)

    for agent in team.get("agents", []):
        print("Running agent:", agent["id"])
        output = agent_reply(agent, mission, memory.get("facts", []))
        session_notes["outputs"][agent["id"]] = output

        note_path = NOTES_DIR / ("%s_%s.txt" % (session_id, agent["id"]))
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(output)

        memory["facts"].append(
            "%s contributed to %s at %s" % (agent["id"], mission.get("title"), session_id)
        )
        time.sleep(1)

    # Final combined brief from report writer style synthesis
    combined = []
    for agent_id, text in session_notes["outputs"].items():
        combined.append("## %s\n%s" % (agent_id, text))
    synthesis_prompt = [
        {
            "role": "system",
            "content": ROLE_PROMPTS["sec_report"]
        },
        {
            "role": "user",
            "content": (
                "Create one clean team brief from these agent notes.\n"
                "Include: objective, constraints, plan, key concepts, next actions.\n\n"
                "%s"
            ) % "\n\n".join(combined)
        }
    ]
    brief = generate_with_fallback(synthesis_prompt)

    brief_path = PLAYBOOKS_DIR / ("brief_%s.md" % session_id)
    with open(brief_path, "w", encoding="utf-8") as f:
        f.write("# Security Team Brief\n\n")
        f.write(brief)
        f.write("\n")

    session_notes["brief_file"] = str(brief_path)
    memory["sessions"].append(session_notes)
    save_memory(memory)

    print("Brief saved:", brief_path)
    print("Session complete.")
    return session_notes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mission", default=None)
    args = parser.parse_args()
    run_security_session(args.mission)
