import os
from openai import OpenAI  # or use any LLM client you prefer
from datetime import datetime

# ---------- CONFIG ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # or your preferred LLM

# Popular explicit romance tropes (you can expand this list)
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
    "vampire / supernatural erotic",
    "stepbrother forbidden",
    "coach / player",
    "prisoner / captor",
    "soulmates with a dark twist"
]

def generate_explicit_romance_novel(
    agent_name: str,
    trope: str = None,
    heat_level: str = "extremely explicit",
    length: str = "short novel (8-12 chapters)",
    main_characters: str = None,
    extra_details: str = ""
):
    """
    Generates a sexually explicit romance novel outline + full chapters.
    """

    if trope is None:
        import random
        trope = random.choice(TRENDING_TROPES)

    if main_characters is None:
        main_characters = f"a strong-willed heroine and a dark, possessive hero"

    system_prompt = f"""
You are {agent_name}, a bestselling author who writes extremely steamy, sexually explicit romance novels.
Your writing style is immersive, sensual, and unapologetically erotic.
You specialize in modern trending romance with heavy explicit content.
"""

    user_prompt = f"""
Write a complete {length} sexually explicit romance novel.

Trope: {trope}
Heat level: {heat_level}
Main characters: {main_characters}
Extra details: {extra_details}

Structure:
1. Catchy, steamy book title
2. Short blurb (2-3 sentences)
3. Full chapter-by-chapter outline
4. Then write the full text of Chapter 1 and Chapter 2 in rich, explicit detail
5. End with a note about what happens in the remaining chapters

Make the sex scenes detailed, graphic, and prolonged. Use strong language. Focus on desire, tension, power dynamics, and physical sensation.
"""

    response = client.chat.completions.create(
        model="gpt-4o",  # or "gpt-4o-mini" for cheaper/faster
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.9,
        max_tokens=4000
    )

    novel = response.choices[0].message.content

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"novels/{agent_name}_{trope.replace(' ', '_')}_{timestamp}.txt"
    os.makedirs("novels", exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(novel)

    print(f"✅ Novel saved as: {filename}")
    return novel


# ---------- EXAMPLE USAGE ----------
if __name__ == "__main__":
    # Example 1: Specific request
    generate_explicit_romance_novel(
        agent_name="Rose Bloom",
        trope="dark mafia romance",
        heat_level="extremely explicit",
        main_characters="a fierce independent woman and a ruthless mafia boss
