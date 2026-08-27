def write_fleet_report():
    hours = 4
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    created = []
    books_completed = []
    toku_applied = []
    toku_failed = []

    for folder in ["books", "storefront_exports", "toku", "security_team"]:
        if not os.path.isdir(folder):
            continue
        for path in Path(folder).rglob("*"):
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            created.append("- %s | %s" % (folder, path))
            if folder == "books" and path.suffix == ".txt" and "refined" not in path.name.lower():
                words = word_count(path.read_text(encoding="utf-8", errors="ignore"))
                books_completed.append("- %s (%s words)" % (path, words))

    toku_dir = Path("toku")
    if toku_dir.exists():
        for path in toku_dir.rglob("*.json"):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue

            rows = []
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict) and isinstance(data.get("results"), list):
                rows = data["results"]
            elif isinstance(data, dict):
                rows = [data]

            for row in rows:
                if row.get("type") and row.get("type") != "bid":
                    continue
                job = row.get("job") or {}
                title = job.get("title") or row.get("title")
                if not title or title == "untitled":
                    continue
                team = row.get("team") or "unknown"
                status = str(row.get("status") or "").lower()
                code = row.get("response_code")
                line = "- team=%s | status=%s | code=%s | job=%s" % (team, status, code, title)
                if status == "applied":
                    toku_applied.append(line)
                elif status == "apply_failed":
                    toku_failed.append(line)

    lines = [
        "# Fleet Report",
        "Generated: " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "Window: last 4 hours",
        "",
        "## Summary",
        "Files created: %s" % len(created),
        "Books touched: %s" % len(books_completed),
        "Toku applied: %s" % len(toku_applied),
        "Toku failed: %s" % len(toku_failed),
        "",
        "## Books",
    ]
    lines.extend(books_completed or ["None"])
    lines += ["", "## Toku applied"]
    lines.extend(toku_applied or ["None"])
    lines += ["", "## Toku failed"]
    lines.extend(toku_failed or ["None"])

    Path("fleet-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Updated fleet-report.md")
    print("Toku applied:", len(toku_applied))
    print("Toku failed:", len(toku_failed))
