#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import html
import json
import os
import re
import shutil
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

# If a title/field is basically all proper nouns (ratio of key terms to
# total words is at/above this), don't translate it at all -- Google
# Translate mangles pure name phrases like "Skill Vetter" -> "უნარი ვეტერი".
KEEP_ENGLISH_THRESHOLD = 0.6
# Titles with this normalized-text similarity or higher, within DEDUP_WINDOW_DAYS
# of each other, are treated as the same story republished under a new pub_date/uid.
DEDUP_TITLE_SIMILARITY = 0.87
DEDUP_WINDOW_DAYS = 7


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


def extract_key_terms(text):
    if not text:
        return []
    terms = set(re.findall(r'\b[A-Z][A-Za-z0-9]*(?:\.[A-Za-z]+)?\b', text))
    acronyms = set(re.findall(r'\b[A-Z]{2,}\b', text))
    terms |= acronyms
    stop = {'The', 'A', 'An', 'In', 'On', 'For', 'With', 'As', 'Is', 'Of', 'To', 'And'}
    return sorted(t for t in terms if t not in stop and len(t) > 1)


def skeptic_verify(translated_ka, key_terms):
    if not key_terms:
        return True, 'no key terms to check'
    missing = [t for t in key_terms if t not in translated_ka]
    if missing:
        return False, f'missing terms: {missing}'
    return True, 'all key terms present'


def smooth_georgian(text):
    """Clean up mechanical Google-Translate artifacts (spacing, quote
    style, word doubling) that read as unnatural Georgian. This is a
    rule-based polish, not a fluency rewrite -- it cannot fix word order
    or case-marking errors, only the artifacts regex can safely catch."""
    if not text:
        return text
    text = re.sub(r'\b(\S+)( \1\b)+', r'\1', text)  # collapse doubled words
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)  # no space before punctuation
    text = re.sub(r'([.!?])(?=[Ⴀ-ჿა-ჰA-Za-z])', r'\1 ', text)  # space after sentence end
    text = re.sub(r'"([^"]+)"', r'„\1“', text)  # Georgian-style quotes
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def translate_field_corrected(text_en, limit):
    if not text_en:
        return ''
    key_terms = extract_key_terms(text_en)
    ka = smooth_georgian(translate(text_en, limit))
    if not key_terms:
        return ka
    ok, _ = skeptic_verify(ka, key_terms)
    if ok:
        return ka
    tokens = re.findall(r'[A-Za-z]+', text_en)
    ratio = len(key_terms) / max(1, len(tokens))
    if ratio >= KEEP_ENGLISH_THRESHOLD:
        return text_en
    missing = [t for t in key_terms if t not in ka]
    return f"{ka} ({', '.join(missing)})" if missing else ka


def backfill_correct(item):
    """Re-apply smoothing/skeptic correction to an item's already-translated
    fields without calling the Translate API again. merge_section() carries
    old items forward untouched -- only the handful of freshly-fetched items
    per run pass through translate_field_corrected(), so most held-over
    items still contain artifacts (doubled words, uncaught proper-noun
    mistranslations) from before this correction logic existed. This fixes
    those in place, once, using the text already on hand."""
    for en_field, ka_field, limit in (
        ('title_en', 'title_ka', 180),
        ('excerpt_en', 'excerpt_ka', 480),
        ('description_en', 'description_ka', 1300),
    ):
        text_en = item.get(en_field, '')
        ka = smooth_georgian(item.get(ka_field, ''))
        if not text_en or not ka:
            item[ka_field] = ka
            continue
        key_terms = extract_key_terms(text_en)
        if not key_terms:
            item[ka_field] = ka
            continue
        ok, _ = skeptic_verify(ka, key_terms)
        if ok:
            item[ka_field] = ka
            continue
        tokens = re.findall(r'[A-Za-z]+', text_en)
        ratio = len(key_terms) / max(1, len(tokens))
        if ratio >= KEEP_ENGLISH_THRESHOLD:
            item[ka_field] = text_en
            continue
        missing = [t for t in key_terms if t not in ka]
        item[ka_field] = f"{ka} ({', '.join(missing)})" if missing else ka
    return item


def normalize_title(title):
    return re.sub(r'[^a-z0-9 ]', '', title.lower()).strip()


def dedup_near_duplicates(all_items):
    """Collapse items whose titles are near-identical and whose pub_date
    falls within DEDUP_WINDOW_DAYS of each other -- the same story often
    gets re-listed under a new uid/pub_date when a feed re-crawls it."""
    normalized = [normalize_title(it['title_en']) for it in all_items]
    parsed_dates = [parse_pub_date(it.get('pub_date', '')) for it in all_items]
    drop = set()
    for i in range(len(all_items)):
        if i in drop or not normalized[i]:
            continue
        for j in range(i + 1, len(all_items)):
            if j in drop or not normalized[j]:
                continue
            if parsed_dates[i] and parsed_dates[j]:
                if abs((parsed_dates[i] - parsed_dates[j]).days) > DEDUP_WINDOW_DAYS:
                    continue
            ratio = difflib.SequenceMatcher(None, normalized[i], normalized[j]).ratio()
            if ratio >= DEDUP_TITLE_SIMILARITY:
                newer, older = (i, j) if (parsed_dates[i] or datetime.min.replace(tzinfo=timezone.utc)) >= (parsed_dates[j] or datetime.min.replace(tzinfo=timezone.utc)) else (j, i)
                drop.add(older)
    kept_uids = {all_items[i]['uid'] for i in range(len(all_items)) if i not in drop}
    dropped_uids = {all_items[i]['uid'] for i in drop}
    return kept_uids, dropped_uids


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Fetch, translate, and dedup AI-news feed items.')
    parser.add_argument(
        '--out',
        default=os.path.join(BASE, 'ai-news.json'),
        help='Path to write ai-news.json (default: %(default)s)',
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Before overwriting --out, copy the existing file to a timestamped .bak-<UTC timestamp> path',
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    json_path = args.out
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
            item['title_ka'] = translate_field_corrected(title_en, 180)
            item['excerpt_ka'] = translate_field_corrected(item['excerpt_en'], 480)
            item['description_ka'] = translate_field_corrected(desc_en, 1300)
            new_items.append(item)
            if len(new_items) >= limit:
                break
        sections[feed] = merge_section(existing_sections.get(feed, []), new_items)

    for feed in sections:
        sections[feed] = [backfill_correct(it) for it in sections[feed]]

    all_items = [it for feed, _, _ in FEEDS for it in sections.get(feed, [])]
    kept_uids, dropped_uids = dedup_near_duplicates(all_items)
    if dropped_uids:
        for feed in sections:
            sections[feed] = [it for it in sections[feed] if it['uid'] in kept_uids]
        all_items = [it for it in all_items if it['uid'] in kept_uids]

    featured = sections.get('news', [])[:2] + sections.get('twitter', [])[:3] + sections.get('reddit', [])[:5]
    featured = featured[:10]

    payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'featured': featured,
        'sections': sections,
        'all': all_items,
        'feed_labels': {feed: label for feed, label, _ in FEEDS},
        'newsgraph_meta': {
            'translator': 'google_corrected_smoothed',
            'duplicate_items_dropped': len(dropped_uids),
            'total_items': len(all_items),
        },
    }

    if args.backup and os.path.exists(json_path):
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        shutil.copy2(json_path, f'{json_path}.bak-{stamp}')

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f'updated {len(featured)} featured items, {len(all_items)} total items, {len(dropped_uids)} duplicates dropped')


if __name__ == '__main__':
    main()
