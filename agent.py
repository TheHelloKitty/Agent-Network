import os
import json
import random
import argparse
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
        "style": "warm fun safe imaginative",
        "topics": ["talking animals", "first day of school", "friendship", "bedtime adventure"]
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional character-driven ending",
        "topics": ["second chance", "enemies to lovers", "fake dating", "slow burn"]
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy explicit high tension",
        "topics": ["dark mafia romance", "possessive anti-hero", "forced proximity", "age gap"]
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "investigative gripping factual",
        "topics": ["unsolved disappearance", "small town murder", "cold case reopened"]
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "fast-paced twists high stakes",
        "topics": ["missing wife", "witness protection", "serial killer hunt"]
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "world-building quest magic",
        "topics": ["hidden heir", "dragon academy", "cursed kingdom"]
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic cinematic",
        "topics": ["colony ship", "AI uprising", "time loop"]
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "practical clear useful",
        "topics": ["habit building", "money basics", "focus and productivity"]
    },
    "horror": {
        "folder": "books/horror",
        "age": "adult",
        "style": "atmospheric creepy dread",
        "topics": ["haunted lake house", "cult in the woods", "last night at the motel"]
    }
}

BOOKS_PER_CATEGORY = 1

def safe_name(text):
    return "".join(c if c.isalnum() or c in "-_ " else "" for c in text).strip().replace(" ", "_")[:80]

def generate_with_fallback(messages, temperature=0.9, max_tokens=8000):
    last_error = None
    for model in GROQ_MODELS:
        try:
            print("Trying model:", model)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            print("Using model:", model)
            return response
        except Exception as e:
            print("Model failed:", model, e)
            last_error = e
    raise RuntimeError(last_error)

def write_book(agent_name, category_key, topic):
    cat = CATEGORIES[category_key]
    system_prompt = f"You are {agent_name}, a professional author. Category: {category_key}. Audience: {cat['age']}. Style: {cat['style']}. Write a complete book. If children's, keep it age-appropriate."
    user_prompt = f"Write a 12-chapter book about {topic}. Include title, author {agent_name}, blurb, and full chapter text."

    response = generate_with_fallback([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])

    book_text = response.choices[0].message.content
    os.makedirs(cat["folder"], exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{cat['folder']}/{safe_name(agent_name)}_{safe_name(topic)}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(book_text)

    print("Saved:", filename)
    return {
        "agent": agent_name,
        "category": category_key,
        "topic": topic,
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
    with
