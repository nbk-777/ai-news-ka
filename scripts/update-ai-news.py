#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
TRANSLATE_CLIENTS = ['dict-chrome-ex', 'it', 'at']
CURL_BIN = shutil.which('curl')
HISTORY_DAYS = 7
MAX_PER_SECTION = 40
TRANSLATE_RATE_LIMIT_DELAY = 0.12  # seconds between translate calls
GEORGIAN_CHAR_RE = re.compile(r'[\u10A0-\u10FF]')


def log(msg):
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}', flush=True)


def parse_pub_date(pub):
    try:
        dt = parsedate_to_datetime(pub)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def merge_section(existing_items, new_items):
    by_uid = {it['uid']: it for it in existing_items}
    for it in new_items:
        by_uid[it['uid']] = it
    cutoff = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    merged = list(by_uid.values())
    merged.sort(key=lambda it: parse_pub_date(it.get('pub_date', '')) or cutoff, reverse=True)
    kept = [it for it in merged if (parse_pub_date(it.get('pub_date', '')) or cutoff) >= cutoff]
    return kept[:MAX_PER_SECTION]


FEEDS = [
    ('news', 'ნიუსი', 4),
    ('twitter', 'ტვიტერი', 4),
    ('github', 'გიტჰაბი', 3),
    ('reddit', 'რედიტი', 5),
    ('youtube', 'იუთუბი', 4),
    ('product_hunt', 'Product Hunt', 3),
    ('skill', 'Skills', 4),
    ('blog', 'ბლოგი', 4),
    ('paper', 'კვლევა', 4),
    ('event', 'ივენთი', 3),
]


def open_with_retry(request, timeout=30, attempts=3, opener=None, sleeper=None):
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    for attempt in range(1, attempts + 1):
        try:
            return opener(request, timeout=timeout)
        except (TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as e:
            if attempt == attempts:
                raise
            delay = attempt * 2
            if isinstance(e, urllib.error.HTTPError) and e.code == 429:
                delay = min(delay * 2, 8)
            sleeper(delay)


def fetch_xml(feed):
    url = f'https://www.agenticbrew.ai/feed/{feed}.xml'
    req = urllib.request.Request(url, headers=UA)
    try:
        with open_with_retry(req, timeout=30) as r:
            return ET.fromstring(r.read())
    except Exception as e:
        log(f'ERROR: fetch_xml({feed}) failed: {e}')
        return None


def clean_text(raw):
    """Strip HTML tags and unescape entities, normalizing whitespace."""
    if not raw:
        return ''
    text = re.sub(r'<[^>]+>', ' ', raw)
    text = html.unescape(text)
    return ' '.join(text.split())


def truncate_words(text, limit=320):
    """Truncate text at word boundaries without cutting words in half."""
    text = ' '.join((text or '').split())
    if not text or len(text) <= limit:
        return text
    truncated = text[:limit].rsplit(' ', 1)[0]
    return (truncated.rstrip('.,;:-') + '…') if truncated else text[:limit] + '…'


def first_sentences(text, limit=320):
    text = clean_text(text)
    if not text:
        return ''
    sents = re.split(r'(?<=[.!?])\s+', text)
    out = ''
    for s in sents:
        if not s:
            continue
        candidate = f'{out} {s}'.strip() if out else s.strip()
        if len(candidate) > limit:
            if not out:
                return truncate_words(text, limit)
            return out.rstrip() + '…'
        out = candidate
        if len(out) >= 180 and len(sents) > 1:
            break
    return out or truncate_words(text, limit)


TWITTER_STAT_SEP_RE = re.compile(
    r'\s*·\s*\d+(?:[.,]\d+)?[kKmM]?\s*(?:likes?|rts?|retweets?|replies|views?|bookmarks?)\b'
    r'(?:\s*·\s*\d+(?:[.,]\d+)?[kKmM]?\s*(?:likes?|rts?|retweets?|replies|views?|bookmarks?)\b)*'
    r'(?:\s*·\s*)?',
    re.IGNORECASE,
)


def clean_feed_description(desc: str, feed: str = '') -> str:
    """Clean descriptions that bundle multiple posts/tweets separated by metrics.
    Keeps the primary (first) post to maintain coherence with title and source link.
    """
    if not desc:
        return ''
    if feed == 'twitter' or TWITTER_STAT_SEP_RE.search(desc):
        parts = TWITTER_STAT_SEP_RE.split(desc)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            return parts[0]
    return desc.strip()


def post_process_georgian(text):
    """Refine domain-specific AI terminology in Georgian translations."""
    if not text:
        return text
    # Fix Superintelligence (Google Translate confuses it with CIA/intelligence)
    text = re.sub(r'სუპერდაზვერვ(ის|ამ|ას|ით|ად|ა)', r'სუპერინტელექტ\1', text)
    # Fix Prompt Guardrail mistranslations ("სწრაფი დამცავი ღერძი")
    text = text.replace('სწრაფი დამცავი ღერძი', 'პრომპტის უსაფრთხოების ზღვარი')
    text = text.replace('სწრაფი დამცავი', 'პრომპტის დამცავი')
    text = text.replace('დამცავი ღერძი', 'უსაფრთხოების ზღვარი')
    # Fix agent acting in autonomy context (was "მსახიობობას")
    text = text.replace('აუმჯობესებენ მსახიობობას', 'აუმჯობესებენ ავტონომიურ მოქმედებას')
    # Fix Skill Vetter literal translation
    text = text.replace('უნარი ვეტერი', 'უნარების ვერიფიკატორი (Skill Vetter)')
    # Fix benchmark
    text = text.replace('ბოლო თარგმანის მაჩვენებელი', 'თარგმანის ბოლო ბენჩმარკი')
    # Fix paper as academic paper mistranslation ("ქაღალდი")
    text = text.replace('ქაღალდი ამოწმებს', 'ნაშრომი ამოწმებს')
    text = text.replace('ქაღალდში', 'ნაშრომში')
    text = text.replace('ქაღალდის მიხედვით', 'ნაშრომის მიხედვით')
    # Fix model parameter scale (e.g. "1.46 მმ" -> "1.46M")
    text = re.sub(r'(\d+(?:\.\d+)?)\s*მმ\b', r'\1M', text)
    return text


def translate_segment(text):
    """Translate text segment to Georgian with client rotation and curl HTTP/2 fallback."""
    # 1. Try HTTP/1.1 with verified working client endpoints
    for client in TRANSLATE_CLIENTS:
        url = f'https://translate.googleapis.com/translate_a/single?client={client}&sl=en&tl=ka&dt=t&q=' + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers=UA)
        try:
            with open_with_retry(req, timeout=20, attempts=2) as r:
                data = r.read().decode('utf-8')
            arr = json.loads(data)
            translated = ''.join(part[0] for part in arr[0] if part and part[0]).strip()
            if translated:
                time.sleep(TRANSLATE_RATE_LIMIT_DELAY)
                return translated
        except Exception:
            continue

    # 2. Fallback to curl HTTP/2 if available (bypasses HTTP/1.1 bot detection)
    if CURL_BIN:
        try:
            url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ka&dt=t&q=' + urllib.parse.quote(text)
            res = subprocess.run([CURL_BIN, '-s', '--max-time', '15', url], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout:
                arr = json.loads(res.stdout)
                translated = ''.join(part[0] for part in arr[0] if part and part[0]).strip()
                if translated:
                    time.sleep(TRANSLATE_RATE_LIMIT_DELAY)
                    return translated
        except Exception:
            pass

    return ''


def translate(text, limit=1100, fallback=''):
    """Translate text to Georgian with URL protection, HTML cleaning, and post-processing."""
    cleaned = clean_text(text)
    if not cleaned:
        return fallback

    if len(cleaned) > limit:
        cleaned = truncate_words(cleaned, limit)

    # Protect URLs from being mangled or translated
    urls = []
    def url_repl(m):
        urls.append(m.group(0))
        return f' __URL_{len(urls)-1}__ '

    protected = re.sub(r'https?://[^\s\)\"\'>]+', url_repl, cleaned)

    try:
        translated = translate_segment(protected)
        if not translated:
            log(f'WARN: translate() produced empty output, using fallback: "{cleaned[:40]}..."')
            return fallback

        # Restore preserved URLs
        for idx, u in enumerate(urls):
            translated = re.sub(rf'__\s*URL_{idx}\s*__', u, translated)

        # Refine terminology
        translated = post_process_georgian(translated)
        return translated
    except Exception as e:
        log(f'WARN: translate() failed ({e}), using fallback: "{cleaned[:40]}..."')
        return fallback


def process_feed(feed, label, limit, existing_sections):
    """Fetch and process one feed in parallel with caching and translation."""
    log(f'Fetching {feed} ({label})...')
    root = fetch_xml(feed)
    if root is None:
        log(f'SKIP: {feed} (fetch failed)')
        return feed, existing_sections.get(feed, [])

    existing_by_uid = {it['uid']: it for it in existing_sections.get(feed, [])}
    new_items = []

    for it in root.iter('item'):
        title_en = (it.findtext('title') or '').strip()
        raw_desc_en = (it.findtext('description') or '').strip()
        desc_en = clean_feed_description(raw_desc_en, feed=feed)
        link = (it.findtext('link') or '').strip()
        pub = (it.findtext('pubDate') or '').strip()
        cats = [c.text.strip() for c in it.findall('category') if c.text]

        uid = f'{feed}|{pub}|{title_en}'
        excerpt_en = first_sentences(desc_en, 260)

        # Cache check: if already translated, has Georgian characters, AND cached description matches clean desc_en
        cached = existing_by_uid.get(uid)
        cached_valid = (
            cached
            and cached.get('description_en') == desc_en
            and GEORGIAN_CHAR_RE.search(cached.get('title_ka', ''))
            and GEORGIAN_CHAR_RE.search(cached.get('description_ka', ''))
            and not TWITTER_STAT_SEP_RE.search(cached.get('description_ka', ''))
        )
        if cached_valid:
            title_ka = post_process_georgian(cached.get('title_ka', ''))
            excerpt_ka = post_process_georgian(cached.get('excerpt_ka', ''))
            description_ka = post_process_georgian(cached.get('description_ka', ''))
            log(f'  {feed}: "{title_en[:45]}..." (cached translation reused)')
        else:
            title_ka = (
                post_process_georgian(cached.get('title_ka', ''))
                if (cached and GEORGIAN_CHAR_RE.search(cached.get('title_ka', '')))
                else translate(title_en, 180, fallback=title_en)
            )
            excerpt_ka = translate(excerpt_en, 480, fallback=excerpt_en)
            description_ka = translate(desc_en, 1300, fallback=desc_en)
            log(f'  {feed}: "{title_en[:45]}..." → freshly translated')

        item = {
            'uid': uid,
            'feed': feed,
            'source_label': label,
            'title_en': title_en,
            'description_en': desc_en,
            'excerpt_en': excerpt_en,
            'link': link,
            'pub_date': pub,
            'categories': cats,
            'title_ka': title_ka,
            'excerpt_ka': excerpt_ka,
            'description_ka': description_ka,
        }
        new_items.append(item)

        if len(new_items) >= limit:
            break

    merged = merge_section(existing_sections.get(feed, []), new_items)
    log(f'✓ {feed}: {len(new_items)} new/updated, {len(merged)} total after merge')
    return feed, merged


def main():
    log('AI News update starting...')
    json_path = os.path.join(BASE, 'ai-news.json')
    existing_sections = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding='utf-8') as f:
                existing_sections = json.load(f).get('sections', {})
            log(f'Loaded existing ai-news.json ({len(existing_sections)} sections)')
            # Sanitize legacy cached items across all sections
            for feed_name, items in existing_sections.items():
                for it in items:
                    raw_desc = it.get('description_en', '')
                    cleaned_desc = clean_feed_description(raw_desc, feed=feed_name)
                    has_dirty_ka = bool(
                        TWITTER_STAT_SEP_RE.search(it.get('description_ka', ''))
                        or ('მოწონება' in it.get('description_ka', '') and 'RT' in it.get('description_ka', ''))
                    )
                    if cleaned_desc != raw_desc or has_dirty_ka:
                        log(f'Sanitizing legacy cached item [{feed_name}]: {it.get("uid")}')
                        it['description_en'] = cleaned_desc
                        it['excerpt_en'] = first_sentences(cleaned_desc, 260)
                        it['description_ka'] = translate(cleaned_desc, 1300, fallback=cleaned_desc)
                        it['excerpt_ka'] = translate(it['excerpt_en'], 480, fallback=it['excerpt_en'])
        except (json.JSONDecodeError, OSError) as e:
            log(f'WARN: Could not load existing JSON: {e}')
            existing_sections = {}

    sections = {}

    # Parallel feed processing (10 feeds concurrently)
    log(f'Processing {len(FEEDS)} feeds in parallel...')
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_feed, feed, label, limit, existing_sections): feed
            for feed, label, limit in FEEDS
        }
        for future in as_completed(futures):
            feed_name = futures[future]
            try:
                fname, merged_items = future.result()
                sections[fname] = merged_items
            except Exception as e:
                log(f'ERROR: {feed_name} processing failed: {e}')
                sections[feed_name] = existing_sections.get(feed_name, [])

    # Apply Georgian terminology polish across all section items
    for feed_name, items in sections.items():
        for it in items:
            if it.get('title_ka'):
                it['title_ka'] = post_process_georgian(it['title_ka'])
            if it.get('excerpt_ka'):
                it['excerpt_ka'] = post_process_georgian(it['excerpt_ka'])
            if it.get('description_ka'):
                it['description_ka'] = post_process_georgian(it['description_ka'])

    all_items = [it for feed, _, _ in FEEDS for it in sections.get(feed, [])]

    # Primary featured: top items from news, twitter, reddit
    featured = sections.get('news', [])[:3] + sections.get('twitter', [])[:3] + sections.get('reddit', [])[:4]
    if len(featured) < 10:
        seen_uids = {it['uid'] for it in featured}
        for it in all_items:
            if it['uid'] not in seen_uids:
                featured.append(it)
                seen_uids.add(it['uid'])
                if len(featured) >= 10:
                    break
    featured = featured[:10]

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'featured': featured,
        'sections': sections,
        'all': all_items,
        'feed_labels': {feed: label for feed, label, _ in FEEDS},
    }

    output_path = os.path.join(BASE, 'ai-news.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')

    log(f'✓ Updated {len(featured)} featured items, {len(all_items)} total items')
    log(f'✓ Written to {output_path}')
    print(f'updated {len(featured)} featured items, {len(all_items)} total items')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        log('Interrupted by user')
        sys.exit(130)
    except Exception as e:
        log(f'FATAL: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
