import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"

TEAM_KEYS = {
    "Inkforge": os.getenv("TOKU_INKFORGE_KEY"),
    "Polish": os.getenv("TOKU_POLISH_KEY"),
    "Signal": os.getenv("TOKU_SIGNAL_KEY"),
    "Brief": os.getenv("TOKU_BRIEF_KEY"),
    "Hire": os.getenv("TOKU_HIRE_KEY"),
}

TEAM_KEYWORDS = {
    "Inkforge": ["ebook", "book", "novel", "write", "writing", "story", "manuscript", "draft", "fiction"],
    "Polish": ["edit", "editing", "proof", "rewrite", "refine", "continuity", "polish", "proofread"],
    "Signal": ["promo", "caption", "social", "post", "marketing", "content", "copy", "twitter", "x post"],
    "Brief": ["research", "brief", "market", "competitor", "analysis", "report", "summary"],
}

MESSAGES = {
    "Inkforge": "Inkforge can deliver a full original ebook draft with structure, dialogue, title options, and blurb.",
    "Polish": "Polish can refine your draft for continuity, pacing, and stronger dialogue while keeping your plot.",
    "Signal": "Signal can deliver a promo pack with hooks, captions, and soft CTAs.",
    "Brief": "Brief can deliver a structured research report with findings, sources, and next actions.",
}

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def save_event(event):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    print("Logged", path)
    return str(path)

def list_jobs(limit=30):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("jobPosts") or data.get("jobs") or data.get("data") or []

def match_team(job):
    text = " ".join([
        str(job.get("title", "")),
        str(job.get("description", "")),
        " ".join(job.get("tags") or []),
        str(job.get("category", "")),
    ]).lower()
    for team, words in TEAM_KEYWORDS.items():
        for w in words:
            if w in text:
                return team
    return None

def bid_price(job, min_cents):
    budget = int(job.get("budgetCents") or 0)
    instant = job.get("instantAcceptCents")
    if budget < min_cents:
        return None
    price = max(min_cents, int(budget * 0.85))
    if instant:
        try:
            instant = int(instant)
            if instant >= min_cents:
                price = min(price, instant)
        except Exception:
            pass
    return price

def submit_bid(job_id, price, message, key):
    url = "%s/api/agents/jobs/%s/bids" % (BASE, job_id)
    r = requests.post(url, headers=headers(key), json={"priceCents": price, "message": message}, timeout=30)
    return r.status_code, r.text

def run(min_budget=20, limit=30, dry_run=False, max_bids=8):
    hire_key = TEAM_KEYS.get("Hire")
    if not hire_key:
        raise RuntimeError("TOKU_HIRE_KEY missing")

    min_cents = int(min_budget * 100)
    jobs = list_jobs(limit=limit)
    print("Open jobs:", len(jobs))

    sent = 0
    results = []
    for job in jobs:
        if sent >= max_bids:
            break
        team = match_team(job)
        if not team:
            continue
        price = bid_price(job, min_cents)
        if not price:
            continue

        row = {
            "team": team,
            "status": "matched",
            "job": {
                "id": job.get("id"),
                "title": job.get("title"),
                "category": job.get("category"),
                "budgetCents": job.get("budgetCents"),
            },
            "priceCents": price,
        }

        if dry_run:
            print("DRY RUN", team, job.get("title"), "$%.2f" % (price / 100.0))
            row["status"] = "matched"
        else:
            code, body = submit_bid(job.get("id"), price, MESSAGES[team], hire_key)
            print("BID", team, job.get("title"), code)
            row["response_code"] = code
            row["response_body"] = body[:1000]
            row["status"] = "applied" if code in (200, 201) else "apply_failed"
            sent += 1
            time.sleep(2)

        save_event(row)
        results.append(row)

    Path("toku").mkdir(exist_ok=True)
    summary = Path("toku") / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    with open(summary, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Submitted/matched:", len(results))
    print("Summary:", summary)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-budget", type=float, default=20)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--max-bids", type=int, default=8)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(
        min_budget=args.min_budget,
        limit=args.limit,
        dry_run=args.dry_run,
        max_bids=args.max_bids,
    )
