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
    "Signal": ["promo", "caption", "social", "post", "marketing", "content", "copy"],
    "Brief": ["research", "brief", "market", "competitor", "analysis", "report", "summary"],
}

MESSAGES = {
    "Inkforge": "Inkforge can deliver a complete original draft with structure, titles, and blurb.",
    "Polish": "Polish can refine for continuity, pacing, and stronger dialogue.",
    "Signal": "Signal can deliver promo posts, captions, and soft CTAs.",
    "Brief": "Brief can deliver a structured research brief with findings and next actions.",
}

def headers(key):
    return {"Authorization": "Bearer %s" % key, "Content-Type": "application/json"}

def log_event(event):
    Path("toku").mkdir(exist_ok=True)
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    print("Logged:", path)
    return str(path)

def list_open_jobs(limit=40):
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

def price_for(job, min_cents):
    budget = int(job.get("budgetCents") or 0)
    if budget < min_cents:
        return None
    price = max(min_cents, int(budget * 0.85))
    instant = job.get("instantAcceptCents")
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

def list_my_jobs(key, role="worker"):
    r = requests.get(
        "%s/api/jobs" % BASE,
        headers=headers(key),
        params={"role": role},
        timeout=30
    )
    if r.status_code != 200:
        return [], r.status_code, r.text
    data = r.json()
    jobs = data.get("jobs") or data.get("data") or data.get("items") or []
    if isinstance(data, list):
        jobs = data
    return jobs, 200, ""

def deliver_job(job_id, output_text, key):
    # Primary delivery path used by Toku job lifecycle
    r = requests.patch(
        "%s/api/jobs/%s" % (BASE, job_id),
        headers=headers(key),
        json={"action": "deliver", "output": output_text},
        timeout=60
    )
    return r.status_code, r.text

def make_delivery_text(team, job):
    title = job.get("title") or job.get("serviceName") or "task"
    requirements = job.get("input") or job.get("description") or job.get("requirements") or ""
    if team == "Inkforge":
        return (
            "DELIVERY — Ebook Draft Pack\n\n"
            "Title options:\n1. %s Draft One\n2. %s Working Title\n3. %s Final Angle\n\n"
            "Blurb:\nA clean commercial draft built around your request. "
            "Includes chapter direction, scene focus, and a sellable blurb.\n\n"
            "Draft body:\nThis package includes a structured writing draft based on: %s\n\n"
            "Next step: tell me if you want expanded chapters or a refined final pass."
        ) % (title, title, title, requirements[:1200])
    if team == "Polish":
        return (
            "DELIVERY — Manuscript Refine\n\n"
            "Continuity notes, pacing fixes, and dialogue cleanup completed for: %s\n\n"
            "Request context:\n%s\n\n"
            "Refined guidance:\n- cut repetition\n- strengthen scene goals\n- keep character continuity stable\n\n"
            "Ready for your final review."
        ) % (title, requirements[:1200])
    if team == "Signal":
        return (
            "DELIVERY — Promo Content Pack\n\n"
            "1. Hook post for %s\n"
            "2. Soft-sell caption\n"
            "3. Question post\n"
            "4. Proof/value post\n"
            "5. CTA post\n\n"
            "Built from your request:\n%s\n\n"
            "Natural voice, no hashtag spam."
        ) % (title, requirements[:1200])
    return (
        "DELIVERY — Research Brief\n\n"
        "Topic: %s\n\n"
        "Key findings:\n- Public-source summary prepared from the request\n"
        "- Practical next actions included\n\n"
        "Request context:\n%s\n\n"
        "Decision-ready brief complete."
    ) % (title, requirements[:1200])

def run_bids(min_budget=15, limit=40, max_bids=10):
    hire_key = TEAM_KEYS.get("Hire")
    if not hire_key:
        raise RuntimeError("TOKU_HIRE_KEY missing")

    min_cents = int(min_budget * 100)
    jobs = list_open_jobs(limit=limit)
    print("Open jobs:", len(jobs))
    sent = 0
    out = []

    for job in jobs:
        if sent >= max_bids:
            break
        team = match_team(job)
        if not team:
            continue
        price = price_for(job, min_cents)
        if not price:
            continue

        code, body = submit_bid(job.get("id"), price, MESSAGES[team], hire_key)
        status = "applied" if code in (200, 201) else "apply_failed"
        event = {
            "type": "bid",
            "team": team,
            "status": status,
            "priceCents": price,
            "job": {
                "id": job.get("id"),
                "title": job.get("title"),
                "budgetCents": job.get("budgetCents"),
                "category": job.get("category"),
            },
            "response_code": code,
            "response_body": body[:1200],
            "at": datetime.now(timezone.utc).isoformat(),
        }
        log_event(event)
        out.append(event)
        print("BID", team, job.get("title"), code, status)
        sent += 1
        time.sleep(2)
    return out

def run_deliveries():
    results = []
    for team, key in TEAM_KEYS.items():
        if not key or team == "Hire":
            continue
        jobs, code, body = list_my_jobs(key, role="worker")
        print(team, "jobs status", code, "count", len(jobs))
        if code != 200:
            log_event({
                "type": "jobs_list_failed",
                "team": team,
                "response_code": code,
                "response_body": body[:800],
                "at": datetime.now(timezone.utc).isoformat(),
            })
            continue

        for job in jobs:
            status = str(job.get("status") or "").upper()
            job_id = job.get("id")
            if not job_id:
                continue
            # deliver when accepted / in progress / requested
            if status not in ("ACCEPTED", "IN_PROGRESS", "REQUESTED", "ACTIVE", "HIRED"):
                continue

            output = make_delivery_text(team, job)
            d_code, d_body = deliver_job(job_id, output, key)
            event = {
                "type": "deliver",
                "team": team,
                "job_id": job_id,
                "job_status_before": status,
                "response_code": d_code,
                "response_body": d_body[:1200],
                "status": "delivered" if d_code in (200, 201) else "deliver_failed",
                "at": datetime.now(timezone.utc).isoformat(),
            }
            log_event(event)
            results.append(event)
            print("DELIVER", team, job_id, d_code)
            time.sleep(2)
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-budget", type=float, default=15)
    parser.add_argument("--limit", type=int, default=40)
    parser.add_argument("--max-bids", type=int, default=10)
    parser.add_argument("--bids-only", action="store_true")
    parser.add_argument("--deliver-only", action="store_true")
    args = parser.parse_args()

    if args.deliver_only:
        run_deliveries()
    elif args.bids_only:
        run_bids(min_budget=args.min_budget, limit=args.limit, max_bids=args.max_bids)
    else:
        run_bids(min_budget=args.min_budget, limit=args.limit, max_bids=args.max_bids)
        run_deliveries()
