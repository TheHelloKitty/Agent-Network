import os
import json
import random
import argparse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
]

CATEGORIES = {
    "childrens": {
        "folder": "books/childrens",
        "age": "ages 6-10",
        "style": "warm, fun, safe, and easy to read",
        "topics": ["talking animals", "first day of school", "friendship", "bedtime adventure"],
        "public_domain": []
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional and character-driven",
        "topics": ["second chance", "enemies to lovers", "fake dating", "slow burn"],
        "public_domain": [161, 1342]
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy, explicit, and intense",
        "topics": ["dark mafia romance", "possessive anti-hero", "forced proximity"],
        "public_domain": []
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "investigative and gripping",
        "topics": ["unsolved disappearance", "small town murder", "cold case"],
        "public_domain": [2852]
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "fast, tense, and twisty",
        "topics": ["missing wife", "witness protection", "serial killer hunt"],
        "public_domain": [1661]
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "magical and adventurous",
        "topics": ["hidden heir", "dragon academy", "cursed kingdom"],
        "public_domain": [55, 12]
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic and cinematic",
        "topics": ["colony ship", "AI uprising", "time loop"],
        "public_domain": [36, 35]
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "clear, useful, and practical",
        "topics": ["habit building", "money basics", "focus"],
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
    return "".join(c if c.isalnum() or c in "-_ " else "" for c in text).strip().replace(" ", "_")[:80]

def generate_with_fallback(messages):
    last_error = None
    for model in GROQ_MODELS:
        try:
            print("Trying model:", model)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.95,
                max_tokens=8000
            )
            print("Using model:", model)
            return response
        except Exception as e:
            print("Model failed:", model, e)
            last_error = e
    raise RuntimeError(last_error)

def fetch_public_domain(book_id):
    urls = [
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
    ]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=30) as res:
                text = res.read().decode("utf-8", errors="ignore")
            return text[:12000]
        except Exception as e:
            print("Could not fetch", url, e)
    return None

def write_book(agent_name, category_key, topic, source_text=None):
    cat = CATEGORIES[category_key]

    if source_text:
        system_prompt = (
            f"You are {agent_name}, a novelist who writes in natural human language. "
            f"Rewrite this public-domain book into a modern original-feeling novel. "
            f"Change names, setting, and plot enough to make it fresh. "
            f"Keep it in the {category_key} category. Audience: {cat['age']}. "
            f"Style: {cat['style']}. Use normal spoken English, not robotic AI phrasing. "
            f"If this is a children's book, keep it completely age-appropriate."
        )
        user_prompt = (
            f"Modernize and rewrite this public-domain source into a 12-chapter novel.\n"
            f"Topic direction: {topic}\n\n"
            f"SOURCE:\n{source_text}"
        )
    else:
        system_prompt = (
            f"You are {agent_name}, a novelist who writes original books in natural human language. "
            f"Write like a real author, not like an AI. Use specific details, imperfect people, "
            f"and dialogue that sounds spoken. Audience: {cat['age']}. Style: {cat['style']}. "
            f"If this is a children's book, keep it completely age-appropriate."
        )
        user_prompt = (
            f"Write an original 12-chapter novel about {topic}. "
            f"Include a title, author name {agent_name}, a short blurb, and the full chapters. "
            f"Do not summarize. Write actual scenes."
        )

    response = generate_with_fallback([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

    book_text = response.choices[0].message.content
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode = "rewrite" if source_text else "original"
    filename = f"{cat['folder']}/{safe_name(agent_name)}_{safe_name(topic)}_{mode}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(book_text)

    print("Saved:", filename)
    return {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
        "mode": mode,
        "file": filename,
        "created_at": timestamp
    }

def update_category_file(category_key, book_info):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    index_path = f"{cat['folder']}/CATEGORY.json"
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
        agent_names = [f"Agent_{i:04d}" for i in range(1, 21)]

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
                    created.append(f"- {path.stem.split('_')[0]} | {folder} | {path}")

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
        f"Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"Window: last {hours} hours",
        f"Files created: {len(created)}",
        f"Toku applied: {len(toku_jobs['applied'])}",
        f"Toku accepted: {len(toku_jobs['accepted'])}",
        f"Toku completed: {len(toku_jobs['completed'])}",
        "",
        "## Created in the last 4 hours"
    ]
    lines.extend(created or ["None"])
    lines += ["", "## Toku jobs"]
    for status in ("applied", "accepted", "completed"):
        lines.append("### " + status.title())
        if toku_jobs[status]:
            for job in toku_jobs[status]:
                lines.append(f"- {job.get('agent', 'unknown')} | {job.get('title', 'untitled')}")
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
