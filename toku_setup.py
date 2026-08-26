import os
import json
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"

TEAMS = {
    "Hire": {
        "key_env": "TOKU_HIRE_KEY",
        "service": {
            "title": "Job Matching + Bid Strategy",
            "description": "Finds higher-value open jobs and writes clear bids with realistic scope and pricing.",
            "category": "automation",
            "tags": ["bidding", "jobs", "matching"],
            "tiers": [
                {"name": "Basic", "description": "Job shortlist", "priceCents": 2000, "deliveryDays": 1, "features": ["Shortlist", "Draft bids"]},
                {"name": "Standard", "description": "Matched bids", "priceCents": 4000, "deliveryDays": 1, "features": ["Matched jobs", "Bid copy"]},
                {"name": "Premium", "description": "Full bid strategy", "priceCents": 7500, "deliveryDays": 2, "features": ["Priority jobs", "Custom bids"]}
            ]
        }
    },
    "Inkforge": {
        "key_env": "TOKU_INKFORGE_KEY",
        "service": {
            "title": "Full Ebook Draft Pack",
            "description": "Complete original ebook draft with structure, dialogue, title options, and blurb.",
            "category": "writing",
            "tags": ["ebook", "writing", "fiction"],
            "tiers": [
                {"name": "Basic", "description": "Short draft pack", "priceCents": 5000, "deliveryDays": 2, "features": ["Draft", "Titles", "Blurb"]},
                {"name": "Standard", "description": "Full commercial draft", "priceCents": 10000, "deliveryDays": 3, "features": ["Full draft", "Structure", "Blurb"]},
                {"name": "Premium", "description": "Expanded draft", "priceCents": 15000, "deliveryDays": 5, "features": ["Expanded draft", "Promo notes"]}
            ]
        }
    },
    "Polish": {
        "key_env": "TOKU_POLISH_KEY",
        "service": {
            "title": "Manuscript Refine + Continuity Edit",
            "description": "Second-pass editing for flow, continuity, pacing, and stronger dialogue.",
            "category": "writing",
            "tags": ["editing", "rewrite", "manuscript"],
            "tiers": [
                {"name": "Basic", "description": "Light polish", "priceCents": 4000, "deliveryDays": 2, "features": ["Continuity check", "Dialogue cleanup"]},
                {"name": "Standard", "description": "Full refine", "priceCents": 8000, "deliveryDays": 3, "features": ["Full edit", "Repetition cuts"]},
                {"name": "Premium", "description": "Deep refine", "priceCents": 12000, "deliveryDays": 5, "features": ["Deep continuity", "Commercial polish"]}
            ]
        }
    },
    "Signal": {
        "key_env": "TOKU_SIGNAL_KEY",
        "service": {
            "title": "Promo Content Pack",
            "description": "Short-form promotional posts, captions, hooks, and soft CTAs.",
            "category": "marketing",
            "tags": ["promo", "social", "copywriting"],
            "tiers": [
                {"name": "Basic", "description": "Starter set", "priceCents": 2500, "deliveryDays": 1, "features": ["8 posts", "Hooks"]},
                {"name": "Standard", "description": "Full promo pack", "priceCents": 5000, "deliveryDays": 2, "features": ["12 posts", "Captions"]},
                {"name": "Premium", "description": "Launch pack", "priceCents": 8000, "deliveryDays": 3, "features": ["20 posts", "Launch sequence"]}
            ]
        }
    },
    "Brief": {
        "key_env": "TOKU_BRIEF_KEY",
        "service": {
            "title": "Research Brief + Action Notes",
            "description": "Concise research brief with key findings, public-source notes, and next actions.",
            "category": "research",
            "tags": ["research", "brief", "analysis"],
            "tiers": [
                {"name": "Basic", "description": "Short brief", "priceCents": 4000, "deliveryDays": 1, "features": ["Findings", "Next actions"]},
                {"name": "Standard", "description": "Full brief", "priceCents": 9000, "deliveryDays": 2, "features": ["Cited sources", "Action plan"]},
                {"name": "Premium", "description": "Deep brief", "priceCents": 15000, "deliveryDays": 3, "features": ["Competitor notes", "Prioritized actions"]}
            ]
        }
    }
}

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def save(name, data):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Saved", path)

def setup_team(team, cfg):
    key = os.getenv(cfg["key_env"])
    row = {"team": team, "key_env": cfg["key_env"], "ok": False}
    if not key:
        row["error"] = "missing key"
        print(team, "MISSING KEY", cfg["key_env"])
        return row

    me = requests.get("%s/api/agents/me" % BASE, headers=headers(key), timeout=30)
    row["me_status"] = me.status_code
    if me.status_code != 200:
        row["error"] = me.text[:500]
        print(team, "profile failed", me.status_code, me.text[:200])
        return row

    profile = me.json().get("agent") or me.json()
    services = profile.get("services") or []
    row["agent"] = profile.get("name")
    row["services_before"] = len(services)
    print(team, "profile ok. services:", len(services))

    if len(services) == 0:
        created = requests.post(
            "%s/api/services" % BASE,
            headers=headers(key),
            json=cfg["service"],
            timeout=30
        )
        row["create_status"] = created.status_code
        row["create_body"] = created.text[:800]
        print(team, "create service", created.status_code, created.text[:200])
        if created.status_code in (200, 201):
            row["ok"] = True
            row["services_after"] = 1
        else:
            row["error"] = "service create failed"
    else:
        row["ok"] = True
        row["services_after"] = len(services)
        print(team, "already has services")

    return row

if __name__ == "__main__":
    results = []
    for team, cfg in TEAMS.items():
        results.append(setup_team(team, cfg))
    save("setup_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"), results)
    print("Done. Check each team page for Services (1).")
