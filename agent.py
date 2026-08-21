import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPORTS_DIR = "reports"
BOOKS_DIR = "books"
TOKU_JOBS_FILE = "toku/jobs.json"
HOURS = 4

EASTERN_OFFSET = timedelta(hours=-4)  # EDT

def now_utc():
    return datetime.now(timezone.utc)

def to_eastern(dt):
    return dt.astimezone(timezone(EASTERN_OFFSET))

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def recent_books(cutoff):
    items = []

    catalog = load_json(os.path.join(BOOKS_DIR, "MASTER_CATALOG.json"), {})
    for book in catalog.get("books", []):
        created = book.get("created_at")
        if not created:
            continue
        try:
            created_dt = datetime.strptime(created, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if created_dt >= cutoff:
            items.append(book)

    # Also scan category folders for newer files
    if os.path.isdir(BOOKS_DIR):
        for path in Path(BOOKS_DIR).rglob("*.txt"):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                items.append({
                    "agent": path.stem.split("_")[0],
                    "category": path.parent.name,
                    "topic": path.stem,
                    "file": str(path),
                    "created_at": mtime.strftime("%Y%m%d_%H%M%S")
                })

    # de-dupe by file
    unique = {}
    for item in items:
        unique[item.get("file")] = item
    return list(unique.values())

def toku_jobs(cutoff):
    data = load_json(TOKU_JOBS_FILE, {"jobs": []})
    recent = []

    for job in data.get("jobs", []):
        times = []
        for key in ("applied_at", "accepted_at", "completed_at", "updated_at"):
            if job.get(key):
                try:
                    times.append(datetime.fromisoformat(job[key].replace("Z", "+00:00")))
                except ValueError:
                    pass
        if any(t >= cutoff for t in times):
            recent.append(job)

    summary = {
        "applied": [j for j in recent if j.get("status") == "applied"],
        "accepted": [j for j in recent if j.get("status") == "accepted"],
        "completed": [j for j in recent if j.get("status") == "completed"],
        "other": [j for j in recent if j.get("status") not in ("applied", "accepted", "completed")]
    }
    return recent, summary

def agent_activity(books, jobs):
    activity = {}

    def bucket(agent):
        if agent not in activity:
            activity[agent] = {
                "agent": agent,
                "books_created": [],
                "toku_applied": [],
                "toku_accepted": [],
                "toku_completed": []
            }
        return activity[agent]

    for book in books:
        agent = book.get("agent", "unknown")
        bucket(agent)["books_created"].append(book)

    for job in jobs:
        agent = job.get("agent", "unknown")
        status = job.get("status", "other")
        key = {
            "applied": "toku_applied",
            "accepted": "toku_accepted",
            "completed": "toku_completed"
        }.get(status)
        if key:
            bucket(agent)[key].append(job)

    return list(activity.values())

def write_report():
    now = now_utc()
    cutoff = now - timedelta(hours=HOURS)
    books = recent_books(cutoff)
    jobs, job_summary = toku_jobs(cutoff)
    agents = agent_activity(books, jobs)

    report = {
        "title": f"{HOURS}-Hour Agent Network Report",
        "timezone": "America/New_York (EDT)",
        "generated_at_utc": now.isoformat(),
        "generated_at_eastern": to_eastern(now).isoformat(),
        "window_start_utc": cutoff.isoformat(),
        "window_start_eastern": to_eastern(cutoff).isoformat(),
        "totals": {
            "books_created": len(books),
            "toku_applied": len(job_summary["applied"]),
            "toku_accepted": len(job_summary["accepted"]),
            "toku_completed": len(job_summary["completed"]),
            "active_agents": len(agents)
        },
        "books_created": books,
        "toku_jobs": job_summary,
        "agents": agents
    }

    os.makedirs(REPORTS_DIR, exist_ok=True)
    stamp = to_eastern(now).strftime("%Y%m%d_%H%M")
    json_path = f"{REPORTS_DIR}/report_{stamp}.json"
    txt_path = f"{REPORTS_DIR}/report_{stamp}.txt"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    lines = [
        f"AGENT NETWORK REPORT",
        f"Generated: {to_eastern(now).strftime('%Y-%m-%d %I:%M %p')} EDT",
        f"Window: last {HOURS} hours",
        "",
        f"Books created: {report['totals']['books_created']}",
        f"Toku applied: {report['totals']['toku_applied']}",
        f"Toku accepted: {report['totals']['toku_accepted']}",
        f"Toku completed: {report['totals']['toku_completed']}",
        f"Active agents: {report['totals']['active_agents']}",
        "",
        "=== BOOKS ==="
    ]

    for book in books:
        lines.append(
            f"- {book.get('agent')} | {book.get('category')} | {book.get('topic')} | {book.get('file')}"
        )

    lines += ["", "=== TOKU JOBS ==="]
    for status in ("applied", "accepted", "completed"):
        lines.append(f"\n{status.upper()}:")
        if not job_summary[status]:
            lines.append("  none")
        for job in job_summary[status]:
            lines.append(
                f"- Agent {job.get('agent')} | {job.get('title')} | {job.get('job_id')} | ${job.get('pay', 'n/a')}"
            )

    lines += ["", "=== AGENTS ==="]
    for a in agents:
        lines.append(
            f"- {a['agent']}: books={len(a['books_created'])}, applied={len(a['toku_applied'])}, accepted={len(a['toku_accepted'])}, completed={len(a['toku_completed'])}"
        )

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"✅ Report saved: {txt_path}")
    print(f"✅ JSON saved: {json_path}")
    return report

if __name__ == "__main__":
    write_report()
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    if args.report:
        from datetime import datetime, timedelta, timezone
        from pathlib import Path
        import json

        HOURS = 4
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=HOURS)
        files = []

        for folder in ["agent_outputs", "books", "storefront_exports", "novels", "toku"]:
            if not os.path.isdir(folder):
                continue
            for path in Path(folder).rglob("*"):
                if path.is_file():
                    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        files.append(f"- {path}")

        lines = [
            "# Fleet Report",
            f"Generated: {now.isoformat()}",
            f"Window: last {HOURS} hours",
            f"Files found: {len(files)}",
            "",
            "## Created in the last 4 hours",
        ]
        lines.extend(files or ["None"])

        with open("fleet-report.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        print("✅ Updated fleet-report.md")
    else:
        run_publishing_network()
