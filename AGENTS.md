# AI News (ქართულად)

Daily AI news digest, aggregated from RSS feeds and machine-translated to Georgian. Static GitHub Pages site with automated daily refresh.

## Structure

- `index.html` — single-file static page (HTML + inline CSS + JavaScript)
- `ai-news.json` — generated data file, rewritten by `scripts/update-ai-news.py`
- `scripts/update-ai-news.py` — fetch RSS feeds from agenticbrew.ai, machine-translate titles/summaries to Georgian via Google Translate API, merge with existing history (7-day retention), write `ai-news.json`
- `.github/workflows/update-ai-news.yml` — GitHub Actions workflow: runs daily at 08:00 Tbilisi time (04:00 UTC), commits changed `ai-news.json`
- `fonts/noto-sans-georgian.woff2` — embedded Georgian font (avoid GitHub Pages 404)
- `.nojekyll` — disables Jekyll processing on GitHub Pages

## Dev environment

Python 3.12+ (standard library only, no `requirements.txt`).

## Build & test

No build step — static HTML.

**Manual refresh:**
```bash
python3 scripts/update-ai-news.py
```

This fetches RSS feeds (10 sections: news/twitter/github/reddit/youtube/product_hunt/skill/blog/paper/event), translates to Georgian, merges with existing `ai-news.json` (7-day retention, max 40 items per section), and writes output.

**View locally:**
```bash
open index.html
# or
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deployment

GitHub Pages auto-deploys from `main` branch root. The workflow commits `ai-news.json` changes daily; Pages picks up and publishes automatically.

**Manual trigger:**
```bash
# via GitHub UI: Actions → Update AI News → Run workflow
# or via gh CLI:
gh workflow run update-ai-news.yml
```

## Conventions

- Feed URLs: hardcoded in `update-ai-news.py` as `https://www.agenticbrew.ai/feed/{section}.xml`
- Translation: Google Translate free tier (`translate.googleapis.com/translate_a/single`), no API key required
- Commit message: `chore: refresh ai-news.json` (automated bot commits)
- No manual edits to `ai-news.json` — script overwrites it
- History retention: 7 days (`HISTORY_DAYS = 7`), items older than cutoff are dropped on next refresh

## Pitfalls

- Do NOT edit `ai-news.json` manually — next workflow run will overwrite it
- GitHub Pages requires `.nojekyll` file — without it, Pages tries Jekyll processing and fails on `_` prefixed paths
- Google Translate API has no published rate limit; script uses 2-second retry backoff on network errors (`open_with_retry`)
- Font asset must be committed to repo — hotlinking external font breaks on Pages
