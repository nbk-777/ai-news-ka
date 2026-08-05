AI News (ქართულად)
===================

Daily AI news digest, aggregated from RSS feeds and machine-translated to Georgian.
Static site, auto-refreshed by a scheduled GitHub Actions workflow.

- `index.html` — the page itself
- `ai-news.json` — generated data, rewritten by `scripts/update-ai-news.py`
- `scripts/update-ai-news.py` — fetches feeds, translates, merges with existing history (7-day retention), writes `ai-news.json`
- `.github/workflows/update-ai-news.yml` — runs the script daily and commits changes
