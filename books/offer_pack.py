import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from providers import generate_with_failover

def generate(messages, temperature=0.7):
    return generate_with_failover(messages, temperature=temperature, max_tokens=2000)

def read_book(path, limit=12000):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[:limit]

def make_offer_pack(book_path, category="romance", price="6.99"):
    book_path = Path(book_path)
    if not book_path.exists():
        raise FileNotFoundError("Book not found: %s" % book_path)

    text = read_book(book_path)
    out_dir = Path("storefront_exports") / ("pack_%s" % datetime.now().strftime("%Y%m%d_%H%M%S"))
    out_dir.mkdir(parents=True, exist_ok=True)

    titles = generate([
        {
            "role": "system",
            "content": "You write commercial ebook titles. Return 8 strong title options only."
        },
        {
            "role": "user",
            "content": "Category: %s\nCreate 8 marketable ebook titles based on this draft:\n%s" % (category, text[:4000])
        }
    ], temperature=0.9)

    blurb = generate([
        {
            "role": "system",
            "content": "You write high-converting ebook blurbs. No spoilers. Short paragraphs."
        },
        {
            "role": "user",
            "content": "Write a sales blurb for this %s ebook. End with a soft call to action.\n\nDRAFT:\n%s" % (category, text[:5000])
        }
    ], temperature=0.8)

    page_copy = generate([
        {
            "role": "system",
            "content": "You write clean product page copy for digital ebook stores like Payhip."
        },
        {
            "role": "user",
            "content": (
                "Create Payhip product page copy with these sections:\n"
                "1. Headline\n2. Subheadline\n3. What you get\n4. Who this is for\n"
                "5. Blurb\n6. Price line\n7. Call to action\n\n"
                "Category: %s\nPrice: $%s\nDraft:\n%s"
            ) % (category, price, text[:5000])
        }
    ], temperature=0.7)

    posts = generate([
        {
            "role": "system",
            "content": "You write short promotional posts for X. No hashtag spam. Natural voice."
        },
        {
            "role": "user",
            "content": (
                "Write 12 promo posts for this ebook. Mix hooks, quotes, questions, and soft sells.\n"
                "Category: %s\nPrice: $%s\nDraft:\n%s"
            ) % (category, price, text[:4000])
        }
    ], temperature=0.9)

    bundles = generate([
        {
            "role": "system",
            "content": "You create digital product bundle ideas."
        },
        {
            "role": "user",
            "content": (
                "Suggest 5 sellable bundle ideas around this ebook for Payhip.\n"
                "Include suggested price for each.\nCategory: %s\nDraft:\n%s"
            ) % (category, text[:3000])
        }
    ], temperature=0.8)

    files = {
        "titles.txt": titles,
        "blurb.txt": blurb,
        "payhip_page_copy.txt": page_copy,
        "promo_posts.txt": posts,
        "bundle_ideas.txt": bundles,
    }

    for name, content in files.items():
        path = out_dir / name
        with open(path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print("Saved:", path)
        time.sleep(1)

    meta = {
        "book": str(book_path),
        "category": category,
        "price": price,
        "output_dir": str(out_dir),
        "created_at": datetime.now().isoformat(),
    }
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print("Offer pack ready:", out_dir)
    return str(out_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--category", default="romance")
    parser.add_argument("--price", default="6.99")
    args = parser.parse_args()
    make_offer_pack(args.book, category=args.category, price=args.price)
