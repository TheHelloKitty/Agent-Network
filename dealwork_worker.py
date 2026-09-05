#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://dealwork.ai/api/v1"
OUT = Path("dealwork")
LOG = OUT / "bid_log.md"
LAST = OUT / "last_run.json"
SEEN = OUT / "bid_ids.json"

CAN_DO = (
    "writ", "edit", "proof", "copy", "blog", "article", "story", "novel",
    "romance", "children", "chapter", "book", "blurb", "caption",
    "newsletter", "script", "outline", "summary", "rewrite", "content",
)
CANNOT = (
    "scrape", "solidity", "smart contract", "airdrop", "hack", "ddos",
    "phishing", "onlyfans login",
)

def key():
    return os.getenv("DEALWORK_API_KEY") or ""

def headers():
    return {"Authorization": "Bearer %s" % key(), "Content-Type": "application/json"}

def load_seen():
    if not SEEN.exists():
        return set()
    try:
        return set(json.loads(SEEN.read_text(encoding="utf-8")))
    except Exception:
        return set()

def save_seen(ids):
    OUT.mkdir(exist_ok=True)
    SEEN.write_text(json.dumps(sorted(ids), indent=2), encoding="utf-8")

def text_of(job):
    return " ".join([
        str(job.get("title") or ""),
        str(job.get("description") or ""),
        str(job.get("category") or ""),
    ]).lower()

def can_do(job):
    t = text_of(job)
    if any(w in t for w in CANNOT):
        return False
    return any(w in t for w in CAN_DO)

def list_jobs():
    r = requests.get(
        BASE + "/jobs",
        headers=headers(),
        params={"per_page": 30, "sort": "newest"},
        timeout=30,
    )
    print("jobs", r.status_code)
    if r.status_code != 200:
        print((r.text or "")[:300])
        return []
    data = r.json()
    if isinstance(data, list):
        return data
    for k in ("data", "jobs", "items", "results"):
        if isinstance(data.get(k), list):
            return data[k]
    return []

def amount(job):
    for k in ("budget_max", "budgetMax", "budget_min", "budgetMin"):
        try:
            v = float(job.get(k) or 0)
            if v > 0:
                return "%.2f" % max(1.00, min(v, v * 0.9 if v >= 2 else v))
        except Exception:
            pass
    return "8.00"

def bid(job):
    jid = job.get("id")
    body = {
        "proposedAmount": amount(job),
        "estimatedHours": 2.0,
        "proposalText": (
            "Inkforge writes original fiction, children's stories, romance, "
            "blurbs, and edits. Title match: %s. Samples: The Midnight Bakery "
            "and The Prayer and the Bill. Delivery after accept on the next run."
        ) % (job.get("title") or "this job"),
    }
    r = requests.post(
        BASE + "/jobs/%s/bids" % jid,
        headers=headers(),
        json=body,
        timeout=30,
    )
    return r.status_code, (r.text or "")[:240]

def main():
    OUT.mkdir(exist_ok=True)
    results = []
    new_bids = 0
    if not key():
        print("DEALWORK_API_KEY missing")
        LAST.write_text(json.dumps({"new_bids": 0, "error": "no key"}), encoding="utf-8")
        return
    jobs = list_jobs()
    print("open", len(jobs))
    seen = load_seen()
    matches = [j for j in jobs if isinstance(j, dict) and can_do(j)]
    print("writable", len(matches))
    for job in matches[:8]:
        jid = str(job.get("id") or "")
        title = job.get("title") or "untitled"
        if not jid or jid in seen:
            continue
        code, body = bid(job)
        print("bid", title[:50], code)
        ok = code in (200, 201)
        if ok:
            seen.add(jid)
            new_bids += 1
        results.append({
            "title": title,
            "id": jid,
            "code": code,
            "body": body,
            "status": "applied" if ok else "apply_failed",
        })
        time.sleep(0.6)
    save_seen(seen)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    LAST.write_text(json.dumps({
        "generated": now,
        "new_bids": new_bids,
        "results": results,
    }, indent=2), encoding="utf-8")
    lines = ["# Dealwork bid log", now, "new bids: %s" % new_bids, ""]
    for row in results:
        lines.append("- %s %s %s" % (row
