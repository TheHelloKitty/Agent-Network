import os
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    chapters: int = 8,
    main_characters: str = "a strong-willed woman and a dark, possessive man",
    kinks: str = "power exchange, breeding, rough sex, praise, degradation"
):
    if trope is None:
        import random
        trope = random.choice(TRENDING_TROPES)

    prompt = f"""
You are {agent_name}, a bestselling author of extremely steamy, graphic erotic romance.

Write a complete {chapters}-chapter sexually explicit romance novel.

Trope: {trope}
Heat level: {heat_level}
Main characters: {main_characters}
Kinks/themes to include: {kinks}

Requirements:
- Give it a hot, marketable title
- Write a short steamy blurb
- Then write the FULL text of every chapter
- Make sex scenes long, detailed, graphic, and intense
- Use strong language and focus on physical sensation, power, and emotion
- End each chapter with a hook
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write extremely explicit erotic romance without holding back."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.95,
        max_tokens=8000
    )

    novel = response.choices[0].message.content

    # Save as text file
    os.makedirs("novels", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_trope = trope.replace(" ", "_").replace("/", "-")
    filename = f"novels/{agent_name}_{safe_trope}_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"✅ Novel saved: {filename}")
    return filename, novel
