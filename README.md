# scibotbot

An append-only archive of the questions answered on [sci-bot.ru](https://sci-bot.ru), the "réponses récentes" feed. A GitHub Actions job runs hourly, records newly answered questions in day-partitioned files under [`data/`](data/), and commits only when something new appears. Git history then doubles as a timeline of the archive.

![Scrape status](https://github.com/dsleo/scibotbot/actions/workflows/scrape.yml/badge.svg)

## How it works

- [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml) is scheduled every 10 minutes, and also runs on push and on manual dispatch. GitHub's scheduler is best-effort, so actual runs are less frequent than scheduled, and the site's feed shows only the latest 32 answers, so a long enough gap between runs permanently loses questions.
- `shot-scraper` loads `https://sci-bot.ru` in headless Chromium, waits for the WebSocket-driven feed to render, and extracts the items.
- [`scripts/merge.py`](scripts/merge.py) checks every existing key across `data/`, adds new questions to today's file (UTC), and writes it back deterministically (`indent=2`, `sort_keys=True`, `ensure_ascii=False`).
- Entries are never removed or rewritten. A question that scrolls off the live feed stays in the archive.
- If the site is down, in maintenance, or returns nothing, the job leaves the archive unchanged and does not commit.
- If another run pushes first, the job resets to the new `main`, re-merges the same scrape, and retries (up to 3 attempts).

## Layout

One file per UTC day, named by the day the question was first captured: `data/YYYY-MM-DD.json`. Each file is a JSON object keyed by the question's URL path (for example `/some-slug-1a2b3c4d`). Each value has:

| Field | Type | Description |
| --- | --- | --- |
| `url` | string | Absolute URL of the question's page on sci-bot.ru. |
| `question` | string | The question text as shown in the feed. |
| `answered_at_utc` | string or null | ISO-8601 UTC timestamp of the answer, from the feed's `data-when` attribute. |
| `topics` | array of strings | Topic labels shown next to the question, such as `"Biomedicine"`. |
| `first_seen_utc` | string | ISO-8601 UTC time when this archive first captured the question. Its date matches the file name. |

Example (`data/2026-11-16.json`):

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

Count all archived questions:

```bash
jq -s 'map(length) | add' data/*.json
```

List questions with their topics, across all days:

```bash
jq -rs 'add | to_entries[] | .value | "\(.answered_at_utc)\t\(.topics | join(", "))\t\(.question)"' data/*.json
```

Python:

```python
import glob
import json

archive = {}
for path in glob.glob("data/*.json"):
    with open(path, encoding="utf-8") as f:
        archive.update(json.load(f))

biomed = [q["question"] for q in archive.values() if "Biomedicine" in q["topics"]]
print(len(biomed), "biomedicine questions")
```

To see when each day's data was added, use Git history:

```bash
git log --format='%h %ad' --date=iso -- data/
```

## Development

The extraction script lives inline in [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml); when sci-bot.ru changes its markup, update the `a.recent-answered-q` selectors there. To re-run the merge locally, save a scrape as `latest.json` in the repo root and run `python3 scripts/merge.py`.
