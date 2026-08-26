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
WORDS_PER_CHAPTER = 4500
MIN_KEEP_WORDS = 800

def generate_with_fallback(messages, temperature=0.95, max_tokens=3000):
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

def add_table_of_contents(filename, chapter_count):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    toc_lines = ["TABLE OF CONTENTS", ""]
    for i in range(1, chapter_count + 1):
        toc_lines.append("Chapter %s" % i)
    toc_lines.append("")
    toc_text = "\n".join(toc_lines)
    parts = content.split("\n\n", 1)
    if len(parts) == 2:
        new_content = parts[0] + "\n\n" + toc_text + "\n\n" + parts[1]
    else:
        new_content = toc_text + "\n\n" + content
    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Table of contents added")

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
        if "chapter plan pending" in low and word_count(text) < min_words:
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
    for r in removed:
        print(" -", r)
    return removed

def true_crime_system_prompt(agent_name):
    return (
        "You are %s, a factual true-crime chronicler. "
        "Write only verified public facts. "
        "No opinions. No speculation. No invented dialogue. "
        "No invented motives. No dramatic commentary. "
        "Use dates, locations, charges, court actions, and publicly reported events only. "
        "If something is unconfirmed, omit it. "
        "Present events in chronological order."
    ) % agent_name

def normal_system_prompt(agent_name):
    return (
        "You are %s. Write like a human novelist, not an AI. "
        "Put people in rooms. Let them talk. Describe what they see and feel."
    ) % agent_name

def build_outline_prompt(agent_name, category_key, topic, cat):
    if category_key == "true_crime":
        return [
            {
                "role": "system",
                "content": true_crime_system_prompt(agent_name)
            },
            {
                "role": "user",
                "content": (
                    "Create a factual true-crime book plan about: %s\n\n"
                    "Include:\n"
                    "1. Working title\n"
                    "2. One-paragraph factual summary\n"
                    "3. Key publicly known figures\n"
                    "4. A %s-chapter chronological outline based only on public facts\n\n"
                    "Rules:\n"
                    "- Facts only\n"
                    "- No opinions\n"
                    "- No speculation\n"
                    "- No invented scenes\n"
                    "- Target length about %s words"
                ) % (topic, CHAPTERS, TARGET_WORDS)
            }
        ]
    return [
        {
            "role": "system",
            "content": "You are %s, a novelist. Write in natural human language." % agent_name
        },
        {
            "role": "user",
            "content": (
                "Create a title, blurb, character list, and a %s-chapter outline for an original %s book about %s. "
                "Audience: %s. Target length: %s words. Use dialogue and description."
            ) % (CHAPTERS, category_key, topic, cat["age"], TARGET_WORDS)
        }
    ]

def build_chapter_prompt(agent_name, category_key, topic, cat, chapter, previous):
    if category_key == "true_crime":
        system = true_crime_system_prompt(agent_name)
        user = (
            "Write the next factual section for Chapter %s of a true-crime account about: %s\n\n"
            "Rules:\n"
            "- Facts only\n"
            "- Public reporting / public-record framing only\n"
            "- Timeline style\n"
            "- No commentary\n"
            "- No opinions\n"
            "- No fictional scenes\n"
            "- No invented dialogue\n"
            "- Continue from this prior text:\n%s"
        ) % (chapter, topic, previous)
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

    system = normal_system_prompt(agent_name)
    user = (
        "Write the next section of Chapter %s of this original novel.\n"
        "Category: %s\nTopic: %s\nStyle: %s\n"
        "Use natural dialogue and physical description.\n"
        "Do not summarize. Write actual scenes.\n"
        "Continue from this:\n%s"
    ) % (chapter, category_key, topic, cat["style"], previous)

    if category_key == "childrens":
        user += "\nKeep this completely appropriate for children ages 6-10."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]

def write_full_novel(agent_name, category_key, topic):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "%s/%s_%s_full_%s.txt" % (
        cat["folder"],
        safe_name(agent_name),
        safe_name(topic),
        timestamp
    )

    outline_prompt = build_outline_prompt(agent_name, category_key, topic, cat)

    try:
        outline = generate_with_fallback(
            outline_prompt,
            temperature=0.2 if category_key == "true_crime" else 0.95
        )
    except Exception as e:
        print("Outline failed:", e)
        outline = ""

    if word_count(outline) < 40:
        print("Outline too weak. Aborting empty book.")
        raise RuntimeError("Outline generation failed")

    parts = [outline]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(outline + "\n\n")

    previous = outline[-1500:]
    last_chapter = 0

    for chapter in range(1, CHAPTERS + 1):
        chapter_text = ""
        tries = 0
        while word_count(chapter_text) < WORDS_PER_CHAPTER:
            tries += 1
            if tries > 8:
                print("Too many retries on chapter", chapter)
                break

            prompt = build_chapter_prompt(
                agent_name, category_key, topic, cat, chapter, previous
            )

            try:
                chunk = generate_with_fallback(
                    prompt,
                    temperature=0.2 if category_key == "true_crime" else 0.95
                )
            except Exception as e:
                print("Generation failed on chapter", chapter, e)
                time.sleep(20)
                continue

            if not chunk or word_count(chunk) < 20:
                print("Empty chunk on chapter", chapter)
                time.sleep(3)
                continue

            chapter_text = chapter_text + "\n\n" + chunk
            previous = chunk[-1500:]
            time.sleep(3)
            total_now = word_count("\n".join(parts) + chapter_text)
            if total_now >= TARGET_WORDS:
                break

        if word_count(chapter_text) < 50:
            print("Skipping empty chapter", chapter)
            continue

        header = "\n\nCHAPTER %s\n\n" % chapter
        with open(filename, "a", encoding="utf-8") as f:
            f.write(header + chapter_text + "\n")
        parts.append(header + chapter_text)
        last_chapter = chapter
        total_words = word_count("\n".join(parts))
        print("Chapter", chapter, "saved. Words so far:", total_words)
        time.sleep(5)
        if total_words >= TARGET_WORDS:
            break

    final_words = word_count("\n".join(parts))
    if final_words < MIN_KEEP_WORDS:
        print("Book undeveloped. Deleting", filename)
        delete_book_family(filename)
        raise RuntimeError("Refusing to keep empty/undeveloped book (%s words)" % final_words)

    if last_chapter < 1:
        last_chapter = 1

    add_table_of_contents(filename, last_chapter)
    txt_to_pdf(filename)
    txt_to_docx(filename)

    info = {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
        "file": filename,
        "words": final_words,
        "chapters": last_chapter,
        "created_at": timestamp
    }
    print("Novel saved:", filename, "words:", info["words"])
    return info

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

def list_book_files(limit=5):
    files = []
    books_root = Path("books")
    if not books_root.exists():
        return []
    for path in books_root.rglob("*.txt"):
        name = path.name.lower()
        if "refined" in name:
            continue
        if name == "category.json":
            continue
        if is_undeveloped_book(path):
            continue
        files.append(path)
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]

def chunk_text(text, max_chars=6000):
    chunks = []
    current = []
    size = 0
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        if size + len(para) > max_chars and current:
            chunks.append("\n\n".join(current))
            current = [para]
            size = len(para)
        else:
            current.append(para)
            size += len(para)
    if current:
        chunks.append("\n\n".join(current))
    return chunks

def refine_book(txt_path):
    print("Refining:", txt_path)
    with open(txt_path, "r", encoding="utf-8") as f:
        original = f.read()

    if word_count(original) < MIN_KEEP_WORDS:
        print("Skipping refine on undeveloped book")
        return None

    is_true_crime = "true_crime" in str(txt_path).lower()

    if is_true_crime:
        bible_prompt = [
            {
                "role": "system",
                "content": "Extract only factual entities and timeline points. No opinions."
            },
            {
                "role": "user",
                "content": (
                    "From this true-crime draft, extract:\n"
                    "- key people\n- key dates\n- locations\n- charges or court actions\n"
                    "- factual timeline points only\n\n"
                    "DRAFT:\n%s" % original[:12000]
                )
            }
        ]
    else:
        bible_prompt = [
            {
                "role": "system",
                "content": "You are a continuity editor. Extract stable character facts only."
            },
            {
                "role": "user",
                "content": (
                    "From this novel draft, create a short character continuity bible.\n"
                    "For each important character list:\n"
                    "- name\n- age if known\n- appearance\n- personality\n- relationships\n- goals\n"
                    "- facts that must stay consistent\n\n"
                    "DRAFT:\n%s" % original[:12000]
                )
            }
        ]

    try:
        character_bible = generate_with_fallback(bible_prompt, temperature=0.2)
    except Exception as e:
        print("Bible failed:", e)
        character_bible = "Continuity notes unavailable."

    refined_parts = [character_bible, "\n\n--- REFINED TEXT ---\n\n"]
    chunks = chunk_text(original, max_chars=6000)
    previous_summary = "Beginning of book."

    for i, chunk in enumerate(chunks, start=1):
        if is_true_crime:
            prompt = [
                {
                    "role": "system",
                    "content": (
                        "You are a factual true-crime editor. "
                        "Keep only facts. Remove opinions, speculation, invented dialogue, and dramatic commentary."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "Edit this section for factual clarity only.\n"
                        "Do not add new claims.\n"
                        "Do not speculate.\n"
                        "Keep chronological order.\n\n"
                        "FACT NOTES:\n%s\n\nPREVIOUS CONTEXT:\n%s\n\nSECTION %s:\n%s"
                    ) % (character_bible, previous_summary, i, chunk)
                }
            ]
            temp = 0.2
        else:
            prompt = [
                {
                    "role": "system",
                    "content": "You are a professional fiction editor. Improve clarity, dialogue, pacing, and character continuity. Do not invent a totally new plot."
                },
                {
                    "role": "user",
                    "content": (
                        "Edit this section into stronger prose.\n"
                        "Keep character continuity exact to the bible.\n"
                        "Do not summarize. Return full rewritten scenes.\n\n"
                        "CHARACTER BIBLE:\n%s\n\nPREVIOUS CONTEXT:\n%s\n\nSECTION %s:\n%s"
                    ) % (character_bible, previous_summary, i, chunk)
                }
            ]
            temp = 0.5

        try:
            edited = generate_with_fallback(prompt, temperature=temp)
        except Exception as e:
            print("Refine section failed:", i, e)
            time.sleep(20)
            edited = chunk
        refined_parts.append(edited)
        previous_summary = edited[-1200:]
        print("Refined section", i, "of", len(chunks))
        time.sleep(3)

    out_path = str(txt_path).replace(".txt", "_refined.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(refined_parts))

    if is_undeveloped_book(out_path):
        print("Refined output undeveloped. Deleting", out_path)
        delete_book_family(out_path)
        return None

    add_table_of_contents(out_path, CHAPTERS)
    txt_to_pdf(out_path)
    txt_to_docx(out_path)
    print("Refined book saved:", out_path)
    return out_path

def run_refine(limit=5):
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
    print("Refined", len(results), "books")
    return results

def run_publishing_network():
    cleanup_empty_books()
    category_key = os.getenv("BOOK_CATEGORY")
    if category_key not in CATEGORIES:
        category_key = random.choice(list(CATEGORIES.keys()))
    cat = CATEGORIES[category_key]
    agent = os.getenv("BOOK_AGENT", "Agent_%04d" % random.randint(1, 3510))
    topic = random.choice(cat["topics"])
    book_info = write_full_novel(agent, category_key, topic)
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

def write_fleet_report():
    hours = 4
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    created = []
    books_completed = []
    refined_books = []
    toku_events = []

    for folder in ["agent_outputs", "books", "storefront_exports", "novels", "toku", "security_team"]:
        if not os.path.isdir(folder):
            continue
        for path in Path(folder).rglob("*"):
            if not path.is_file():
                continue
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue

            rel = str(path)
            created.append("- %s | %s | %s" % (path.stem.split("_")[0], folder, rel))

            name = path.name.lower()
            if folder.startswith("books") and name.endswith(".txt") and "refined" not in name:
                if not is_undeveloped_book(path):
                    books_completed.append("- %s (%s words)" % (rel, word_count(path.read_text(encoding="utf-8", errors="ignore"))))
            if folder.startswith("books") and "_refined" in name and name.endswith(".txt"):
                if not is_undeveloped_book(path):
                    refined_books.append("- %s" % rel)

    toku_dir = Path("toku")
    if toku_dir.exists():
        for path in toku_dir.rglob("*.json"):
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            rows = data if isinstance(data, list) else [data]
            for row in rows:
                team = row.get("team") or "unknown"
                job = row.get("job") or {}
                title = job.get("title") or row.get("title") or "untitled job"
                status = str(row.get("status") or "unknown").lower()
                toku_events.append(
                    "- team=%s | status=%s | job=%s | file=%s" % (
                        team, status, title, path.name
                    )
                )

    lines = [
        "# Fleet Report",
        "Generated: " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "Window: last 4 hours",
        "",
        "## Summary",
        "Files created: %s" % len(created),
        "Developed books completed: %s" % len(books_completed),
        "Books refined: %s" % len(refined_books),
        "Toku job events: %s" % len(toku_events),
        "",
        "## Created in the last 4 hours",
    ]
    lines.extend(created or ["None"])
    lines.append("")
    lines.append("## Developed books completed")
    lines.extend(books_completed or ["None"])
    lines.append("")
    lines.append("## Successful books after refine pass")
    lines.extend(refined_books or ["None"])
    lines.append("")
    lines.append("## Toku jobs (applied / accepted / completed)")
    lines.extend(toku_events or ["None"])

    with open("fleet-report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Updated fleet-report.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.cleanup:
        cleanup_empty_books()
    elif args.report:
        write_fleet_report()
    elif args.refine:
        run_refine(limit=args.limit)
    else:
        run_publishing_network()
