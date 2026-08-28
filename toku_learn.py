import json
from collections import Counter
from pathlib import Path

def run():
    path = Path("toku")
    titles_ok = []
    titles_bad = []
    for f in path.glob("event_*.json"):
        try:
            row = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if row.get("type") != "bid":
            continue
        title = (row.get("job") or {}).get("title") or ""
        status = row.get("status")
        if status == "applied":
            titles_ok.append(title)
        elif status in ("apply_failed", "already_bid"):
            titles_bad.append(title)

    def top_words(titles):
        c = Counter()
        stop = {"the", "and", "for", "with", "job", "a", "to", "of", "in", "on"}
        for t in titles:
            for w in t.lower().replace("—", " ").replace("-", " ").split():
                w = "".join(ch for ch in w if ch.isalnum())
                if len(w) > 3 and w not in stop:
                    c[w] += 1
        return c.most_common(15)

    data = {
        "applied_count": len(titles_ok),
        "failed_count": len(titles_bad),
        "good_words": top_words(titles_ok),
        "bad_words": top_words(titles_bad),
        "prefer_next": [w for w, n in top_words(titles_ok) if n >= 2],
        "avoid_next": [w for w, n in top_words(titles_bad) if n >= 3],
    }
    Path("toku/learn.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    run()
