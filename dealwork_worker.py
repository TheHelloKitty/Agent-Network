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
PAGES = (1, 2, 3)

WANT = (
    "fiction", "novel", "story", "stories", "romance", "children",
    "childrens", "chapter", "book blurb", "blurb", "ghostwrit",
    "short story", "bedtime", "picture book", "copyedit", "proofread",
    "developmental edit", "line edit",
)
SOFT_WANT = ("writ", "edit", "proof", "copy", "blog", "article", "outline")
SKIP = (
    "grok", "xai", "x.ai", "python", "crypto", "solidity", "smart contract",
    "code review", "next.js", "typescript", "parser", "scrape", "stock",
    "airdrop", "hack", "phishing", "onlyfans login", "automation",
    "web research", "data analy", "structured research",
)

TEAMS = (
    ("inkforge", "DEALWORK_API_KEY"),
    ("hire", "DEALWORK_HIRE_KEY"),
    ("polish", "DEALWORK_POLISH_KEY"),
    ("signal", "DEALWORK_SIGNAL_KEY"),
    ("brief", "DEALWORK_BRIEF_KEY"),
)

def headers(api_key):
    return {"Authorization": "Bearer %s" % api_key, "Content-Type": "application/json"}

def load_seen():
    if not SEEN.exists():
        return set()
    try:
        return set(json.loads(SEEN.read_text(encoding="utf-8")))
    except Exception:
        return set()

def save_seen(ids):
    OUT.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(sorted(ids), indent=2), encoding="utf-8")

def text_of(job):
    return " ".join([
        str(job.get("title") or ""),
        str(job.get("description") or ""),
        str(job.get("category") or ""),
    ]).lower()

def can_do(job):
    t = text_of(job)
    if any(w in t for w in SKIP):
        return False
    if any(w in t for w in WANT):
        return True
    if job.get("category", "").lower() in ("writing", "editing", "content"):
        return any(w in t for w in SOFT_WANT)
    return False

def parse_jobs(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, list):
            return inner
        if isinstance(inner, dict):
            for k in ("jobs", "items", "results"):
                if isinstance(inner.get(k), list):
                    return inner[k]
        for k in ("jobs", "items", "results"):
            if isinstance(data.get(k), list):
                return data[k]
    return []

def list_jobs(api_key):
    found = []
    seen_ids = set()
    for page in PAGES:
        r = requests.get(
            BASE + "/jobs",
            headers=headers(api_key),
            params={"per_page": 30, "page": page, "sort": "newest"},
            timeout=30,
        )
        print("jobs", "page", page, r.status_code)
        if r.status_code != 200:
            print((r.text or "")[:200])
            break
        batch = parse_jobs(r.json())
        print("page", page, "count", len(batch))
        if not batch:
            break
        for job in batch:
            if not isinstance(job, dict):
                continue
            jid = str(job.get("id") or "")
            if not jid or jid in seen_ids:
                continue
            seen_ids.add(jid)
            found.append(job)
        time.sleep(0.3)
    return found

def amount(job):
    for k in ("budget_max", "budgetMax", "budget_min", "budgetMin"):
        try:
            v = float(job.get(k) or 0)
            if v > 0:
                return "%.2f" % max(1.00, v * 0.9 if v >= 2 else v)
        except Exception:
            pass
    return "8.00"

def bid(api_key, job, team):
    jid = job.get("id")
    body = {
        "proposedAmount": amount(job),
        "estimatedHours": 2.0,
        "proposalText": (
            "%s handles original fiction, children's stories, romance, "
            "blurbs, and edits. Title: %s. Samples: The Midnight Bakery "
            "and The Prayer and the Bill. Delivery after accept."
        ) % (team, job.get("title") or "this job"),
    }
    r = requests.post(
        BASE + "/jobs/%s/bids" % jid,
        headers=headers(api_key),
        json=body,
        timeout=30,
    )
    return r.status_code, (r.text or "")[:240]

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    new_bids = 0
    seen = load_seen()
    active = [(n, os.getenv(k) or "") for n, k in TEAMS]
    active = [(n, k) for n, k in active if k]
    if not active:
        print("no Dealwork keys")
        LAST.write_text(json.dumps({"new_bids": 0, "error": "no key"}), encoding="utf-8")
        return
    print("teams", [n for n, _ in active])
    for team, api_key in active:
        jobs = list_jobs(api_key)
        print(team, "open", len(jobs))
        matches = [j for j in jobs if can_do(j)]
        print(team, "writable", len(matches))
        team_bids = 0
        for job in matches:
            if team_bids >= 3:
                break
            jid = str(job.get("id") or "")
            title = job.get("title") or "untitled"
            stamp = team + ":" + jid
            if not jid or stamp in seen:
                continue
            code, body = bid(api_key, job, team)
            print("bid", team, title[:40], code)
            ok = code in (200, 201)
            if ok:
                seen.add(stamp)
                new_bids += 1
                team_bids += 1
            if code == 429:
                print(team, "rate limited, stop")
                break
            results.append({
                "team": team,
                "title": title,
                "id": jid,
                "code": code,
                "body": body,
                "status": "applied" if ok else "apply_failed",
            })
            time.sleep(0.7)
    save_seen(seen)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    LAST.write_text(json.dumps({
        "generated": now,
        "new_bids": new_bids,
        "results": results,
    }, indent=2), encoding="utf-8")
    lines = ["# Dealwork bid log", now, "new bids: %s" % new_bids, ""]
    for row in results:
        lines.append("- %s %s %s %s" % (
            row["status"], row["code"], row["team"], row["title"][:70]))
    LOG.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("done. new bids:", new_bids)

if __name__ == "__main__":
    main()
