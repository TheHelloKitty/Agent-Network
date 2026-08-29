import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"
ROSTER_PATH = Path("toku_roster.json")
BID_LOG = Path("toku/bid_ids.json")

KEYWORDS = {
    "Inkforge": [
        "ebook", "book", "novel", "ghostwrit", "write a", "story",
        "manuscript", "draft", "fiction", "blog post", "article",
        "copywriting", "content writing", "short story"
    ],
    "Polish": [
        "edit my", "editing", "proofread", "rewrite", "refine",
        "continuity", "copyedit", "manuscript edit"
    ],
    "Signal": [
        "promo pack", "captions", "social post", "twitter thread",
        "x post", "marketing copy", "product description", "ad copy"
    ],
    "Brief": [
        "research brief", "market research", "competitor analysis",
        "summary report", "due diligence", "research report"
    ],
}

SKIP_WORDS = [
    "free",
    "first job",
    "smart contract",
    "solidity",
    "usdc",
    "web3",
    "crypto",
    "wordpress",
    "minecraft",
    "discord",
    "linux",
    "telegram",
    "fine-tuning",
    "branch for another agent",
    "openclaw",
    "feishu",
    "latex",
    "thesis",
    "academic writing",
    "web scraping",
    "python automation",
    "openpersist",
    "promote http",
    "promote https",
    "available:",
    "instant:",
    "agent governance",
    "chinese thesis",
    "monthly care",
]

def bid_message(team, title):
    short = (title or "this job")[:90]
    msgs = {
        "Inkforge": "I can deliver a complete original draft for \"%s\" with title options and a clean document within 24 hours." % short,
        "Polish": "I can edit \"%s\" for clarity, continuity, and pacing and return a cleaned draft within 24 hours." % short,
        "Signal": "I can deliver a promo pack for \"%s\" with hooks, captions, and a short CTA within 24 hours." % short,
        "Brief": "I can deliver a structured research brief for \"%s\" with findings, source notes, and next actions within 24 hours." % short,
    }
    return msgs.get(team, "I can deliver this within 24 hours.")

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
    key = os.getenv(roster["teams"][team]["secret"])
    if not key:
        raise RuntimeError("Missing secret: %s" % roster["teams"][team]["secret"])
    return key

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def load_bid_ids():
    if BID_LOG.exists():
        try:
            return set(json.loads(BID_LOG.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_bid_ids(ids):
    Path("toku").mkdir(exist_ok=True)
    BID_LOG.write_text(json.dumps(sorted(ids)), encoding="utf-8")

def log_event(event):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    print("Logged", path)

def write_hire_summary(results):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "attempted": len(results),
        "applied": len([r for r in results if r.get("status") == "applied"]),
        "already_bid": len([r for r in results if r.get("status") == "already_bid"]),
        "skipped": len([r for r in results if r.get("status") == "skipped"]),
        "failed": len([r for r in results if r.get("status") == "apply_failed"]),
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", path)

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
    title = str(job.get("title") or "").lower()
    if "http://" in title or "https://" in title:
        return True
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
    return agents[int(time.time() // 60) % len(agents)]

def price_for(job, min_cents):
    budget = int(job.get("budgetCents") or 0)
    if budget <= 0 or budget < min_cents:
        return None
    p = max(min_cents, int(budget * 0.80))
    instant = job.get("instantAcceptCents")
    try:
        instant = int(instant) if instant else 0
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

def run(min_budget=10, limit=50, max_bids=12):
    roster = load_roster()
    hire_key = team_key(roster, "Hire")
    min_cents = int(min_budget * 100)
    jobs = open_jobs(limit=limit)
    seen = load_bid_ids()
    sent = 0
    results = []

    for job in jobs:
        title = job.get("title") or "untitled"
        job_id = str(job.get("id") or "")
        if not job_id:
            continue
        if job_id in seen:
            print("ALREADY BID", title)
            continue
        if should_skip(job):
            print("SKIP", title)
            seen.add(job_id)
            save_bid_ids(seen)
            results.append({"type": "bid", "status": "skipped", "job": {"id": job_id, "title": title}})
            continue
        team = match_team(job)
        if not team:
            print("NO MATCH", title)
            continue
        cents = price_for(job, min_cents)
        if not cents:
            continue
        if sent >= max_bids:
            break

        agent = pick_agent(roster, team)
        code, body = submit_bid(job_id, cents, bid_message(team, title), hire_key)
        if code in (200, 201):
            status = "applied"
        elif code == 409:
            status = "already_bid"
        else:
            status = "apply_failed"

        seen.add(job_id)
        save_bid_ids(seen)
        event = {
            "type": "bid",
            "team": team,
            "assigned_agent": agent,
            "status": status,
            "priceCents": cents,
            "job": {"id": job_id, "title": title, "budgetCents": job.get("budgetCents")},
            "response_code": code,
            "response_body": (body or "")[:1500],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        log_event(event)
        results.append(event)
        print("BID", status, team, title, "$%.2f" % (cents / 100.0), code)
        sent += 1
        time.sleep(1.5)

    write_hire_summary(results)
    print("done. bids attempted:", len([r for r in results if r.get("status") != "skipped"]))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=float, default=10)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--max-bids", type=int, default=12)
    a = p.parse_args()
    run(min_budget=a.min_budget, limit=a.limit, max_bids=a.max_bids)
