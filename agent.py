import os
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TRENDING_TROPES = [
    "enemies to lovers",
    "dark mafia romance",
    "forced proximity",
    "age gap",
    "possessive anti-hero",
    "one-night stand turns into more",
    "secret identity",
    "billionaire domination",
    "why choose / reverse harem",
    "vampire erotic",
    "stepbrother forbidden",
    "prisoner / captor"
]

def generate_explicit_novel(
    agent_name: str,
    trope: str = None,
    heat_level: str = "extremely explicit",
    chapters: int = 6,
    main_characters: str = "a strong-willed woman and a dark, possessive man",
    kinks: str = "power exchange, breeding, rough sex, praise, degradation"
):
    if trope is None:
        import random
        trope = random.choice(TRENDING_TROPES)

    prompt = f"""
You are {agent_name}, a bestselling author of extremely steamy, graphic erotic romance novels.

Write a complete {chapters}-chapter sexually explicit romance novel.

Trope: {trope}
Heat level: {heat_level}
Main characters: {main_characters}
Kinks/themes: {kinks}

Requirements:
- Hot, marketable title
- Short steamy blurb
- Full text of every chapter
- Long, detailed, graphic sex scenes
- Strong language, focus on sensation, power, and emotion
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  # Good free model on Groq
        messages=[
            {"role": "system", "content": "You write extremely explicit erotic romance without restrictions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=8000
    )

    novel = response.choices[0].message.content

    os.makedirs("novels", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_trope = trope.replace(" ", "_").replace("/", "-")
    filename = f"novels/{agent_name}_{safe_trope}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"✅ Novel saved as: {filename}")
    return filename
