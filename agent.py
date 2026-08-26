import os
import json
import random
import time
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fpdf import FPDF
from docx import Document
from providers import generate_with_failover

CATEGORIES = {
    "childrens": {
        "folder": "books/childrens",
        "age": "ages 6-10",
        "style": "warm, fun, safe, lots of talk and simple scenes",
        "topics": ["talking animals", "friendship", "bedtime adventure"],
    },
    "romance": {
        "folder": "books/romance",
        "age": "adult",
        "style": "emotional, dialogue-heavy, detailed settings",
        "topics": ["second chance", "enemies to lovers", "slow burn"],
    },
    "spicy_romance": {
        "folder": "books/spicy_romance",
        "age": "adult",
        "style": "steamy, explicit, intense dialogue and physical detail",
        "topics": ["dark mafia romance", "forced proximity"],
    },
    "true_crime": {
        "folder": "books/true_crime",
        "age": "adult",
        "style": "strictly factual, timeline-based, public-record only, no opinions",
        "topics": [
            "Julio Foolio case public timeline",
            "McKenzie Shirilla case public court coverage",
            "recent headline cases from public reporting only"
        ],
    },
    "thriller": {
        "folder": "books/thriller",
        "age": "adult",
        "style": "tense dialogue, sharp description, short scenes",
        "topics": ["missing wife", "witness protection"],
    },
    "fantasy": {
        "folder": "books/fantasy",
        "age": "teen/adult",
        "style": "vivid places, spoken voices, quest scenes",
        "topics": ["hidden heir", "dragon academy"],
    },
    "sci_fi": {
        "folder": "books/sci_fi",
        "age": "teen/adult",
        "style": "futuristic detail and human conversation",
        "topics": ["colony ship", "AI uprising"],
    },
    "nonfiction": {
        "folder": "books/nonfiction",
        "age": "adult",
        "style": "clear examples, plain talk, useful stories",
        "topics": ["habit building", "money basics"],
    },
    "horror": {
        "folder": "books/horror",
        "age": "adult",
        "style": "creepy description and uneasy dialogue",
        "topics": ["haunted lake house", "cult in the woods"],
    }
}

CHAPTERS = 20
TARGET_WORDS = 90000
WORDS_PER_CHAPTER = 4500
MIN_KEEP_WORDS = 800

def generate_with_fallback(messages, temperature=0.95, max_tokens=3000):
    return generate_with_failover(
        messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

def safe_name(text):
    cleaned = []
    for c in text:
        if c.isalnum() or c in "-_ ":
            cleaned.append(c)
    return "".join(cleaned).strip().replace(" ", "_")[:80]

def word_count(text):
    return len((text or "").split())

def txt_to_pdf(txt_path):
    try:
        pdf_path = txt_path.replace(".txt", ".pdf")
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        pdf.set_font("Helvetica", size=12)
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                safe = line.encode("latin-1", "replace").decode("latin-1").strip()
                if not safe:
                    pdf.ln(6)
                    continue
                pdf.multi_cell(180, 8, " ".join(safe.split()))
        pdf.output(pdf_path)
        print("PDF saved:", pdf_path)
    except Exception as e:
        print("PDF failed:", e)

def txt_to_docx(txt_path):
    try:
        docx_path = txt_path.replace(".txt", ".docx")
        doc = Document()
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                doc.add_paragraph(line.rstrip("\n"))
        doc.save(docx_path)
        print("DOCX saved:", docx_path)
    except Exception as e:
        print("DOCX failed:", e)

def add_table_of_contents(filename, chapter_count):
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    toc_lines = ["TABLE OF CONTENTS", ""]
    for i in range(1, chapter_count + 1):
        toc_lines.append("Chapter %s" % i)
    toc_lines.append("")
    toc_text = "\n".join(toc_lines)
    parts = content.split("\n\n", 1)
    if len(parts) == 2:
        new_content = parts[0] + "\n\n" + toc_text + "\n\n" + parts[1]
    else:
        new_content = toc_text + "\n\n" + content
    with open(filename, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Table of contents added")

def delete_book_family(txt_path):
    for sib in [txt_path, txt_path.replace(".txt", ".pdf"), txt_path.replace(".txt", ".docx")]:
        try:
            if os.path.exists(sib):
                os.remove(sib)
                print("Deleted:", sib)
        except Exception as e:
            print("Could not delete", sib, e)

def is_undeveloped_book(path, min_words=MIN_KEEP_WORDS):
    try:
        p = Path(path)
        if not p.exists() or not p.is_file():
            return True
        if p.stat().st_size < 200:
            return True
        text = p.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            return True
        low = text.lower()
        if "draft in progress" in low and word_count(text) < min_words:
            return True
        if "chapter plan pending" in low and word_count(text) < min_words:
            return True
        if word_count(text) < min_words:
            return True
        return False
    except Exception:
        return True

def cleanup_empty_books(min_words=MIN_KEEP_WORDS):
    root =
