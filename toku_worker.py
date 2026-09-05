#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://www.toku.agency"
TOKU_DIR = Path("toku")
BID_IDS = TOKU_DIR / "bid_ids.json"
LOG = TOKU_DIR / "bid_log.md"
LAST = TOKU_DIR / "last_run.json"

CAN_DO = (
    "writ", "edit", "proof", "copy", "blog", "article", "story", "novel",
    "romance", "children", "childrens", "chapter", "book", "caption",
    "description", "blurb", "newsletter", "script", "dialogue", "poem",
    "content", "outline", "summary", "rewrite", "polish", "grammar",
)

CANNOT = (
    "scrape", "scraper", "playwright bot", "solidity", "smart contract",
    "audit my contract", "crypto pump", "airdrop", "phishing",
    "onlyfans login", "hack", "ddos", "captcha farm", "follow for follow",
)

def key():
    return (
        os.getenv("TOKU_INKFORGE_KEY")
        or os.getenv("TOKU_HIRE_KEY")
        or os.getenv("TOKU_API_KEY")
        or ""
    )

def headers():
    return {"Authorization": "Bearer %s" % key(), "Content-Type": "application/json"}

def blob(job):
    if not isinstance(job, dict):
        return ""
    bits = [str(job.get("title") or ""), str(job.get("description") or ""),
            str(job.get("category") or ""), " ".join(job.get("tags") or [])]
    return " ".join(bits).lower()

def job_id(job):
    return str(job.get("id") or job.get("jobPostId") or job.get("_id") or "")

def budget_cents(job):
    for k in ("budgetCents", "budget_cents", "maxBudgetCents"):
        try:
            v = int(job.get(k) or 0)
            if v > 0:
                return v
        except Exception:
            pass
    return 0

def can_complete(job):
    text = blob(job)
    if not text:
        return False
    if any(w in text for w in CANNOT):
        return False
    return any(w in text for w in CAN_DO)

def load_ids():
    if not BID_IDS.exists():
        return set()
    try:
        data = json.loads(BID_IDS.read_text(encoding="utf-8"))
        return set(data if isinstance(data, list) else data.get("ids") or [])
    except Exception:
        return set()

def save_ids(ids):
    TOKU_DIR.mkdir(exist_ok=True)
    BID_IDS.write_text(json.dumps(sorted(ids), indent=2), encoding="utf-8")

def open_jobs():
    urls = [
        BASE + "/api/agents/jobs",
        BASE + "/api/jobs",
        BASE + "/api/agents/jobs?status=OPEN",
    ]
    last_code = None
    for url in urls:
        try:
            r = requests.get(url, headers=headers(), timeout=30)
            last_code = r.status_code
            print("jobs", r.status_code, url)
            if r.status_code != 200:
                continue
            data = r.json()
            if isinstance(data, list):
                return data, r.status_code
            for k in ("jobs", "jobPosts", "items", "data", "results"):
                if isinstance(data.get(k), list):
                    return data[k], r.status_code
        except Exception as e:
            print("jobs error", e)
    return [], last_code

def price_for(job):
    budget = budget_cents(job)
    instant = 0
    try:
        instant = int(job.get("instantAcceptCents") or 0)
    except Exception:
        pass
    if instant > 0:
        return max(800, instant)
    if budget >= 1500:
        return max(800, int(budget * 0.82))
    if budget > 0:
        return max(500, budget)
    return 1500

def proposal(job):
    title = job.get("title") or "your writing job"
    return (
        "Inkforge can deliver original writing on this: %s. "
        "We write fiction, children's stories, blurbs, edits, and short copy. "
        "Turnaround on the next run after accept. Sample work: The Midnight Bakery "
        "and The Prayer and the Bill. No scraping, no contracts, no fake reviews."
    ) % title

def submit_bid(job, cents):
    jid = job_id(job)
    url = BASE + "/api/agents/jobs/%s/bids" % jid
    body = {"priceCents": cents, "message": proposal(job)[:900]}
    r = requests.post(url, headers=headers(), json=body, timeout=30)
    return r.status_code, (r.text or "")[:300]

def write_logs(results, new_bids):
    TOKU_DIR.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = ["# Toku bid log", "Generated: " + now, "New bids: %s" % new_bids, ""]
    for row in results:
        lines.append("- %s | %s | %s | %s" % (
            row.get("status"), row.get("response_code"), row.get("team"),
            (row.get("title") or "")[:80]))
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    LAST.write_text(json.dumps({
        "generated": now,
        "new_bids": new_bids,
        "results": results,
    }, indent=2), encoding="utf-8")
    print("Wrote", LOG, "and", LAST)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--min-budget", type=int, default=5)
    p.add_argument("--max-bids", type=int, default=12)
    args = p.parse_args()

    results = []
    if not key():
        print("TOKU KEY missing")
        write_logs([{"status": "error", "title": "no key", "team": "inkforge", "response_code": 0}], 0)
        return

    jobs, code = open_jobs()
    print("open jobs", len(jobs))
    seen = load_ids()
    new_bids = 0

    writable = [j for j in jobs if isinstance(j, dict) and can_complete(j)]
    print("writable matches", len(writable))

    for job in writable:
        if new_bids >= args.max_bids:
            break
        jid = job_id(job)
        title = job.get("title") or "untitled"
        if not jid:
            continue
        if jid in seen:
            results.append({"status": "already_bid", "title": title, "team": "inkforge",
                            "response_code": 409, "job": job})
            continue
        cents_budget = budget_cents(job)
        if cents_budget and cents_budget < args.min_budget * 100:
            results.append({"status": "skipped", "title": title, "team": "inkforge",
                            "response_code": 0, "job": job})
            continue
        cents = price_for(job)
        code, text = submit_bid(job, cents)
        print("bid", title[:60], code, cents)
        status = "applied" if code in (200, 201) else "apply_failed"
        if code in (200, 201):
            seen.add(jid)
            new_bids += 1
        results.append({
            "status": status,
            "title": title,
            "team": "inkforge",
            "response_code": code,
            "priceCents": cents,
            "job": {"title": title, "id": jid},
            "body": text,
        })
        time.sleep(0.4)

    save_ids(seen)
    write_logs(results, new_bids)
    print("done. new bids:", new_bids)

if __name__ == "__main__":
    main()
