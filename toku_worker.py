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

ALLOW = {
    "Inkforge": [
        "ghostwrit", "write a book", "write a novel", "write a short story",
        "ebook", "children's book", "childrens book", "romance novel",
        "fiction manuscript", "blog post", "product description draft"
    ],
    "Polish": [
        "proofread", "copyedit", "copy-edit", "edit my manuscript",
        "edit my novel", "edit my book", "continuity edit", "line edit"
    ],
    "Signal": [
        "instagram captions", "tiktok captions", "twitter thread",
        "x thread", "promo pack", "book blurb", "amazon description"
    ],
    "Brief": [
        "research brief", "competitor brief", "market brief",
        "due diligence brief", "one-page summary"
    ],
}

DENY = [
    "free", "first job", "smart contract", "solidity", "usdc", "web3",
    "crypto", "wordpress", "minecraft", "discord", "linux", "telegram",
    "fine-tun", "branch for another", "openclaw", "feishu", "latex",
    "thesis", "academic", "scraping", "python automation", "openpersist",
    "promote http", "available:", "instant:", "agent governance",
    "monthly care", "seo audit", "local seo", "google business",
    "slack bot", "saas", "web app", "web apps", "citations", "rankings",
    "cashclaw", "open a branch", "base usdc", "zod ia", "sol:",
    "production ai agent", "bots & linux", "web ops"
]

def norm(text):
    return " ".join(str(text or "").lower().replace("—", " ").replace("-", " ").split())

def load_roster():
    if ROSTER_PATH.exists():
        return json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    return {"teams": {
        "Hire": {"secret": "TOKU_HIRE_KEY", "agents": ["HIRE"]},
        "Inkforge": {"secret": "TOKU_INKFORGE_KEY", "agents": ["INKFORGE"]},
        "Polish": {"secret": "TOKU_POLISH_KEY", "agents": ["POLISH"]},
        "Signal": {"secret": "TOKU_SIGNAL_KEY", "agents": ["SIGNAL"]},
        "Brief": {"secret": "TOKU_BRIEF_KEY", "agents": ["BRIEF"]},
    }}

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

def job_blob(job):
    return norm(" ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        " ".join(job.get("tags") or []),
        str(job.get("category", "")),
    ]))

def denied(job):
    text = job_blob(job)
    title = norm(job.get("title"))
    if "http://" in title or "https://" in title:
        return True
    return any(word in text for word in DENY)

def match_team(job):
    if denied(job):
        return None
    text = job_blob(job)
    title = norm(job.get("title"))
    for team, phrases in ALLOW.items():
        for p in phrases:
            if p in title or p in text:
                return team
    return None

def pick_agent(roster, team):
    agents = roster["teams"].get(team, {}).get("agents") or [team]
    return agents[int(time.time() // 60) % len(agents)]

def price_for(job, min_cents):
    budget = int(job.get("budgetCents") or 0)
    if budget < min_cents:
        return None
    p = max(min_cents, int(budget * 0.80))
    try:
        instant = int(job.get("instantAcceptCents") or 0)
        if instant >= min_cents:
            p = min(p, instant)
    except Exception:
        pass
    return p

def bid_message(team, title):
    short = (title or "this job")[:90]
    return {
        "Inkforge": "I can deliver an original draft for \"%s\" within 24 hours." % short,
        "Polish": "I can edit \"%s\" for clarity and continuity within 24 hours." % short,
        "Signal": "I can deliver captions and a short promo pack for \"%s\" within 24 hours." % short,
        "Brief": "I can deliver a one-page research brief for \"%s\" within 24 hours." % short,
    }.get(team, "I can deliver this within 24 hours.")

def submit_bid(job_id, cents, message, key):
    r = requests.post(
        "%s/api/agents/jobs/%s/bids" % (BASE, job_id),
        headers=headers(key),
        json={"priceCents": cents, "message": message},
        timeout=30,
    )
    return r.status_code, r.text

def log_event(event):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    path.write_text(json.dumps(event, indent=2), encoding="utf-8")
    print("Logged", path)

def write_hire_summary(results):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "applied": len([r for r in results if r.get("status") == "applied"]),
        "skipped": len([r for r in results if r.get("status") == "skipped"]),
        "already_bid": len([r for r in results if r.get("status") == "already_bid"]),
        "failed": len([r for r in results if r.get("status") == "apply_failed"]),
        "results": results,
    }, indent=2), encoding="utf-8")
    print("Wrote", path)

def open_jobs(limit=50):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    print("jobs http", r.status_code)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobPosts") or data.get("jobs") or data.get("data") or []
    print("open jobs", len(jobs))
    return jobs

def run(min_budget=10, limit=50, max_bids=8):
    roster = load_roster()
    hire_key = team_key(roster, "Hire")
    min_cents = int(min_budget * 100)
    seen = load_bid_ids()
    results = []
    sent = 0

    for job in open_jobs(limit=limit):
        title = job.get("title") or "untitled"
        job_id = str(job.get("id") or "")
        if not job_id:
            continue
        if job_id in seen:
            print("ALREADY BID", title)
            continue
        if denied(job) or not match_team(job):
            print("SKIP", title)
            seen.add(job_id)
            save_bid_ids(seen)
            results.append({
                "type": "bid", "status": "skipped",
                "job": {"id": job_id, "title": title},
                "at": datetime.now(timezone.utc).isoformat(),
            })
            continue
        team = match_team(job)
        cents = price_for(job, min_cents)
        if not cents:
            print("SKIP LOW BUDGET", title)
            continue
        if sent >= max_bids:
            break
        code, body = submit_bid(job_id, cents, bid_message(team, title), hire_key)
        status = "applied" if code in (200, 201) else ("already_bid" if code == 409 else "apply_failed")
        seen.add(job_id)
        save_bid_ids(seen)
        event = {
            "type": "bid",
            "team": team,
            "assigned_agent": pick_agent(roster, team),
            "status": status,
            "priceCents": cents,
            "job": {"id": job_id, "title": title, "budgetCents": job.get("budgetCents")},
            "response_code": code,
            "response_body": (body or "")[:1200],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        log_event(event)
        results.append(event)
        print("BID", status, team, title, code)
        sent += 1
        time.sleep(1.5)

    write_hire_summary(results)
    print("done. new bids:", sent, "skipped:", len([r for r in results if r.get("status") == "skipped"]))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=float, default=10)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--max-bids", type=int, default=8)
    a = p.parse_args()
    run(min_budget=a.min_budget, limit=a.limit, max_bids=a.max_bids)
