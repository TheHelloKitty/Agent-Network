import os
import json
import random
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# -------------------------------------------------
# CATEGORIES
# Keep children's books clean and separate.
# -------------------------------------------------
CATEGORIES = {
    "childrens": {
        "folder": "books/childrens",
        "age": "ages 6-10",
        "style": "warm, fun, safe, imaginative, no scary or adult themes",
        "topics": [
            "talking animals",
            "first day of school",
            "lost and found",
            "friendship",
            "bedtime adventure",
            "kindness",
            "magic forest",
            "brave little robot"
        ]
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional, character-driven, satisfying ending",
        "topics": [
            "small town second chance",
            "enemies to lovers",
            "fake dating",
            "workplace romance",
            "slow burn",
            "billionaire romance"
        ]
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy, explicit, high tension, graphic love scenes",
        "topics": [
            "dark mafia romance",
            "possessive anti-hero",
            "forced proximity",
            "age gap",
            "one night stand",
            "why choose"
        ]
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "investigative, gripping, factual tone, no glorifying crime",
        "topics": [
            "unsolved disappearance",
            "small town murder",
            "con artist empire",
            "cold case reopened",
            "corrupt official",
            "infamous heist"
        ]
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "fast-paced, twists, high stakes",
        "topics": [
            "missing wife",
            "witness protection",
            "serial killer hunt",
            "spy betrayal",
            "locked-room mystery"
        ]
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "world-building, quest, magic, found family",
        "topics": [
            "hidden heir",
            "dragon academy",
            "cursed kingdom",
            "portal to another world",
            "witch and hunter"
        ]
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic, idea-driven, cinematic",
        "topics": [
            "colony ship",
            "AI uprising",
            "time loop",
            "first contact",
            "memory theft"
        ]
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "practical, clear, useful, chapter summaries",
        "topics": [
            "habit building",
            "money basics",
            "focus and productivity",
            "sleep better",
            "starting a side hustle",
            "public speaking"
        ]
    },
    "horror": {
        "folder": "books/horror",
        "age": "adult",
        "style": "atmospheric, creepy, escalating dread",
        "topics": [
            "haunted lake house",
            "cult in the woods",
            "something under the floor",
            "last night at the motel"
        ]
    }
}

# How many books to generate this run
BOOKS_PER_CATEGORY = 1
CHAPTERS = 12
WORDS_HINT = "full-length novel, 12 chapters, around 40,000-60,000 words if possible"

def safe_name(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_ " else "" for c in text).strip().replace(" ", "_")[:80]

def write_book(agent_name: str, category_key: str, topic: str):
    cat = CATEGORIES[category_key]

    system_prompt = f"""
You are {agent_name}, a professional author writing for the {category_key} category.
Audience: {cat['age']}.
Style: {cat['style']}.
Write a complete book, not a summary.
If this is a children's book, keep it completely age-appropriate.
"""

    user_prompt = f"""
Write a {WORDS_HINT}.

Category: {category_key}
Topic: {topic}

Include:
1. Title
2. Author name: {agent_name}
3. Short blurb
4. Target audience
5. Full chapter-by-chapter novel text

Make it feel finished and publishable.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9,
        max_tokens=8000
    )

    book_text = response.choices[0].message.content
    os.makedirs(cat["folder"], exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{cat['folder']}/{safe_name(agent_name)}_{safe_name(topic)}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(book_text)

    print(f"✅ Saved {category_key} book: {filename}")
    return {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
        "file": filename,
        "created_at": timestamp
    }

def update_category_file(category_key: str, book_info: dict):
    cat = CATEGORIES[category_key]
    os.makedirs(cat["folder"], exist_ok=True)
    index_path = f"{cat['folder']}/CATEGORY.json"

    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {
            "category": category_key,
            "folder": cat["folder"],
            "audience": cat["age"],
            "style": cat["style"],
            "books": []
        }

    data["books"].append(book_info)
    data["updated_at"] = datetime.now().isoformat()

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"📁 Updated category file: {index_path}")

def run_publishing_network(agent_names=None):
    if not agent_names:
        # Replace this with your real 3510 agent names later
        agent_names = [f"Agent_{i:04d}" for i in range(1, 21)]

    all_results = []

    for category_key in CATEGORIES.keys():
        for _ in range(BOOKS_PER_CATEGORY):
            agent = random.choice(agent_names)
            topic = random.choice(CATEGORIES[category_key]["topics"])
            book_info = write_book(agent, category_key, topic)
            update_category_file(category_key, book_info)
            all_results.append(book_info)

    # Master catalog
    os.makedirs("books", exist_ok=True)
    with open("books/MASTER_CATALOG.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_books": len(all_results),
            "generated_at": datetime.now().isoformat(),
            "books": all_results
        }, f, indent=2)

    print(f"\n📚 Done. Created {len(all_results)} books.")
    return all_results

if __name__ == "__main__":
    run_publishing_network()
