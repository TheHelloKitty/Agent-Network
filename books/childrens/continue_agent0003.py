import re
from pathlib import Path
from providers import generate_with_failover

NEEDLE = "Agent_0003_talking_animals_original_20260822_000317.txt"
BANNED = ("thinking process", "as an ai", "<think", "drafting", "safety check")

def find_book():
    root = Path("books")
    if not root.exists():
        return None
    hits = list(root.rglob(NEEDLE))
    if hits:
        return hits[0]
    hits = list(root.rglob("*Agent_0003_talking_animals_original*"))
    return hits[0] if hits else None

def next_chapter(text):
    nums = [int(n) for n in re.findall(r"(?im)^CHAPTER\s+(\d+)", text)]
    return (max(nums) + 1) if nums else 1

def clean(chunk):
    low = chunk.lower()
    if any(b in low for b in BANNED):
        chunk = re.split(r"(?i)thinking process|<think|as an ai", chunk, maxsplit=1)[0]
    return chunk.strip()

def main():
    path = find_book()
    if not path:
        print("MISSING", NEEDLE)
        print("Search books/ — file is not in the repo.")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    n = next_chapter(text)
    print("Continuing", path, "next chapter", n, "words", len(text.split()))
    prompt = (
        "Continue this talking-animals children's story. Same characters and tone. "
        "Write ONLY the next chapter as scenes and dialogue. No notes. "
        "If the plot can end cleanly, end this chapter with The End.\n"
        "Start with CHAPTER %s\n\nContinue from:\n%s"
    ) % (n, text[-4000:])
    try:
        raw = generate_with_failover(
            [
                {"role": "system", "content": "Write a children's talking-animals chapter. No adult content."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=1200,
        )
    except Exception as e:
        print("GENERATE FAILED:", e)
        return
    chapter = clean(raw or "")
    if len(chapter.split()) < 60:
        print("Too short, not saving")
        return
    if not re.match(r"(?i)^\s*CHAPTER\s+\d+", chapter):
        chapter = "CHAPTER %s\n\n%s" % (n, chapter)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n\n" + chapter.strip() + "\n")
    print("SAVED", path, "words now", len(path.read_text(encoding="utf-8").split()))

if __name__ == "__main__":
    main()
