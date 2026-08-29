import os
import json
import random
import time
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fpdf import FPDF
from docx import Document
from providers import generate_with_failover

CATEGORIES = {
    "childrens_baby": {
        "folder": "books/childrens/baby",
        "age": "ages 0-3",
        "style": "very short lines, repetition, board-book rhythm, safe and warm",
        "topics": ["bedtime moon", "animal sounds", "mommy and me"],
    },
    "childrens_picture": {
        "folder": "books/childrens/picture",
        "age": "ages 3-6",
        "style": "short scenes, simple words, one clear problem, cozy ending",
        "topics": ["lost teddy", "first day of school", "rainy day adventure"],
    },
    "childrens_early": {
        "folder": "books/childrens/early",
        "age": "ages 6-8",
        "style": "easy chapter-book sentences, dialogue, one small adventure",
        "topics": ["talking puppy", "treehouse club", "school talent show"],
    },
    "childrens_chapter": {
        "folder": "books/childrens/chapter",
        "age": "ages 8-10",
        "style": "longer chapters, friendship stakes, a real middle problem, earned ending",
        "topics": ["summer camp mystery", "secret map", "new kid in town"],
    },
    "childrens_middle_grade": {
        "folder": "books/childrens/middle_grade",
        "age": "ages 9-12",
        "style": "middle-grade novel pace, stronger conflict, humor, emotional payoff, no adult content",
        "topics": ["magic school misfit", "family move", "soccer finals"],
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional, dialogue-heavy, detailed settings",
        "topics": ["second chance", "enemies to lovers", "slow burn"],
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy, explicit, intense dialogue and physical detail",
        "topics": ["dark mafia romance", "forced proximity"],
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "factual high-stakes public cases from public reporting only",
        "topics": [
            "a recent nationally covered homicide trial with public court filings",
            "a viral true-crime case that dominated headlines in the last 24 months",
            "Julio Foolio case public timeline and court coverage",
            "McKenzie Shirilla case public court coverage",
        ],
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "tense dialogue, sharp description, short scenes",
        "topics": ["missing wife", "witness protection"],
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "vivid places, spoken voices, quest scenes",
        "topics": ["hidden heir", "dragon academy"],
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic detail and human conversation",
        "topics": ["colony ship", "AI uprising"],
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "clear examples, plain talk, useful stories",
        "topics": ["habit building", "money basics"],
    },
    "horror": {
        "folder": "books/horror",
        "age": "adult",
        "style": "creepy description and uneasy dialogue",
        "topics": ["haunted lake house", "cult in the woods"],
    }
}

CONTINUE_MIN_WORDS = 80
COMPLETE_WORDS = {
    "childrens_baby": 150,
    "childrens_picture": 500,
    "childrens_early": 3000,
    "childrens_chapter": 10000,
    "childrens_middle_grade": 30000,
    "default": 80000,
}
COMPLETE_CHAPTERS = {
    "childrens_baby": 1,
    "childrens_picture": 1,
    "childrens_early": 6,
    "childrens_chapter": 10,
    "childrens_middle_grade": 16,
    "default": 20,
}

def generate_with_fallback(messages, temperature=0.95, max_tokens=800):
    return generate_with_failover(messages, temperature=temperature, max_tokens=max_tokens)

def safe_name(text):
    cleaned = [c for c in text if c.isalnum() or c in "-_ "]
    return "".join(cleaned).strip().replace(" ", "_")[:80]

def word_count(text):
    return len((text or "").split())

def category_from_path(path):
    text = str(path).replace("\\", "/")
    for key, cat in CATEGORIES.items():
        if cat["folder"] in text:
            return key
    if "books/childrens" in text:
        return "childrens_chapter"
    return "romance"

def is_childrens(category_key):
    return str(category_key).startswith("childrens")

def complete_threshold(path):
    cat = category_from_path(path)
    return (
        COMPLETE_WORDS.get(cat, COMPLETE_WORDS["default"]),
        COMPLETE_CHAPTERS.get(cat, COMPLETE_CHAPTERS["default"]),
    )

def txt_to_pdf(txt_path):
    try:
        pdf_path = txt_path.replace(".txt", ".pdf")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        pdf.set_font("Helvetica", size=12)
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                safe = line.encode("latin-1", "replace").decode("latin-1").strip()
                if not safe:
                    pdf.ln(6)
                    continue
                pdf.multi_cell(180, 8, " ".join(safe.split()))
        pdf.output(pdf_path)
        print("PDF saved:", pdf_path)
    except Exception as e:
        print("PDF failed:", e)

def txt_to_docx(txt_path):
    try:
        docx_path = txt_path.replace(".txt", ".docx")
        doc = Document()
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                doc.add_paragraph(line.rstrip("\n"))
        doc.save(docx_path)
        print("DOCX saved:", docx_path)
    except Exception as e:
        print("DOCX failed:", e)

def delete_book_family(txt_path):
    for sib in [txt_path, txt_path.replace(".txt", ".pdf"), txt_path.replace(".txt", ".docx")]:
        try:
            if os.path.exists(sib):
                os.remove(sib)
        except Exception as e:
            print("Could not delete", sib, e)

def is_undeveloped_book(path, min_words=None):
    try:
        p = Path(path)
        if not p.exists() or not p.is_file() or p.stat().st_size < 60:
            return True
        text = p.read_text(encoding="utf-8", errors="ignore").strip()
        cat = category_from_path(p)
        floor = 40 if is_childrens(cat) else (min_words or 800)
        return (not text) or word_count(text) < floor
    except Exception:
        return True

def cleanup_empty_books(min_words=800):
    root = Path("books")
    if not root.exists():
        return []
    removed = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name.lower() in ("category.json", "master_catalog.json"):
            continue
        if path.suffix.lower() == ".txt" and is_undeveloped_book(path, min_words=min_words):
            for sib in [path, path.with_suffix(".pdf"), path.with_suffix(".docx")]:
                if sib.exists():
                    sib.unlink(missing_ok=True)
                    removed.append(str(sib))
        elif path.suffix.lower() in [".pdf", ".docx"]:
            txt = path.with_suffix(".txt")
            if txt.exists() and is_undeveloped_book(txt, min_words=min_words):
                path.unlink(missing_ok=True)
                removed.append(str(path))
    print("Removed undeveloped files:", len(removed))
    return removed

def true_crime_system_prompt(agent_name):
    return (
        "You are %s, a factual true-crime narrator. "
        "Write ONE public case only. No invented dialogue or motive."
    ) % agent_name

def normal_system_prompt(agent_name, category_key="romance"):
    if is_childrens(category_key):
        age = CATEGORIES[category_key]["age"]
        return (
            "You are %s. Write an original children's book for %s. "
            "Match vocabulary to that age. No adult content."
        ) % (agent_name, age)
    return "You are %s. Write like a human novelist. Put people in rooms. Let them talk." % agent_name

def story_parts(text):
    low = (text or "").lower()
    start = ("chapter 1" in low) or any(x in low[:2500] for x in [
        "once upon", "it started", "one night", "one day", "prologue", "first"
    ])
    middle = word_count(text) >= 120 and any(x in low for x in [
        "but", "then", "suddenly", "problem", "until", "secret",
        "realized", "almost", "climax", "chase", "afraid", "lost"
    ])
    ending = any(x in low[-3500:] for x in [
        "the end", "happily", "good night", "goodnight", "they were safe",
        "home again", "verdict", "sentenced", "epilogue", "years later",
        "fin.", "at last", "safe again"
    ])
    return {"beginning": bool(start), "middle": bool(middle), "ending": bool(ending)}

def next_chapter_number(text):
    n = 0
    for line in text.splitlines():
        s = line.strip().upper()
        if s.startswith("CHAPTER "):
            parts = s.replace("CHAPTER", "").strip().split()
            if parts and parts[0].isdigit():
                n = max(n, int(parts[0]))
    return n + 1

def is_complete_novel(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    words = word_count(text)
    parts = story_parts(text)
    need_words, _ = complete_threshold(path)
    return words >= need_words and parts["beginning"] and parts["middle"] and parts["ending"]

def build_outline_prompt(agent_name, category_key, topic, cat):
    if category_key == "true_crime":
        return [
            {"role": "system", "content": true_crime_system_prompt(agent_name)},
            {"role": "user", "content": "Pick ONE public case matching: %s. Plan that one case only." % topic}
        ]
    if is_childrens(category_key):
        return [
            {"role": "system", "content": normal_system_prompt(agent_name, category_key)},
            {"role": "user", "content": (
                "Plan a children's book for %s about %s. "
                "Include title, beginning, middle problem/climax, and ending. Style: %s."
            ) % (cat["age"], topic, cat["style"])}
        ]
    return [
        {"role": "system", "content": normal_system_prompt(agent_name, category_key)},
        {"role": "user", "content": (
            "Create title, blurb, characters, and a chapter outline for an original %s book about %s. "
            "The outline must have beginning, middle climax, and ending."
        ) % (category_key, topic)}
    ]

def build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous):
    if category_key == "true_crime":
        return [
            {"role": "system", "content": true_crime_system_prompt(agent_name)},
            {"role": "user", "content": (
                "Continue the one chosen case. Chapter %s. Assignment: %s. "
                "Public facts only.\nContinue from:\n%s"
            ) % (chapter, topic, previous)}
        ]
    if is_childrens(category_key):
        return [
            {"role": "system", "content": normal_system_prompt(agent_name, category_key)},
            {"role": "user", "content": (
                "Write Chapter %s of a %s book about %s.\nStyle: %s\n"
                "Keep writing the story. Do not stop just because it is getting long enough.\n"
                "Continue from:\n%s"
            ) % (chapter, cat["age"], topic, cat["style"], previous)}
        ]
    return [
        {"role": "system", "content": normal_system_prompt(agent_name, category_key)},
        {"role": "user", "content": (
            "Write Chapter %s of this %s book about %s. Style: %s. "
            "Use dialogue and description. Keep the plot moving toward climax and ending.\nContinue from:\n%s"
        ) % (chapter, category_key, topic, cat["style"], previous)}
    ]

def build_ending_prompt(agent_name, category_key, topic, previous):
    cat = CATEGORIES.get(category_key, {})
    if is_childrens(category_key):
        ask = (
            "Write the FINAL chapter of this %s children's book about %s. "
            "Resolve the problem. Give a clear ending. End with The End.\nContinue from:\n%s"
        ) % (cat.get("age", "children"), topic, previous)
    elif category_key == "true_crime":
        ask = "Write the FINAL chapter using only public facts. Cover the latest public outcome.\nContinue from:\n%s" % previous
    else:
        ask = (
            "Write the FINAL chapter of this %s book about %s. "
            "Hit the climax if needed, then end the story.\nContinue from:\n%s"
        ) % (category_key, topic, previous)
    return [
        {"role": "system", "content": normal_system_prompt(agent_name, category_key)},
        {"role": "user", "content": ask}
    ]

def write_full_novel(agent_name, category_key, topic, max_chapters=4):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "%s/%s_%s_full_%s.txt" % (cat["folder"], safe_name(agent_name), safe_name(topic), timestamp)
    try:
        outline = generate_with_fallback(
            build_outline_prompt(agent_name, category_key, topic, cat),
            temperature=0.2 if category_key == "true_crime" else 0.9
        )
    except Exception as e:
        print("Outline failed:", e)
        outline = ""
    if word_count(outline) < 20:
        raise RuntimeError("Outline generation failed")

    parts = [outline]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(outline + "\n\n")
    previous = outline[-1500:]
    last_chapter = 0
    if category_key == "childrens_baby":
        chapters = 1
    elif category_key == "childrens_picture":
        chapters = 2
    elif is_childrens(category_key):
        chapters = 3
    else:
        chapters = max_chapters

    for chapter in range(1, chapters + 1):
        chapter_text = ""
        tries = 0
        need = 40 if category_key == "childrens_baby" else (80 if is_childrens(category_key) else 400)
        while word_count(chapter_text) < need and tries < 6:
            tries += 1
            try:
                chunk = generate_with_fallback(
                    build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous),
                    temperature=0.2 if category_key == "true_crime" else 0.9
                )
            except Exception as e:
                print("Generation failed on chapter", chapter, e)
                break
            if chunk and word_count(chunk) >= 8:
                chapter_text += "\n\n" + chunk
                previous = chunk[-1500:]
            time.sleep(2)
        if word_count(chapter_text) < 8:
            break
        header = "\n\nCHAPTER %s\n\n" % chapter
        with open(filename, "a", encoding="utf-8") as f:
            f.write(header + chapter_text + "\n")
        parts.append(header + chapter_text)
        last_chapter = chapter
        print("Chapter", chapter, "saved. Words so far:", word_count("\n".join(parts)))
        time.sleep(2)

    final_words = word_count("\n".join(parts))
    if final_words < (30 if is_childrens(category_key) else CONTINUE_MIN_WORDS):
        delete_book_family(filename)
        raise RuntimeError("Refusing to keep empty book (%s words)" % final_words)

    info = {
        "agent": agent_name, "category": category_key, "topic": topic,
        "file": filename, "words": final_words, "chapters": last_chapter, "created_at": timestamp
    }
    print("Novel saved:", filename, "words:", final_words)
    return info

def latest_book_to_continue():
    files = []
    root = Path("books")
    if not root.exists():
        return None
    for path in root.rglob("*_full_*.txt"):
        if "refined" in path.name.lower():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if word_count(text) < 30:
            continue
        if is_complete_novel(path):
            continue
        files.append((word_count(text), path))
    if not files:
        return None
    return sorted(files, key=lambda x: x[0], reverse=True)[0][1]

def continue_book(path, extra_chapters=6):
    print("Continuing:", path)
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    start_chapter = next_chapter_number(text)
    previous = text[-1500:] if text else "Start of book."
    added = 0
    category_key = category_from_path(path)
    cat = CATEGORIES.get(category_key, CATEGORIES["romance"])
    topic = Path(path).stem
    agent_name = "Agent_Continue"
    if category_key == "childrens_baby":
        extra_chapters = 1
    elif is_childrens(category_key):
        extra_chapters = min(extra_chapters, 3)

    for chapter in range(start_chapter, start_chapter + extra_chapters):
        chapter_text = ""
        tries = 0
        need = 40 if category_key == "childrens_baby" else (80 if is_childrens(category_key) else 400)
        while word_count(chapter_text) < need and tries < 6:
            tries += 1
            try:
                chunk = generate_with_fallback(
                    build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous),
                    temperature=0.2 if category_key == "true_crime" else 0.8
                )
            except Exception as e:
                print("Continue generation failed:", e)
                break
            if chunk and word_count(chunk) >= 8:
                chapter_text += "\n\n" + chunk
                previous = chunk[-1500:]
            time.sleep(2)
        if word_count(chapter_text) < 8:
            break
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\nCHAPTER %s\n\n%s\n" % (chapter, chapter_text))
        added += 1
        print("Added chapter", chapter)
        time.sleep(2)

    text_now = Path(path).read_text(encoding="utf-8", errors="ignore")
    parts = story_parts(text_now)
    need_words, _ = complete_threshold(path)
    if word_count(text_now) >= need_words and not parts["ending"]:
        try:
            ending = generate_with_fallback(
                build_ending_prompt(agent_name, category_key, topic, previous),
                temperature=0.7
            )
            if ending and word_count(ending) >= 15:
                with open(path, "a", encoding="utf-8") as f:
                    f.write("\n\nCHAPTER %s\n\n%s\n\nThe End\n" % (start_chapter + added, ending))
                print("Wrote ending chapter")
        except Exception as e:
            print("Ending chapter failed:", e)
    print("Added chapters this run:", added)
    return str(path)

def update_category_file(category_key, book_info):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    index_path = cat["folder"] + "/CATEGORY.json"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"category": category_key, "books": []}
    data["books"].append(book_info)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def list_book_files(limit=2):
    files = []
    root = Path("books")
    if not root.exists():
        return []
    for path in root.rglob("*.txt"):
        name = path.name.lower()
        if "refined" in name or name == "category.json":
            continue
        if is_undeveloped_book(path):
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]

def refine_book(txt_path):
    original = Path(txt_path).read_text(encoding="utf-8", errors="ignore")
    if word_count(original) < 40:
        return None
    prompt = [
        {"role": "system", "content": "You are a professional editor. Keep age-appropriateness."},
        {"role": "user", "content": "Edit this section into stronger prose.\n\n%s" % original[:4000]}
    ]
    try:
        edited = generate_with_fallback(prompt, temperature=0.4)
    except Exception as e:
        print("Refine failed:", e)
        return None
    out_path = str(txt_path).replace(".txt", "_refined.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(edited or original[:4000])
    return out_path

def run_refine(limit=2):
    results = []
    for path in list_book_files(limit=limit):
        try:
            refined = refine_book(path)
            if refined:
                results.append(refined)
        except Exception as e:
            print("Failed to refine", path, e)
    return results

def run_publishing_network():
    cleanup_empty_books()
    category_key = os.getenv("BOOK_CATEGORY")
    if category_key not in CATEGORIES:
        category_key = "romance"
    agent = os.getenv("BOOK_AGENT", "Agent_%04d" % random.randint(1, 3510))
    topic = random.choice(CATEGORIES[category_key]["topics"])
    book_info = write_full_novel(agent, category_key, topic, max_chapters=4)
    update_category_file(category_key, book_info)
    os.makedirs("books", exist_ok=True)
    catalog_path = "books/MASTER_CATALOG.json"
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = {"books": []}
    catalog.setdefault("books", []).append(book_info)
    catalog["total_books"] = len(catalog["books"])
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    return book_info

def run_continue():
    cleanup_empty_books()
    path = latest_book_to_continue()
    if path:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        print("Continuing unfinished book:", path, "words:", word_count(text), "parts:", story_parts(text))
        extra = 2 if is_childrens(category_from_path(path)) else 6
        return continue_book(path, extra_chapters=extra)
    print("No unfinished book. Starting a new one.")
    return run_publishing_network()

def book_status_row(path):
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    words = word_count(text)
    last = next_chapter_number(text) - 1
    parts = story_parts(text)
    cat = category_from_path(path)
    need_words, _ = complete_threshold(path)
    if words < (40 if is_childrens(cat) else 800):
        state = "empty"
    elif is_complete_novel(path):
        state = "complete"
    else:
        state = "incomplete"
    return {
        "file": str(path), "words": words, "last_chapter": max(0, last),
        "state": state, "category": cat, "need_words": need_words,
        "beginning": parts["beginning"], "middle": parts["middle"], "ending": parts["ending"],
    }

def write_book_status():
    root = Path("books")
    rows = []
    if root.exists():
        for path in sorted(root.rglob("*.txt")):
            name = path.name.lower()
            if name in ("category.json", "master_catalog.json") or "refined" in name:
                continue
            rows.append(book_status_row(path))
    lines = [
        "# Book Status",
        "Generated: " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "",
        "complete = minimum words for that age AND beginning + middle + ending",
        "Children's minimums: baby 80, picture 500, early 2500, chapter 8000, middle grade 20000",
        "Adult complete = 80000 + beginning/middle/ending",
        "",
    ]
    if not rows:
        lines.append("No books found.")
    else:
        for row in rows:
            lines.append(
                "- %s | %s | %s/%s words | ch %s | begin=%s mid=%s end=%s | %s" % (
                    row["category"], row["file"], row["words"], row["need_words"],
                    row["last_chapter"], row["beginning"], row["middle"], row["ending"], row["state"]
                )
            )
        counts = {}
        for row in rows:
            counts[row["state"]] = counts.get(row["state"], 0) + 1
        lines += ["", "## Counts"]
        for k, v in counts.items():
            lines.append("- %s: %s" % (k, v))
    Path("book-status.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote book-status.md")

def export_complete_books():
    root = Path("books")
    exported = []
    if not root.exists():
        print("No books folder")
        return []
    for path in root.rglob("*_full_*.txt"):
        if "refined" in path.name.lower():
            continue
        if not is_complete_novel(path):
            print("Not complete, skip export:", path)
            continue
        txt = str(path)
        txt_to_pdf(txt)
        txt_to_docx(txt)
        exported.append(txt)
        print("Exported complete book:", txt)
    print("Exported", len(exported), "complete books")
    return exported

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
            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict) and isinstance(data.get("results"), list):
                rows = data.get("results")
            elif isinstance(data, dict):
                rows = [data]
            else:
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if row.get("type") and row.get("type") != "bid":
                    continue
                job = row.get("job") if isinstance(row.get("job"), dict) else {}
                title = job.get("title") or row.get("title")
                if not title or title == "untitled":
                    continue
                status = str(row.get("status") or "").lower()
                line = "- team=%s | status=%s | code=%s | job=%s" % (
                    row.get("team") or "unknown",
                    status,
                    row.get("response_code"),
                    title
                )
                if status == "applied":
                    toku_applied.append(line)
                elif status in ("apply_failed", "already_bid"):
                    toku_failed.append(line)

    lines = [
        "# Fleet Report",
        "Generated: " + now.strftime("%Y-%m-%d %H:%M UTC"),
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--export-complete", action="store_true")
    parser.add_argument("--continue", dest="do_continue", action="store_true")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()

    if args.cleanup:
        cleanup_empty_books()
    elif args.status:
        write_book_status()
    elif args.export_complete:
        export_complete_books()
    elif args.do_continue:
        run_continue()
    elif args.report:
        write_fleet_report()
    elif args.refine:
        run_refine(limit=args.limit)
    else:
        run_publishing_network()
