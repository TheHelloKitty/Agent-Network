def latest_book_to_continue():
    files = []
    root = Path("books")
    if not root.exists():
        return None
    for path in root.rglob("*_full_*.txt"):
        if "refined" in path.name.lower():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        words = word_count(text)
        if words < CONTINUE_MIN_WORDS:
            continue
        files.append((words, path))
    if not files:
        return None
    # finish the longest incomplete book first
    incomplete = [(w, p) for w, p in files if w < 15000]
    pool = incomplete if incomplete else files
    pool = sorted(pool, key=lambda x: x[0], reverse=True)
    return pool[0][1]

def run_continue():
    cleanup_empty_books(min_words=CONTINUE_MIN_WORDS)
    path = latest_book_to_continue()
    if path:
        words = word_count(Path(path).read_text(encoding="utf-8", errors="ignore"))
        print("Continuing longest book:", path, "words:", words)
        extra = 6 if words < 15000 else 3
        return continue_book(path, extra_chapters=extra)
    print("No book to continue. Starting a new one.")
    return run_publishing_network()
