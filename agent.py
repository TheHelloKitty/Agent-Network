import re
from pathlib import Path
from providers import generate_with_failover

FOLDER = Path("books/spicy_romance")
BANNED = (
    "thinking process", "as an ai", "<think", "drafting",
    "safety check", "self-correction", "constraint",
)

PROMPT = """You are continuing the novel CRIMSON VOWS.
Hero: Luca Dante Borelli (family says Luca, streets say Dante). One man, not two.
Heroine: Evie Caruso. Bar: The Velvet Lantern.
Brother: Marco. Rival: Gino "The Ghost" Santoro. Detective: Mara Quinn.
Sister: Elena. Marta and Sal Rossi.
Write ONLY the next chapter as scenes with dialogue.
No outline, no notes, no thinking.
If this is chapter 6 or later, one consensual explicit scene between Luca Dante and Evie is allowed.
Start with a line like CHAPTER 3
Continue from this ending:

"""

def latest_seed():
    FOLDER.mkdir(parents=True, exist_ok=True)
    files = sorted(
        [p for p in FOLDER.glob("Crimson_Vows*.txt") if "refined" not in p.name.lower()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[0] if files else None

def next_chapter(text):
    nums = [int(n) for n in re.findall(r"(?im)^CHAPTER\s+(\d+)", text)]
    return (max(nums) + 1) if nums else 3

def clean(chunk):
    low = chunk.lower()
    if any(b in low for b in BANNED):
        parts = re.split(r"(?i)thinking process|<think|as an ai", chunk, maxsplit=1)
        chunk = parts[0]
    return chunk.strip()

def main():
    path = latest_seed()
    if not path:
        print("NO CRIMSON FILE. Run seed_crimson.py first.")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    n = next_chapter(text)
    print("Continuing", path.name, "next chapter", n, "words now", len(text.split()))
    tail = text[-3500:]
    try:
        raw = generate_with_failover(
            [
                {"role": "system", "content": "Write only novel prose."},
                {"role": "user", "content": PROMPT + tail},
            ],
            temperature=0.85,
            max_tokens=1200,
        )
    except Exception as e:
        print("GENERATE FAILED:", e)
        return
    chapter = clean(raw or "")
    if len(chapter.split()) < 80:
        print("Chunk too short, not saving:", len(chapter.split()), "words")
        return
    if not re.match(r"(?i)^\s*CHAPTER\s+\d+", chapter):
        chapter = "CHAPTER %s\n\n%s" % (n, chapter)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n" + chapter.strip() + "\n")
    print("SAVED chapter to", path, "new words", len(path.read_text(encoding="utf-8").split()))

if __name__ == "__main__":
    main()
