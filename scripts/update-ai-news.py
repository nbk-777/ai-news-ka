#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'Mozilla/5.0'}
TRANSLATE_URL = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=ka&dt=t&q='
HISTORY_DAYS = 7
MAX_PER_SECTION = 40


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
    ('news', 'ნიუსი', 2),
    ('twitter', 'ტვიტერი', 3),
    ('github', 'გიტჰაბი', 2),
    ('reddit', 'რედიტი', 3),
    ('youtube', 'იუთუბი', 2),
    ('product_hunt', 'Product Hunt', 1),
    ('skill', 'Skills', 2),
    ('blog', 'ბლოგი', 2),
    ('paper', 'კვლევა', 2),
    ('event', 'ივენთი', 1),
]


def open_with_retry(request, timeout=30, attempts=3, opener=None, sleeper=None):
    opener = opener or urllib.request.urlopen
    sleeper = sleeper or time.sleep
    for attempt in range(1, attempts + 1):
        try:
            return opener(request, timeout=timeout)
        except (TimeoutError, urllib.error.URLError):
            if attempt == attempts:
                raise
            sleeper(attempt * 2)


def fetch_xml(feed):
    url = f'https://www.agenticbrew.ai/feed/{feed}.xml'
    req = urllib.request.Request(url, headers=UA)
    with open_with_retry(req, timeout=30) as r:
        return ET.fromstring(r.read())


def first_sentences(text, limit=320):
    text = ' '.join((text or '').split())
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
                return text[:limit].rstrip() + '…'
            return out.rstrip() + '…'
        out = candidate
        if len(out) >= 180 and len(sents) > 1:
            break
    return out or text[:limit].rstrip() + '…'


def translate(text, limit=1100):
    text = html.unescape(' '.join((text or '').split()))
    if not text:
        return ''
    if len(text) > limit:
        text = text[:limit]
    url = TRANSLATE_URL + urllib.parse.quote(text)
    req = urllib.request.Request(url, headers=UA)
    with open_with_retry(req, timeout=30) as r:
        data = r.read().decode('utf-8')
    arr = json.loads(data)
    return ''.join(part[0] for part in arr[0]).strip()


def main():
    json_path = os.path.join(BASE, 'ai-news.json')
    existing_sections = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding='utf-8') as f:
                existing_sections = json.load(f).get('sections', {})
        except (json.JSONDecodeError, OSError):
            existing_sections = {}

    sections = {}
    for feed, label, limit in FEEDS:
        root = fetch_xml(feed)
        new_items = []
        for it in root.iter('item'):
            title_en = (it.findtext('title') or '').strip()
            desc_en = (it.findtext('description') or '').strip()
            link = (it.findtext('link') or '').strip()
            pub = (it.findtext('pubDate') or '').strip()
            cats = [c.text.strip() for c in it.findall('category') if c.text]
            item = {
                'uid': f'{feed}|{pub}|{title_en}',
                'feed': feed,
                'source_label': label,
                'title_en': title_en,
                'description_en': desc_en,
                'excerpt_en': first_sentences(desc_en, 260),
                'link': link,
                'pub_date': pub,
                'categories': cats,
            }
            item['title_ka'] = translate(title_en, 180)
            item['excerpt_ka'] = translate(item['excerpt_en'], 480)
            item['description_ka'] = translate(desc_en, 1300)
            new_items.append(item)
            if len(new_items) >= limit:
                break
        sections[feed] = merge_section(existing_sections.get(feed, []), new_items)

    all_items = [it for feed, _, _ in FEEDS for it in sections.get(feed, [])]
    featured = sections.get('news', [])[:2] + sections.get('twitter', [])[:3] + sections.get('reddit', [])[:5]
    featured = featured[:10]

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'featured': featured,
        'sections': sections,
        'all': all_items,
        'feed_labels': {feed: label for feed, label, _ in FEEDS},
    }

    with open(os.path.join(BASE, 'ai-news.json'), 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'updated {len(featured)} featured items, {len(all_items)} total items')


if __name__ == '__main__':
    main()
