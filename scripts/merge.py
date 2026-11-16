"""Merge latest.json (scraped feed) into data/YYYY-MM-DD.json, append-only.

Each question lives in the file for the UTC day it was first captured.
Keys are the question's URL path, checked against every day file, so
re-running on the same feed is a no-op. An empty scrape changes nothing.
"""
import glob
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

BASE = "https://sci-bot.ru"
DATA_DIR = "data"

now = datetime.now(timezone.utc).replace(microsecond=0)
today_path = os.path.join(DATA_DIR, now.strftime("%Y-%m-%d") + ".json")

with open("latest.json", encoding="utf-8") as f:
    latest = json.load(f)

if not latest:
    print("Scrape returned no items; leaving data/ unchanged.")
    sys.exit(0)

# Every key already archived, across all days.
seen = set()
for path in glob.glob(os.path.join(DATA_DIR, "*.json")):
    with open(path, encoding="utf-8") as f:
        seen.update(json.load(f))  # a corrupt file fails the run; it is never overwritten

today = {}
if os.path.exists(today_path):
    with open(today_path, encoding="utf-8") as f:
        today = json.load(f)

stamp = now.isoformat().replace("+00:00", "Z")
added = 0
for item in latest:
    question = (item.get("question") or "").strip()
    href = (item.get("href") or "").strip()
    if not question:
        continue
    key = href or hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    if key in seen:  # append-only: never rewrite an entry already captured
        continue
    seen.add(key)
    today[key] = {
        "url": BASE + href if href.startswith("/") else href,
        "question": question,
        "answered_at_utc": item.get("answered_at_utc"),
        "topics": item.get("topics") or [],
        "first_seen_utc": stamp,
    }
    added += 1

if added == 0:
    print(f"Added 0 new question(s); {len(seen)} archived in total.")
    sys.exit(0)

os.makedirs(DATA_DIR, exist_ok=True)
with open(today_path, "w", encoding="utf-8") as f:
    json.dump(today, f, indent=2, ensure_ascii=False, sort_keys=True)
    f.write("\n")
print(f"Added {added} new question(s) to {today_path}; {len(seen)} archived in total.")
