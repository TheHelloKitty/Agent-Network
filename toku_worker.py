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
    "Inkforge": ["ebook", "book", "novel", "write", "writing", "story", "manuscript", "draft", "fiction", "blog", "article"],
    "Polish": ["edit", "editing", "proof", "rewrite", "refine", "continuity", "polish", "proofread"],
    "Signal": ["promo", "caption", "social", "post", "marketing", "content", "copy", "twitter"],
    "Brief": ["research", "brief", "market", "competitor", "analysis", "report", "summary"],
}

MSG = {
    "Inkforge": "I can deliver a complete original writing draft with clear structure, title options, and blurb.",
    "Polish": "I can refine your draft for continuity, pacing, and stronger dialogue while preserving your voice.",
    "Signal": "I can deliver a promo content pack with hooks, captions, and soft CTAs.",
    "Brief": "I can deliver a structured research brief with findings, source notes, and next actions.",
}

def load_roster():
    if not ROSTER_PATH.exists():
        raise RuntimeError("toku_roster.json missing")
    with open(ROSTER_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

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

def open_jobs(limit=50):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    print("jobs http", r.status_code)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobPosts") or data.get("jobs") or data.get("data") or []
    print("open jobs", len(jobs))
    return jobs

def match_team(job):
    text = " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        " ".join(job.get("tags") or []),
        str(job.get("category", "")),
    ]).lower()
    for team, words in KEYWORDS.items():
        for w in words:
            if w in text:
                return team
    cat = str(job.get("category", "")).lower()
    return {
        "writing": "Inkforge",
        "content": "Signal",
        "marketing": "Signal",
        "research": "Brief",
    }.get(cat)

def pick_agent(roster, team):
    agents = roster["teams"][team].get("agents") or []
    if not agents:
        return None
    # simple rotate by minute
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
        if sent >= max_bids:
            break
        team = match_team(job)
        if not team or team not in roster["teams"]:
            continue
        cents = price_for(job, min_cents)
        if not cents:
            continue

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
                "title": job.get("title"),
                "budgetCents": job.get("budgetCents"),
                "category": job.get("category"),
            },
            "response_code": code,
            "response_body": body[:1500],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        log_event(event)
        results.append(event)
        print("BID", status, team, agent, job.get("title"), "$%.2f" % (cents / 100.0), code)
        sent += 1
        time.sleep(1.5)

    summary = Path("toku") / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    with open(summary, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("done. bids attempted:", len(results))
    print("summary:", summary)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=float, default=10)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--max-bids", type=int, default=15)
    a = p.parse_args()
    run(min_budget=a.min_budget, limit=a.limit, max_bids=a.max_bids)
