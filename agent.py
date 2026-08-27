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
    "childrens": {
        "folder": "books/childrens",
        "age": "ages 6-10",
        "style": "warm, fun, safe, lots of talk and simple scenes",
        "topics": ["talking animals", "friendship", "bedtime adventure"],
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
        "style": "strictly factual, timeline-based, public-record only, no opinions",
        "topics": [
            "Julio Foolio case public timeline",
            "McKenzie Shirilla case public court coverage",
            "recent headline cases from public reporting only"
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

CHAPTERS = 20
TARGET_WORDS = 90000
MIN_KEEP_WORDS = 800
CONTINUE_MIN_WORDS = 80
CONTINUE_CHAPTERS = 3

def generate_with_fallback(messages, temperature=0.95, max_tokens=800):
    return generate_with_failover(
        messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

def safe_name(text):
    cleaned = []
    for c in text:
        if c.isalnum() or c in "-_ ":
            cleaned.append(c)
    return "".join(cleaned).strip().replace(" ", "_")[:80]

def word_count(text):
    return len((text or "").split())

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
                print("Deleted:", sib)
        except Exception as e:
            print("Could not delete", sib, e)

def is_undeveloped_book(path, min_words=MIN_KEEP_WORDS):
    try:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return True
        if p.stat().st_size < 200:
            return True
        text = p.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return True
        low = text.lower()
        if "draft in progress" in low and word_count(text) < min_words:
            return True
        if word_count(text) < min_words:
            return True
        return False
    except Exception:
        return True

def cleanup_empty_books(min_words=MIN_KEEP_WORDS):
    root = Path("books")
    if not root.exists():
        print("No books folder")
        return []
    removed = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name.lower() in ("category.json", "master_catalog.json"):
            continue
        if path.suffix.lower() == ".txt":
            if is_undeveloped_book(path, min_words=min_words):
                for sib in [path, path.with_suffix(".pdf"), path.with_suffix(".docx")]:
                    if sib.exists():
                        sib.unlink(missing_ok=True)
                        removed.append(str(sib))
            continue
        if path.suffix.lower() in [".pdf", ".docx"]:
            txt = path.with_suffix(".txt")
            if txt.exists() and is_undeveloped_book(txt, min_words=min_words):
                path.unlink(missing_ok=True)
                removed.append(str(path))
            elif not txt.exists() and path.stat().st_size < 1000:
                path.unlink(missing_ok=True)
                removed.append(str(path))
    print("Removed undeveloped files:", len(removed))
    return removed

def true_crime_system_prompt(agent_name):
    return (
        "You are %s, a factual true-crime chronicler. "
        "Write only verified public facts. No opinions. No speculation. "
        "No invented dialogue. If something is unconfirmed, omit it."
    ) % agent_name

def normal_system_prompt(agent_name):
    return (
        "You are %s. Write like a human novelist. "
        "Put people in rooms. Let them talk. Describe what they see and feel."
    ) % agent_name

def build_outline_prompt(agent_name, category_key, topic, cat):
    if category_key == "true_crime":
        return [
            {"role": "system", "content": true_crime_system_prompt(agent_name)},
            {"role": "user", "content": (
                "Create a factual true-crime book plan about: %s. "
                "Include a working title, factual summary, key public figures, "
                "and a short chronological outline. Facts only."
            ) % topic}
        ]
    return [
        {"role": "system", "content": "You are %s, a novelist." % agent_name},
        {"role": "user", "content": (
            "Create a title, short blurb, character list, and a compact chapter outline "
            "for an original %s book about %s. Audience: %s."
        ) % (category_key, topic, cat["age"])}
    ]

def build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous):
    if category_key == "true_crime":
        return [
            {"role": "system", "content": true_crime_system_prompt(agent_name)},
            {"role": "user", "content": (
                "Write the next factual section for Chapter %s about: %s. "
                "Facts only. Timeline style. No invented dialogue.\nContinue from:\n%s"
            ) % (chapter, topic, previous)}
        ]
    user = (
        "Write the next section of Chapter %s.\n"
        "Category: %s\nTopic: %s\nStyle: %s\n"
        "Use dialogue and description. Do not summarize.\nContinue from:\n%s"
    ) % (chapter, category_key, topic, cat["style"], previous)
    if category_key == "childrens":
        user += "\nKeep this appropriate for children ages 6-10."
    return [
        {"role": "system", "content": normal_system_prompt(agent_name)},
        {"role": "user", "content": user}
    ]

def write_full_novel(agent_name, category_key, topic, max_chapters=4):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "%s/%s_%s_full_%s.txt" % (
        cat["folder"], safe_name(agent_name), safe_name(topic), timestamp
    )
    try:
        outline = generate_with_fallback(
            build_outline_prompt(agent_name, category_key, topic, cat),
            temperature=0.2 if category_key == "true_crime" else 0.9
        )
    except Exception as e:
        print("Outline failed:", e)
        outline = ""
    if word_count(outline) < 30:
        raise RuntimeError("Outline generation failed")

    parts = [outline]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(outline + "\n\n")
    previous = outline[-1500:]
    last_chapter = 0

    for chapter in range(1, max_chapters + 1):
        chapter_text = ""
        tries = 0
        while word_count(chapter_text) < 400 and tries < 6:
            tries += 1
            try:
                chunk = generate_with_fallback(
                    build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous),
                    temperature=0.2 if category_key == "true_crime" else 0.9
                )
            except Exception as e:
                print("Generation failed on chapter", chapter, e)
                break
            if chunk and word_count(chunk) >= 20:
                chapter_text += "\n\n" + chunk
                previous = chunk[-1500:]
            time.sleep(2)
        if word_count(chapter_text) < 20:
            break
        header = "\n\nCHAPTER %s\n\n" % chapter
        with open(filename, "a", encoding="utf-8") as f:
            f.write(header + chapter_text + "\n")
        parts.append(header + chapter_text)
        last_chapter = chapter
        print("Chapter", chapter, "saved. Words so far:", word_count("\n".join(parts)))
        time.sleep(2)

    final_words = word_count("\n".join(parts))
    if final_words < CONTINUE_MIN_WORDS:
        delete_book_family(filename)
        raise RuntimeError("Refusing to keep empty book (%s words)" % final_words)

    info = {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
        "file": filename,
        "words": final_words,
        "chapters": last_chapter,
        "created_at": timestamp
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
        files.append(path)
    if not files:
        return None
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[0]

def next_chapter_number(text):
    n = 0
    for line in text.splitlines():
        s = line.strip().upper()
        if s.startswith("CHAPTER "):
            parts = s.replace("CHAPTER", "").strip().split()
            if parts and parts[0].isdigit():
                n = max(n, int(parts[0]))
    return n + 1

def continue_book(path, extra_chapters=CONTINUE_CHAPTERS):
    print("Continuing:", path)
    text = Path(path).read_text(encoding="utf-8", errors="ignore")
    start_chapter = next_chapter_number(text)
    previous = text[-1500:] if text else "Start of book."
    added = 0
    category_key = "romance"
    for key, cat in CATEGORIES.items():
        if cat["folder"] in str(path):
            category_key = key
            break
    cat = CATEGORIES[category_key]
    topic = path.stem
    agent_name = "Agent_Continue"

    for chapter in range(start_chapter, start_chapter + extra_chapters):
        chapter_text = ""
        tries = 0
        while word_count(chapter_text) < 400 and tries < 6:
            tries += 1
            try:
                chunk = generate_with_fallback(
                    build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous),
                    temperature=0.8
                )
            except Exception as e:
                print("Continue generation failed:", e)
                break
            if chunk and word_count(chunk) >= 20:
                chapter_text += "\n\n" + chunk
                previous = chunk[-1500:]
            time.sleep(2)
        if word_count(chapter_text) < 20:
            break
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\nCHAPTER %s\n\n%s\n" % (chapter, chapter_text))
        added += 1
        print("Added chapter", chapter)
        time.sleep(2)
    print("Added chapters this run:", added)
    return str(path)

def update_category_file(category_key, book_info):
    cat = CATEGORIES[category_key]
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
    print("Refining:", txt_path)
    original = Path(txt_path).read_text(encoding="utf-8", errors="ignore")
    if word_count(original) < MIN_KEEP_WORDS:
        print("Skipping refine on undeveloped book")
        return None
    prompt = [
        {"role": "system", "content": "You are a professional editor. Improve clarity and keep the plot."},
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
    if is_undeveloped_book(out_path, min_words=80):
        delete_book_family(out_path)
        return None
    print("Refined book saved:", out_path)
    return out_path

def run_refine(limit=2):
    files = list_book_files(limit=limit)
    if not files:
        print("No developed books found to refine")
        return []
    results = []
    for path in files:
        try:
            refined = refine_book(path)
            if refined:
                results.append(refined)
        except Exception as e:
            print("Failed to refine", path, e)
    return results

def run_publishing_network():
    cleanup_empty_books(min_words=CONTINUE_MIN_WORDS)
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
    cleanup_empty_books(min_words=CONTINUE_MIN_WORDS)
    path = latest_book_to_continue()
    if path and word_count(Path(path).read_text(encoding="utf-8", errors="ignore")) >= CONTINUE_MIN_WORDS:
        return continue_book(path, extra_chapters=CONTINUE_CHAPTERS)
    print("No book to continue. Starting a new one.")
    return run_publishing_network()

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
    parser.add_argument("--continue", dest="do_continue", action="store_true")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()

    if args.cleanup:
        cleanup_empty_books()
    elif args.do_continue:
        run_continue()
    elif args.report:
        write_fleet_report()
    elif args.refine:
        run_refine(limit=args.limit)
    else:
        run_publishing_network()
