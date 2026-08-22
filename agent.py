import os
import json
import random
import argparse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from groq import Groq
from fpdf import FPDF
from docx import Document

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GROQ_MODELS = [
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.6-27b",
]

CATEGORIES = {
    "childrens": {
        "folder": "books/childrens",
        "age": "ages 6-10",
        "style": "warm fun and safe",
        "topics": ["talking animals", "friendship", "bedtime adventure"],
        "public_domain": []
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional and character-driven",
        "topics": ["second chance", "enemies to lovers", "slow burn"],
        "public_domain": [161, 1342]
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy and explicit",
        "topics": ["dark mafia romance", "forced proximity"],
        "public_domain": []
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "investigative and gripping",
        "topics": ["unsolved disappearance", "small town murder"],
        "public_domain": [2852]
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "fast and twisty",
        "topics": ["missing wife", "witness protection"],
        "public_domain": [1661]
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "magical and adventurous",
        "topics": ["hidden heir", "dragon academy"],
        "public_domain": [55, 12]
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic",
        "topics": ["colony ship", "AI uprising"],
        "public_domain": [36, 35]
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "clear and useful",
        "topics": ["habit building", "money basics"],
        "public_domain": [1232]
    },
    "horror": {
        "folder": "books/horror",
        "age": "adult",
        "style": "creepy and atmospheric",
        "topics": ["haunted lake house", "cult in the woods"],
        "public_domain": [345, 43]
    }
}

BOOKS_PER_CATEGORY = 1
REWRITE_CHANCE = 0.3

def safe_name(text):
    cleaned = []
    for c in text:
        if c.isalnum() or c in "-_ ":
            cleaned.append(c)
    return "".join(cleaned).strip().replace(" ", "_")[:80]

def generate_with_fallback(messages):
    last_error = None
    for model in GROQ_MODELS:
        try:
            print("Trying model:", model)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.95,
                max_tokens=3000
            )
            print("Using model:", model)
            return response
        except Exception as e:
            print("Model failed:", model, e)
            last_error = e
    raise RuntimeError(last_error)

def fetch_public_domain(book_id):
    url1 = "https://www.gutenberg.org/cache/epub/%s/pg%s.txt" % (book_id, book_id)
    url2 = "https://www.gutenberg.org/files/%s/%s-0.txt" % (book_id, book_id)
    for url in [url1, url2]:
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                text = res.read().decode("utf-8", errors="ignore")
            return text[:4000]
        except Exception as e:
            print("Could not fetch", url, e)
    return None

def txt_to_pdf(txt_path):
    pdf_path = txt_path.replace(".txt", ".pdf")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            safe = line.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 8, safe.strip())
    pdf.output(pdf_path)
    print("PDF saved:", pdf_path)
    return pdf_path

def txt_to_docx(txt_path):
    docx_path = txt_path.replace(".txt", ".docx")
    doc = Document()
    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                doc.add_paragraph(text)
            else:
                doc.add_paragraph("")
    doc.save(docx_path)
    print("DOCX saved:", docx_path)
    return docx_path

def write_book(agent_name, category_key, topic, source_text=None):
    cat = CATEGORIES[category_key]
    if source_text:
        system_prompt = "You are %s. Rewrite a public-domain book in natural human language. Category: %s. Audience: %s. Style: %s. Make it feel original. If children's, keep it age-appropriate." % (agent_name, category_key, cat["age"], cat["style"])
        user_prompt = "Modernize this source into a 12-chapter novel about %s.\n\nSOURCE:\n%s" % (topic, source_text)
        mode = "rewrite"
    else:
        system_prompt = "You are %s. Write an original novel in natural human language. Audience: %s. Style: %s. If children's, keep it age-appropriate." % (agent_name, cat["age"], cat["style"])
        user_prompt = "Write an original 12-chapter novel about %s. Include title, author %s, blurb, and full chapters." % (topic, agent_name)
        mode = "original"

    response = generate_with_fallback([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

    book_text = response.choices[0].message.content
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "%s/%s_%s_%s_%s.txt" % (
        cat["folder"],
        safe_name(agent_name),
        safe_name(topic),
        mode,
        timestamp
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(book_text)

    print("Saved:", filename)
    txt_to_pdf(filename)
    txt_to_docx(filename)

    info = {}
    info["agent"] = agent_name
    info["category"] = category_key
    info["topic"] = topic
    info["mode"] = mode
    info["file"] = filename
    info["pdf"] = filename.replace(".txt", ".pdf")
    info["docx"] = filename.replace(".txt", ".docx")
    info["created_at"] = timestamp
    return info

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

def run_publishing_network(agent_names=None):
    if not agent_names:
        agent_names = ["Agent_%04d" % i for i in range(1, 21)]

    all_results = []
    for category_key, cat in CATEGORIES.items():
        for _ in range(BOOKS_PER_CATEGORY):
            agent = random.choice(agent_names)
            topic = random.choice(cat["topics"])
            source_text = None
            if cat["public_domain"] and random.random() < REWRITE_CHANCE:
                book_id = random.choice(cat["public_domain"])
                source_text = fetch_public_domain(book_id)
            book_info = write_book(agent, category_key, topic, source_text)
            update_category_file(category_key, book_info)
            all_results.append(book_info)

    os.makedirs("books", exist_ok=True)
    with open("books/MASTER_CATALOG.json", "w", encoding="utf-8") as f:
        json.dump({"total_books": len(all_results), "books": all_results}, f, indent=2)
    print("Created", len(all_results), "books")
    return all_results

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

    toku_jobs = {"applied": [], "accepted": [], "completed": []}
    jobs_path = Path("toku/jobs.json")
    if jobs_path.exists():
        with open(jobs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        jobs = data.get("jobs", data if isinstance(data, list) else [])
        for job in jobs:
            status = str(job.get("status", "")).lower()
            if status in toku_jobs:
                toku_jobs[status].append(job)

    lines = [
        "# Fleet Report",
        "Generated: " + now.strftime("%Y-%m-%d %H:%M UTC"),
        "Window: last 4 hours",
        "Files created: %s" % len(created),
        "Toku applied: %s" % len(toku_jobs["applied"]),
        "Toku accepted: %s" % len(toku_jobs["accepted"]),
        "Toku completed: %s" % len(toku_jobs["completed"]),
        "",
        "## Created in the last 4 hours"
    ]
    lines.extend(created or ["None"])
    lines += ["", "## Toku jobs"]
    for status in ("applied", "accepted", "completed"):
        lines.append("### " + status.title())
        if toku_jobs[status]:
            for job in toku_jobs[status]:
                lines.append("- %s | %s" % (job.get("agent", "unknown"), job.get("title", "untitled")))
        else:
            lines.append("None")

    with open("fleet-report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("Updated fleet-report.md")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()
    if args.report:
        write_fleet_report()
    else:
        run_publishing_network()
