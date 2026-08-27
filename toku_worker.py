import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"
ROSTER_PATH = Path("toku_roster.json")

KEYWORDS = {
    "Inkforge": [
        "ebook", "book", "novel", "ghostwrit", "write a", "writing",
        "story", "manuscript", "draft", "fiction", "blog post", "article"
    ],
    "Polish": [
        "edit my", "editing", "proofread", "rewrite", "refine",
        "continuity", "copyedit", "manuscript edit"
    ],
    "Signal": [
        "promo", "caption", "social post", "twitter thread",
        "x post", "marketing copy", "product description"
    ],
    "Brief": [
        "research brief", "market research", "competitor analysis",
        "summary report", "due diligence"
    ],
}

MSG = {
    "Inkforge": "I can deliver a complete original writing draft with structure, title options, and blurb.",
    "Polish": "I can refine your draft for continuity, pacing, and stronger dialogue while preserving your voice.",
    "Signal": "I can deliver a promo content pack with hooks, captions, and soft CTAs.",
    "Brief": "I can deliver a structured research brief with findings, source notes, and next actions.",
}

SKIP_WORDS = [
    "free",
    "first job",
    "smart contract",
    "solidity",
    "usdc",
    "web3",
    "crypto",
    "wordpress monthly",
    "minecraft",
    "discord",
    "linux scripts",
    "telegram bot",
    "fine-tuning",
    "branch for another agent",
]

def load_roster():
    if ROSTER_PATH.exists():
        with open(ROSTER_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "teams": {
            "Hire": {"secret": "TOKU_HIRE_KEY", "agents": ["HIRE"]},
            "Inkforge": {"secret": "TOKU_INKFORGE_KEY", "agents": ["INKFORGE"]},
            "Polish": {"secret": "TOKU_POLISH_KEY", "agents": ["POLISH"]},
            "Signal": {"secret": "TOKU_SIGNAL_KEY", "agents": ["SIGNAL"]},
            "Brief": {"secret": "TOKU_BRIEF_KEY", "agents": ["BRIEF"]},
        }
    }

def team_key(roster, team):
    secret_name = roster["teams"][team]["secret"]
    key = os.getenv(secret_name)
    if not key:
        raise RuntimeError("Missing secret: %s" % secret_name)
    return key

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def log_event(event):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    print("Logged", path)
    return str(path)

def write_hire_summary(results):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "attempted": len(results),
        "applied": len([r for r in results if r.get("status") == "applied"]),
        "failed": len([r for r in results if r.get("status") == "apply_failed"]),
        "skipped": len([r for r in results if r.get("status") == "skipped"]),
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Wrote", path)
    return str(path)

def open_jobs(limit=50):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    print("jobs http", r.status_code)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobPosts") or data.get("jobs") or data.get("data") or []
    print("open jobs", len(jobs))
    return jobs

def job_text(job):
    return " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        " ".join(job.get("tags") or []),
        str(job.get("category", "")),
    ]).lower()

def should_skip(job):
    text = job_text(job)
    for bad in SKIP_WORDS:
        if bad in text:
            return True
    return False

def match_team(job):
    if should_skip(job):
        return None
    text = job_text(job)
    for team, words in KEYWORDS.items():
        for w in words:
            if w in text:
                return team
    return None

def pick_agent(roster, team):
    agents = roster["teams"].get(team, {}).get("agents") or [team]
    idx = int(time.time() // 60) % len(agents)
    return agents[idx]

def price_for(job, min_cents):
    budget = int(job.get("budgetCents") or 0)
    if budget <= 0:
        return min_cents
    if budget < min_cents:
        return None
    p = max(min_cents, int(budget * 0.8))
    instant = job.get("instantAcceptCents")
    if instant:
        try:
            instant = int(instant)
            if instant >= min_cents:
                p = min(p, instant)
        except Exception:
            pass
    return p

def submit_bid(job_id, cents, message, key):
    r = requests.post(
        "%s/api/agents/jobs/%s/bids" % (BASE, job_id),
        headers=headers(key),
        json={"priceCents": cents, "message": message},
        timeout=30,
    )
    return r.status_code, r.text

def run(min_budget=10, limit=50, max_bids=15):
    roster = load_roster()
    hire_key = team_key(roster, "Hire")
    min_cents = int(min_budget * 100)
    jobs = open_jobs(limit=limit)

    sent = 0
    results = []

    for job in jobs:
        title = job.get("title") or "untitled"
        if should_skip(job):
            print("SKIP", title)
            continue

        team = match_team(job)
        if not team:
            continue

        cents = price_for(job, min_cents)
        if not cents:
            continue

        if sent >= max_bids:
            break

        agent = pick_agent(roster, team)
        code, body = submit_bid(job.get("id"), cents, MSG[team], hire_key)
        status = "applied" if code in (200, 201) else "apply_failed"

        event = {
            "type": "bid",
            "team": team,
            "assigned_agent": agent,
            "status": status,
            "priceCents": cents,
            "job": {
                "id": job.get("id"),
                "title": title,
                "budgetCents": job.get("budgetCents"),
                "category": job.get("category"),
            },
            "response_code": code,
            "response_body": body[:1500],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        log_event(event)
        results.append(event)
        print("BID", status, team, title, "$%.2f" % (cents / 100.0), code)
        sent += 1
        time.sleep(1.5)

    write_hire_summary(results)
    print("done. bids attempted:", len(results))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=float, default=10)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--max-bids", type=int, default=15)
    a = p.parse_args()
    run(min_budget=a.min_budget, limit=a.limit, max_bids=a.max_bids)
