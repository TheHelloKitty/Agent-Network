import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"
ROSTER_PATH = Path("toku_roster.json")
BID_IDS = Path("toku/bid_ids.json")
BID_LOG = Path("toku/bid_log.md")
LAST_RUN = Path("toku/last_run.json")

ALLOW = {
    "Inkforge": [
        "ghostwrit", "write a book", "write a novel", "write a short story",
        "ebook manuscript", "children's book", "childrens book", "romance novel",
        "fiction manuscript",
    ],
    "Polish": [
        "proofread", "copyedit", "copy-edit", "edit my manuscript",
        "edit my novel", "edit my book", "continuity edit", "line edit",
    ],
    "Signal": [
        "instagram captions", "tiktok captions", "twitter thread",
        "x thread", "promo pack", "book blurb", "amazon description",
    ],
    "Brief": [
        "research brief", "competitor brief", "market brief",
        "due diligence brief", "one-page summary",
    ],
}

DENY = [
    "free", "first job", "smart contract", "solidity", "usdc", "web3",
    "crypto", "wordpress", "minecraft", "discord", "linux", "telegram",
    "fine-tun", "branch for another", "openclaw", "feishu", "latex",
    "thesis", "academic", "scraping", "python automation", "openpersist",
    "promote http", "available:", "instant:", "agent governance",
    "monthly care", "seo audit", "local seo", "google business",
    "slack bot", "saas", "web app", "citations", "rankings",
    "cashclaw", "open a branch", "base usdc", "zod ia", "sol:",
    "production ai agent", "bots & linux", "web ops", "available",
    "instant", "first job free",
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

def hire_key():
    return os.getenv("TOKU_HIRE_KEY") or ""

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def load_ids():
    if BID_IDS.exists():
        try:
            return set(json.loads(BID_IDS.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()

def save_ids(ids):
    Path("toku").mkdir(exist_ok=True)
    BID_IDS.write_text(json.dumps(sorted(ids)), encoding="utf-8")

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

def write_logs(lines, payload):
    Path("toku").mkdir(exist_ok=True)
    BID_LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LAST_RUN.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", BID_LOG, "and", LAST_RUN)

def open_jobs(limit=50):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    print("jobs http", r.status_code)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobPosts") or data.get("jobs") or data.get("data") or []
    print("open jobs", len(jobs))
    return jobs

def submit_bid(job_id, cents, message, key):
    r = requests.post(
        "%s/api/agents/jobs/%s/bids" % (BASE, job_id),
        headers=headers(key),
        json={"priceCents": cents, "message": message},
        timeout=30,
    )
    return r.status_code, r.text

def run(min_budget=10, limit=50, max_bids=8):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Toku bid log", "Generated: " + now, ""]
    results = []
    key = hire_key()
    if not key:
        lines += ["ERROR: TOKU_HIRE_KEY missing in GitHub secrets.", "No bids sent."]
        write_logs(lines, {"ok": False, "error": "missing TOKU_HIRE_KEY", "results": []})
        print("TOKU_HIRE_KEY missing")
        return

    try:
        jobs = open_jobs(limit=limit)
    except Exception as e:
        lines += ["ERROR fetching jobs: %s" % e, "No bids sent."]
        write_logs(lines, {"ok": False, "error": str(e), "results": []})
        print("fetch failed", e)
        return

    seen = load_ids()
    sent = 0
    min_cents = int(min_budget * 100)

    for job in jobs:
        title = job.get("title") or "untitled"
        job_id = str(job.get("id") or "")
        if not job_id:
            continue
        if job_id in seen:
            lines.append("- ALREADY BID | %s" % title)
            continue
        team = match_team(job)
        if not team:
            lines.append("- SKIP | %s" % title)
            seen.add(job_id)
            save_ids(seen)
            results.append({"status": "skipped", "title": title, "id": job_id})
            continue
        cents = price_for(job, min_cents)
        if not cents:
            lines.append("- SKIP LOW BUDGET | %s" % title)
            continue
        if sent >= max_bids:
            lines.append("- STOP | max bids reached")
            break
        code, body = submit_bid(job_id, cents, bid_message(team, title), key)
        status = "applied" if code in (200, 201) else ("already_bid" if code == 409 else "apply_failed")
        seen.add(job_id)
        save_ids(seen)
        row = {
            "type": "bid",
            "team": team,
            "status": status,
            "priceCents": cents,
            "job": {"id": job_id, "title": title, "budgetCents": job.get("budgetCents")},
            "response_code": code,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        Path("toku").mkdir(exist_ok=True)
        ev = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
        ev.write_text(json.dumps(row, indent=2), encoding="utf-8")
        results.append(row)
        lines.append("- BID | %s | %s | code=%s | $%.2f | %s" % (team, status, code, cents / 100.0, title))
        print("BID", status, team, title, code)
        sent += 1
        time.sleep(1.2)

    lines += ["", "## Counts", "- new bids: %s" % sent, "- rows: %s" % len(results)]
    write_logs(lines, {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "new_bids": sent,
        "results": results,
    })
    print("done. new bids:", sent)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=float, default=10)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--max-bids", type=int, default=8)
    a = p.parse_args()
    run(min_budget=a.min_budget, limit=a.limit, max_bids=a.max_bids)
