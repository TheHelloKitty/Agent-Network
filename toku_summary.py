import json
from datetime import datetime, timezone
from pathlib import Path

TOKU_DIR = Path("toku")

def write_hire_summary(results):
    TOKU_DIR.mkdir(exist_ok=True)
    path = TOKU_DIR / ("hire_summary_%s.json" % datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "attempted": len(results),
        "applied": len([r for r in results if r.get("status") == "applied"]),
        "failed": len([r for r in results if r.get("status") == "apply_failed"]),
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print("Wrote", path)
    return str(path)

def latest_summary():
    files = sorted(TOKU_DIR.glob("hire_summary_*.json"))
    if not files:
        return None
    return files[-1]

def print_latest():
    path = latest_summary()
    if not path:
        print("No hire_summary files found in toku/")
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("results") or data if isinstance(data, list) else data.get("results") or []
    print("FILE:", path)
    print("ATTEMPTED:", data.get("attempted", len(rows)))
    print("APPLIED:", data.get("applied", len([r for r in rows if r.get("status") == "applied"])))
    print("FAILED:", data.get("failed", len([r for r in rows if r.get("status") == "apply_failed"])))
    print("")
    for row in rows:
        job = row.get("job") or {}
        print("-", row.get("status"), "|", row.get("team"), "|", job.get("title"), "| code", row.get("response_code"))

if __name__ == "__main__":
    print_latest()
