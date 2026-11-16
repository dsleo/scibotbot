# scibotbot

An append-only archive of the questions answered on [sci-bot.ru](https://sci-bot.ru), the "réponses récentes" feed. A GitHub Actions job runs hourly, records any newly answered question in [`questions.json`](questions.json), and commits only when something new appears. Git history then doubles as a timeline of the archive.

![Scrape status](https://github.com/dsleo/scibotbot/actions/workflows/scrape.yml/badge.svg)

## How it works

- [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml) runs on an hourly schedule, on push, and on manual dispatch.
- `shot-scraper` loads `https://sci-bot.ru` in headless Chromium, waits for the WebSocket-driven feed to render, and extracts the items.
- The merge step loads the existing `questions.json`, adds entries whose key is not yet present, and writes the file back deterministically (`indent=2`, `sort_keys=True`, `ensure_ascii=False`).
- Entries are never removed or rewritten. A question that scrolls off the live feed stays in the archive.
- If the site is down, in maintenance, or returns nothing, the job leaves the archive unchanged and does not commit.

## Schema

`questions.json` is a JSON object keyed by each question's URL path (for example `/some-slug-1a2b3c4d`). Each value has:

| Field | Type | Description |
| --- | --- | --- |
| `url` | string | Absolute URL of the question's page on sci-bot.ru. |
| `question` | string | The question text as shown in the feed. |
| `answered_at_utc` | string or null | ISO-8601 UTC timestamp of the answer, from the feed's `data-when` attribute. |
| `topics` | array of strings | Topic labels shown next to the question, such as `"Biomedicine"`. |
| `first_seen_utc` | string | ISO-8601 UTC time when this archive first captured the question. |

Example:

```json
{
  "/function-of-convergent-orbits-in-2c9e5ad8": {
    "answered_at_utc": "2026-11-16T12:48:31.624Z",
    "first_seen_utc": "2026-11-16T13:02:11Z",
    "question": "function of convergent orbits in primates",
    "topics": ["Biomedicine"],
    "url": "https://sci-bot.ru/function-of-convergent-orbits-in-2c9e5ad8"
  }
}
```

`first_seen_utc` records when this archive saw the question, not when it was asked or answered. The index page does not expose answer text or citation counts.

## Querying the data

Count the archived questions:

```bash
jq 'length' questions.json
```

List questions with their topics:

```bash
jq -r '.[] | "\(.answered_at_utc)\t\(.topics | join(", "))\t\(.question)"' questions.json
```

Python:

```python
import json

with open("questions.json", encoding="utf-8") as f:
    archive = json.load(f)

biomed = [q["question"] for q in archive.values() if "Biomedicine" in q["topics"]]
print(len(biomed), "biomedicine questions")
```

To see when each question was first captured, use Git history:

```bash
git log --format='%h %ad' --date=iso -p questions.json
```

Simon Willison's [`git-history`](https://github.com/simonw/git-history) expects a list of records, not a dict keyed by URL, so it cannot read this file as-is.

## Development

The extraction script and merge logic both live inline in [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml). When sci-bot.ru changes its markup, update the `a.recent-answered-q` selectors there.
