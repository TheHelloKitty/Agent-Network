import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

HOURS = 4
FLEET_REPORT = "fleet-report.md"
TOKU_DIR = "toku"
OUTPUT_DIRS = ["agent_outputs", "books", "storefront_exports", "novels"]

def now_utc():
    return datetime.now(timezone.utc)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def recent_files(cutoff):
    items = []
    for folder in OUTPUT_DIRS:
        if not os.path.isdir(folder):
            continue
        for path in Path(folder).rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime >= cutoff:
                items.append({
                    "file": str(path),
                    "folder": folder,
                    "agent": path.stem.split("_")[0],
                    "created_at": mtime.isoformat()
                })
    return items

def load_toku_jobs(cutoff):
    jobs = []

    jobs_file = os.path.join(TOKU_DIR, "jobs.json")
    data = load_json(jobs_file, {})
    if isinstance(data, dict):
        jobs.extend(data.get("jobs", []))
    elif isinstance(data, list):
        jobs.extend(data)

    if os.path.isdir(TOKU_DIR):
        for path in Path(TOKU_DIR).rglob("*.json"):
            if path.name == "jobs.json":
                continue
            extra = load_json(str(path), {})
            if isinstance(extra, dict) and "jobs" in extra:
                jobs.extend(extra["jobs"])
            elif isinstance(extra, dict) and extra.get("status"):
                jobs.append(extra)
            elif isinstance(extra, list):
                jobs.extend(extra)

    recent = []
    for job in jobs:
        if not isinstance(job, dict):
            continue
        times = []
        for key in ("applied_at", "accepted_at", "completed_at", "updated_at"):
            value = job.get(key)
            if not value:
                continue
            try:
                times.append(datetime.fromisoformat(str(value).replace("Z", "+00:00")))
            except ValueError:
                pass
        if times and any(t >= cutoff for t in times):
            recent.append(job)
        elif not times:
            # include if no timestamp, so the report still shows current Toku state
            recent.append(job)
    return recent

def group_toku(jobs):
    grouped = {"applied": [], "accepted": [], "completed": [], "other": []}
    for job in jobs:
        status = str(job.get("status", "other")).lower()
        if status in grouped:
            grouped[status].append(job)
        else:
            grouped["other"].append(job)
    return grouped

def write_fleet_report():
    now = now_utc()
    cutoff = now - timedelta(hours=HOURS)
    files = recent_files(cutoff)
    jobs = load_toku_jobs(cutoff)
    grouped = group_toku(jobs)

    lines = []
    lines.append(f"# Fleet Report")
    lines.append("")
    lines.append(f"- Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"- Window: last {HOURS} hours")
    lines.append(f"- Files created: {len(files)}")
    lines.append(f"- Toku applied: {len(grouped['applied'])}")
    lines.append(f"- Toku accepted: {len(grouped['accepted'])}")
    lines.append(f"- Toku completed: {len(grouped['completed'])}")
    lines.append("")
    lines.append("## Created in the last 4 hours")
    if not files:
        lines.append("None")
    else:
        for item in files:
            lines.append(f"- {item['agent']} | {item['folder']} | {item['file']}")

    lines.append("")
    lines.append("## Toku jobs")
    for status in ("applied", "accepted", "completed"):
        lines.append(f"### {status.title()}")
        if not grouped[status]:
            lines.append("None")
        else:
            for job in grouped[status]:
                lines.append(
                    f"- {job.get('agent', 'unknown')} | {job.get('title', job.get('job_id', 'untitled'))} | {job.get('status')} | ${job.get('pay', 'n/a')}"
                )

    lines.append("")
    lines.append("## Agents")
    agents = {}
    for item in files:
        agents.setdefault(item["agent"], {"files": 0, "applied": 0, "accepted": 0, "completed": 0})
        agents[item["agent"]]["files"] += 1
    for status in ("applied", "accepted", "completed"):
        for job in grouped[status]:
            agent = job.get("agent", "unknown")
            agents.setdefault(agent, {"files": 0, "applied": 0, "accepted": 0, "completed": 0})
            agents[agent][status] += 1

    if not agents:
        lines.append("None")
    else:
        for agent, stats in sorted(agents.items()):
            lines.append(
                f"- {agent}: files={stats['files']}, applied={stats['applied']}, accepted={stats['accepted']}, completed={stats['completed']}"
            )

    with open(FLEET_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"✅ Updated {FLEET_REPORT}")

if __name__ == "__main__":
    write_fleet_report()
