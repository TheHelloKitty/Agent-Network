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
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
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
                max_tokens=3000
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
            return text[:4000]
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
        {"
