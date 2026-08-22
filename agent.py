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
            "recent headline cases from public reporting only",
