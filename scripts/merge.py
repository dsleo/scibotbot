"""Merge latest.json (scraped feed) into questions.json, append-only.

Keys are the question's URL path, so re-running on the same feed is a no-op.
An empty scrape leaves questions.json untouched.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

BASE = "https://sci-bot.ru"
PATH = "questions.json"

archive = {}
if os.path.exists(PATH) and os.path.getsize(PATH) > 0:
    with open(PATH, encoding="utf-8") as f:
        archive = json.load(f)  # a corrupt file fails the run; it is never overwritten

with open("latest.json", encoding="utf-8") as f:
    latest = json.load(f)

if not latest:
    print("Scrape returned no items; leaving questions.json unchanged.")
    sys.exit(0)

now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
added = 0
for item in latest:
    question = (item.get("question") or "").strip()
    href = (item.get("href") or "").strip()
    if not question:
        continue
    key = href or hashlib.sha256(question.encode("utf-8")).hexdigest()[:16]
    if key in archive:  # append-only: never rewrite an entry already captured
        continue
    archive[key] = {
        "url": BASE + href if href.startswith("/") else href,
        "question": question,
        "answered_at_utc": item.get("answered_at_utc"),
        "topics": item.get("topics") or [],
        "first_seen_utc": now,
    }
    added += 1

with open(PATH, "w", encoding="utf-8") as f:
    json.dump(archive, f, indent=2, ensure_ascii=False, sort_keys=True)
    f.write("\n")
print(f"Added {added} new question(s); archive now holds {len(archive)}.")
