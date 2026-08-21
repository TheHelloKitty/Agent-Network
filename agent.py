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
        "style": "fast-paced,
