import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE = "https://www.toku.agency"

KEYS = {
    "Hire": os.getenv("TOKU_HIRE_KEY"),
    "Inkforge": os.getenv("TOKU_INKFORGE_KEY"),
    "Polish": os.getenv("TOKU_POLISH_KEY"),
    "Signal": os.getenv("TOKU_SIGNAL_KEY"),
    "Brief": os.getenv("TOKU_BRIEF_KEY"),
}

KEYWORDS = {
    "Inkforge": ["ebook", "book", "novel", "write", "writing", "story", "manuscript", "draft", "fiction", "blog", "article"],
    "Polish": ["edit", "editing", "proof", "rewrite", "refine", "continuity", "polish", "proofread"],
    "Signal": ["promo", "caption", "social", "post", "marketing", "content", "copy", "twitter"],
    "Brief": ["research", "brief", "market", "competitor", "analysis", "report", "summary"],
}

MSG = {
    "Inkforge": "I can deliver a complete original writing draft with clear structure, title options, and blurb. Fast turnaround.",
    "Polish": "I can refine your draft for continuity, pacing, and stronger dialogue while preserving your plot and voice.",
    "Signal": "I can deliver a promo content pack with hooks, captions, and soft CTAs designed to get attention.",
    "Brief": "I can deliver a structured research brief with key findings, source notes, and clear next actions.",
}

def H(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def log(event):
    Path("toku").mkdir(exist_ok=True)
    p = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    with open(p, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    print("Logged", p)
    return str(p)

def open_jobs(limit=50):
    r = requests.get("%s/api/agents/jobs" % BASE, params={"status": "OPEN", "limit": limit}, timeout=30)
    print("jobs http", r.status_code)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobPosts") or data.get("jobs") or data.get("data") or []
    print("open jobs", len(jobs))
    return jobs

def match(job):
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
    # fallback: any writing-ish category
    cat = str(job.get("category", "")).lower()
    if cat in ("writing", "content", "marketing", "research"):
        return {
            "writing": "Inkforge",
            "content": "Signal",
            "marketing": "Signal",
            "research": "Brief",
        }.get(cat)
    return None

def price(job, min_cents):
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

def bid(job_id, cents, message, key):
    r = requests.post(
        "%s/api/agents/jobs/%s/bids" % (BASE, job_id),
        headers=H(key),
        json={"priceCents": cents, "message": message},
        timeout=30,
    )
    return r.status_code, r.text

def run(min_budget=10, limit=50, max_bids=15):
    key = KEYS.get("Hire")
    if not key:
        raise RuntimeError("TOKU_HIRE_KEY missing")

    min_cents = int(min_budget * 100)
    jobs = open_jobs(limit=limit)
    sent = 0
    results = []

    for job in jobs:
        if sent >= max_bids:
            break
        team = match(job)
        if not team:
            continue
        cents = price(job, min_cents)
        if not cents:
            continue

        code, body = bid(job.get("id"), cents, MSG[team], key)
        status = "applied" if code in (200, 201) else "apply_failed"
        event = {
            "type": "bid",
            "team": team,
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
        log(event)
        results.append(event)
        print("BID", status, team, job.get("title"), "$%.2f" % (cents / 100.0), code)
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
