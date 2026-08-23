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

def ensure_toku_dir():
    Path("toku").mkdir(exist_ok=True)

def save_event(event):
    ensure_toku_dir()
    path = Path("toku") / ("event_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2)
    print("Logged:", path)
    return str(path)

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

def log_status(team, job, status, extra=None):
    event = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "team": team,
        "status": status,
        "applied": status == "applied",
        "accepted": status == "accepted",
        "completed": status == "completed",
        "job": {
            "id
