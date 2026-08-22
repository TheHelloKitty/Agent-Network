import os
import json
import random
import time
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from openai import OpenAI
from fpdf import FPDF
from docx import Document

OPENROUTER_MODELS = [
    "google/gemini-2.0-flash-001",
    "meta-llama/llama-3.3-70b-instruct",
    "qwen/qwen-2.5-72b-instruct",
    "mistralai/mistral-small-3.1-24b-instruct",
]

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
        "style": "investigative, scene-by-scene, spoken interviews",
        "topics": ["unsolved disappearance", "small town murder"],
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

def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it in GitHub Secrets.")
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

def safe_name(text):
    cleaned = []
    for c in text:
        if c.isalnum() or c in "-_ ":
            cleaned.append(c)
    return "".join(cleaned).strip().replace(" ", "_")[:80]

def word_count(text):
    return len(text.split())

def generate_with_fallback(messages):
    last_error = None
    client = get_client()
    for model in OPENROUTER_MODELS:
        try:
            print("Trying model:", model)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.95,
                max_tokens=3000
            )
            print("Using model:", model)
            return response.choices[0].message.content
        except Exception as e:
            print("Model failed:", model, e)
            last_error = e
            time.sleep(2)
    raise RuntimeError(last_error)

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

    outline_prompt = [
        {
            "role": "system",
            "content": "You are %s, a novelist. Write in natural human language." % agent_name
        },
        {
            "role": "user",
            "content": "Create a title, blurb, character list, and a %s-chapter outline for an original %s book about %s. Audience: %s. Target length: %s words. Use dialogue and description." % (CHAPTERS, category_key, topic, cat["age"], TARGET_WORDS)
        }
    ]
    outline = generate_with_fallback(outline_prompt)

    parts = [outline]
    with open(filename, "w", encoding="utf-8") as f:
        f.write(outline + "\n\n")

    previous = outline[-1500:]
    last_chapter = 0

    for chapter in range(1, CHAPTERS + 1):
        chapter_text = ""
        while word_count(chapter_text) < WORDS_PER_CHAPTER:
            user = "Write the next section of Chapter %s of this original novel.\n" % chapter
            user += "Category: %s\nTopic: %s\nStyle: %s\n" % (category_key, topic, cat["style"])
            user += "Use natural dialogue and physical description.\n"
            user += "Do not summarize. Write actual scenes.\n"
            user += "Continue from this:\n%s" % previous

            if category_key == "childrens":
                user += "\nKeep this completely appropriate for children ages 6-10."

            chunk = generate_with_fallback([
                {
                    "role": "system",
                    "content": "You are %s. Write like a human novelist, not an AI. Put people in rooms. Let them talk. Describe what they see and feel." % agent_name
                },
                {
                    "role": "user",
                    "content": user
                }
            ])
            chapter_text = chapter_text + "\n\n" + chunk
            previous = chunk[-1500:]
            time.sleep(1)
            total_now = word_count("\n".join(parts) + chapter_text)
            if total_now >= TARGET_WORDS:
                break

        header = "\n\nCHAPTER %s\n\n" % chapter
        with open(filename, "a", encoding="utf-8") as f:
            f.write(header + chapter_text + "\n")
        parts.append(header + chapter_text)
        last_chapter = chapter
        total_words = word_count("\n".join(parts))
        print("Chapter", chapter, "saved. Words so far:", total_words)
        if total_words >= TARGET_WORDS:
            break

    add_table_of_contents(filename, last_chapter)
    txt_to_pdf(filename)
    txt_to_docx(filename)

    info = {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
        "file": filename,
        "words": word_count("\n".join(parts)),
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
    character_bible = generate_with_fallback(bible_prompt)

    refined_parts = []
    refined_parts.append(character_bible)
    refined_parts.append("\n\n--- REFINED NOVEL ---\n\n")

    chunks = chunk_text(original, max_chars=6000)
    previous_summary = "Beginning of book."

    for i, chunk in enumerate(chunks, start=1):
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are a professional fiction editor. "
                    "Improve clarity, dialogue, pacing, and character continuity. "
                    "Do not invent a totally new plot. Keep the same story. "
                    "Preserve chapter structure when present."
                )
            },
            {
                "role": "user",
                "content": (
                    "Edit this section into stronger prose.\n"
                    "Requirements:\n"
                    "1. Keep character continuity exact to the bible below\n"
                    "2. Improve dialogue so it sounds spoken\n"
                    "3. Cut repetition\n"
                    "4. Strengthen scene goals\n"
                    "5. Keep children's content age-appropriate if this is a children's book\n"
                    "6. Do not summarize. Return full rewritten scenes\n\n"
                    "CHARACTER BIBLE:\n%s\n\n"
                    "PREVIOUS CONTEXT:\n%s\n\n"
                    "SECTION %s:\n%s"
                ) % (character_bible, previous_summary, i, chunk)
            }
        ]
        edited = generate_with_fallback(prompt)
        refined_parts.append(edited)
        previous_summary = edited[-1200:]
        print("Refined section", i, "of", len(chunks))
        time.sleep(1)

    refined_text = "\n\n".join(refined_parts)
    out_path = str(txt_path).replace(".txt", "_refined.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(refined_text)

    add_table_of_contents(out_path, CHAPTERS)
    txt_to_pdf(out_path)
    txt_to_docx(out_path)
    print("Refined book saved:", out_path)
    return out_path

def run_refine(limit=5):
    files = list_book_files(limit=limit)
    if not files:
        print("No books found to refine")
        return []
    results = []
    for path in files:
        try:
            results.append(refine_book(path))
        except Exception as e:
            print("Failed to refine", path, e)
    print("Refined", len(results), "books")
    return results

def run_publishing_network():
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
    for folder in ["agent_outputs", "books", "storefront_exports", "novels", "toku"]:
        if not os.path.isdir(folder):
            continue
        for path in Path(folder).rglob("*"):
            if path.is_file():
                mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if mtime >= cutoff:
                    created.append("- %s | %s | %s" % (path.stem.split("_")[0], folder, path))
    lines = [
        "# Fleet Report",
        "Generated: " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "Window: last 4 hours",
        "Files created: %s" % len(created),
        "",
        "## Created in the last 4 hours"
    ]
    lines.extend(created or ["None"])
    with open("fleet-report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Updated fleet-report.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--refine", action="store_true")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    if args.report:
        write_fleet_report()
    elif args.refine:
        run_refine(limit=args.limit)
    else:
        run_publishing_network()
