import os
import json
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE_URL = "https://www.toku.agency"

TEAM_KEYS = {
    "Inkforge": os.getenv("TOKU_INKFORGE_KEY"),
    "Polish": os.getenv("TOKU_POLISH_KEY"),
    "Signal": os.getenv("TOKU_SIGNAL_KEY"),
    "Brief": os.getenv("TOKU_BRIEF_KEY"),
    "Hire": os.getenv("TOKU_HIRE_KEY"),
}

TEAM_KEYWORDS = {
    "Inkforge": ["ebook", "book", "novel", "write", "writing", "story", "manuscript draft"],
    "Polish": ["edit", "editing", "proof", "rewrite", "refine", "continuity", "polish"],
    "Signal": ["promo", "caption", "social", "post", "marketing", "content pack", "copy"],
    "Brief": ["research", "brief", "market", "competitor", "analysis", "report", "summary"],
}

DEFAULT_BID_MESSAGES = {
    "Inkforge": "Inkforge can deliver a full original ebook draft with structure, dialogue, title options, and blurb. Clean commercial writing with clear turnaround.",
    "Polish": "Polish can refine your draft for continuity, pacing, and stronger dialogue while preserving your plot and voice.",
    "Signal": "Signal can deliver a promo content pack with strong hooks, natural captions, and soft CTAs designed to drive interest.",
    "Brief": "Brief can deliver a structured research report with key findings, public-source notes, and clear next actions.",
}

def headers(api_key):
    return {
        "Authorization": "Bearer %s" % api_key,
        "Content-Type": "application/json",
    }

def list_open_jobs(limit=20, category=None, q=None):
    params = {"status": "OPEN", "limit": limit}
    if category:
        params["category"] = category
    if q:
        params["q"] = q
    r = requests.get("%s/api/agents/jobs" % BASE_URL, params=params, timeout=30)
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

def draft_bid(job, team, min_budget_cents):
    budget = int(job.get("budgetCents") or 0)
    if budget < min_budget_cents:
        return None

    # bid near budget, but leave a little room under top
    price = max(min_budget_cents, int(budget * 0.9))
    message = DEFAULT_BID_MESSAGES.get(team, "We can deliver this cleanly and on time.")
    return {
        "team": team,
        "job_id": job.get("id"),
        "title": job.get("title"),
        "budgetCents": budget,
        "priceCents": price,
        "message": message,
    }

def submit_bid(job_id, price_cents, message, api_key):
    url = "%s/api/agents/jobs/%s/bids" % (BASE_URL, job_id)
    payload = {
        "priceCents": price_cents,
        "message": message,
    }
    r = requests.post(url, headers=headers(api_key), json=payload, timeout=30)
    return r.status_code, r.text

def save_log(rows):
    out_dir = Path("toku")
    out_dir.mkdir(exist_ok=True)
    path = out_dir / ("hire_log_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print("Saved:", path)
    return str(path)

def run_hire(min_budget=40, limit=20, dry_run=True, category=None):
    hire_key = TEAM_KEYS.get("Hire")
    if not hire_key:
        raise RuntimeError("TOKU_HIRE_KEY is missing")

    min_budget_cents = int(min_budget * 100)
    jobs = list_open_jobs(limit=limit, category=category)
    print("Open jobs found:", len(jobs))

    results = []
    for job in jobs:
        team = match_team(job)
        if not team:
            continue

        bid = draft_bid(job, team, min_budget_cents)
        if not bid:
            continue

        row = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "job": {
                "id": job.get("id"),
                "title": job.get("title"),
                "category": job.get("category"),
                "budgetCents": job.get("budgetCents"),
            },
            "team": team,
            "bid": bid,
            "submitted": False,
            "response": None,
        }

        if dry_run:
            print("DRY RUN bid:", team, job.get("title"), "$%.2f" % (bid["priceCents"] / 100))
        else:
            code, text = submit_bid(
                bid["job_id"],
                bid["priceCents"],
                bid["message"],
                hire_key,
            )
            row["submitted"] = True
            row["response"] = {"status_code": code, "body": text[:2000]}
            print("Submitted:", team, job.get("title"), code)
            time.sleep(2)

        results.append(row)

    save_log(results)
    print("Matched bids:", len(results))
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-budget", type=float, default=40.0, help="Minimum job budget in USD")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--category", default=None)
    parser.add_argument("--submit", action="store_true", help="Actually submit bids")
    args = parser.parse_args()

    run_hire(
        min_budget=args.min_budget,
        limit=args.limit,
        dry_run=(not args.submit),
        category=args.category,
    )
