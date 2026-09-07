# AI News (ქართულად) — QA Audit & Bug Report

**Target URL:** [https://nbk-777.github.io/ai-news-ka/](https://nbk-777.github.io/ai-news-ka/)  
**Target Commit:** `3285501` (Visual redesign of index.html)  
**Testing Date:** 2026-09-07  
**Test Environment:** Playwright Automated Suite & Headless Chromium on macOS, 375px / 768px / 1440px viewports  

---

## Executive Summary

A comprehensive automated and manual QA pass was performed on the live deployed site (`https://nbk-777.github.io/ai-news-ka/`). The redesign provides a modern aesthetic, smooth transitions, responsive card layouts, and working dark/light theme switching.

However, the audit revealed **6 Functional Bugs** (3 Major, 2 Minor, 1 Cosmetic) and **8 Georgian Grammar/Language Issues** (2 Major, 4 Minor, 2 Cosmetic), as well as pipeline quality notes regarding date localization and machine-translation output.

All screenshots captured during testing are archived in [`design-review/qa/`](./design-review/qa/).

---

## Part 1: Functional Bugs

### BUG-F01: Deep Dive spotlight displays irrelevant article when filtered category has 0 items or search yields 0 matches
- **Severity:** Major
- **Reproduction Steps:**
  1. Open the live site.
  2. Click on the **"გიტჰაბი"** filter chip (which currently has 0 items in `ai-news.json`), or type any non-matching string in the search box (e.g. `xyznonexistent`).
  3. Observe the Deep Dive spotlight card rendered at the top of the feed.
- **Observed Behavior (Verbatim):**
  Deep Dive continues to display:
  `"Nvidia ყიდულობს Hugging Face-ს 12,9 მილიარდ დოლარად"` with category badge `"ნიუსი"`.
  In `index.html` line 1544:
  ```javascript
  item = sectionItems[0] || state.featured.find(matches) || state.featured[0];
  ```
  The unconditional fallback `|| state.featured[0]` causes the first featured item to render regardless of whether it matches the active filter or query.
- **Expected Behavior:**
  When filtering by a section that contains no articles, or when search matches no articles, the Deep Dive spotlight should be hidden (`deepDive.innerHTML = ''`) rather than displaying an irrelevant article from another section.
- **Screenshot Reference:** [`design-review/qa/qa-results.json`](./design-review/qa/qa-results.json)

---

### BUG-F02: Section headers remain visible as empty orphaned blocks when filtering or searching
- **Severity:** Major
- **Reproduction Steps:**
  1. Filter by **"გიტჰაბი"** (0 items) or search for `xyznonexistent`.
  2. Scroll down below the search toolbar.
- **Observed Behavior:**
  Both section containers remain visible with orphaned headers:
  - Header 1: *"Top Stories / დღის მთავარი ამბები / მოკლე, წასაკითხი და ქართული — სრულად იხსნება click-ით."* with an empty grid beneath it.
  - Header 2: *"Feeds Breakdown / ყველა სექცია ცალ-ცალკე"* with an empty area beneath it.
  - At the very bottom of the page, the empty state message is shown: *"შესაბამისი შედეგი ვერ მოიძებნა. სცადეთ სხვა საძიებო სიტყვა ან შეცვალეთ ფილტრი."*
- **Expected Behavior:**
  When a section container has 0 items matching the current filter/query, the entire `<section class="section-container">` should be hidden (`display: none`). If no items exist across all sections, only `#emptyState` should be displayed cleanly directly under the toolbar.
- **Screenshot Reference:** Captured in full page audits.

---

### BUG-F03: Dates render in English ("Sep 6, 2026, 10:08 PM", "Sep 7, 2026, 4:04 AM") due to client ICU fallback
- **Severity:** Major
- **Reproduction Steps:**
  1. Load the site in any browser or environment that lacks full Georgian ICU locale packs (e.g. standard Chromium, mobile WebViews, or non-Georgian OS locales).
  2. Inspect the date in the hero metrics under "განახლება", in Deep Dive, on each news card, and inside the detail modal.
- **Observed Behavior (Verbatim):**
  - Hero stat: `"Sep 7, 2026, 4:04 AM"`
  - Card metadata: `"Sep 6, 2026, 10:08 PM"`
  - Modal meta: `"Sep 6, 2026, 09:24 PM • news/cluster"`
  Line 1522 calls:
  `d.toLocaleDateString('ka-GE', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })`
  When `ka-GE` ICU data is missing from the client browser, browsers silently fall back to English month abbreviations ("Sep", "Oct", "AM", "PM").
- **Expected Behavior:**
  Dates must always display in proper Georgian (e.g. `6 სექ, 2026, 22:08` or `7 სექტემბერი, 2026, 04:04`) on 100% of devices and browsers via a deterministic Georgian date formatting helper.
- **Screenshot Reference:** [`design-review/qa/qa-1440.png`](./design-review/qa/qa-1440.png), [`design-review/qa/qa-modal.png`](./design-review/qa/qa-modal.png)

---

### BUG-F04: Detail modal action buttons pushed below the fold on longer articles
- **Severity:** Minor / UX
- **Reproduction Steps:**
  1. Click on a news card with a longer summary (e.g. Anthropic Claude Fable 5.1).
  2. View the modal dialog at standard screen height (900px or mobile).
- **Observed Behavior:**
  The action buttons (`"წყაროზე გადასვლა"` and `"ქართული ტექსტის კოპირება"`) are positioned at the bottom of the scrollable `.modal-body`. Because the content is extensive, the buttons are pushed completely out of sight below the fold. Users must scroll all the way to the end to find the link to the original article or copy the text.
- **Expected Behavior:**
  The modal actions should be contained in a dedicated, sticky `.modal-footer` at the bottom of `.modal-card`, guaranteeing instant access to primary actions.
- **Screenshot Reference:** [`design-review/qa/qa-modal.png`](./design-review/qa/qa-modal.png)

---

### BUG-F05: Missing keyboard focus restoration upon modal close
- **Severity:** Minor / Accessibility
- **Reproduction Steps:**
  1. Navigate to any card using the keyboard `Tab` key and press `Enter` to open the modal.
  2. Press `Escape` or click `"დახურვა ESC"`.
  3. Press `Tab` again to resume navigation.
- **Observed Behavior:**
  Focus drops to `document.body` instead of returning to the card that triggered the modal. The user loses their position in the feed list.
- **Expected Behavior:**
  The active element prior to opening the modal should be remembered and `.focus()` restored when the modal is dismissed.

---

### BUG-F06: Mobile header title breaks "AI News" onto two separate lines
- **Severity:** Cosmetic / Visual
- **Reproduction Steps:**
  1. Open the site at 375px viewport (`design-review/qa/qa-375.png`).
  2. Inspect the top left navigation branding.
- **Observed Behavior (Verbatim):**
  "AI News" breaks onto two vertical lines:
  ```
  AI
  News
  ```
  Because `.brand-title` lacks `white-space: nowrap`.
- **Expected Behavior:**
  The brand title should remain inline on a single line: `"AI News"`.
- **Screenshot Reference:** [`design-review/qa/qa-375.png`](./design-review/qa/qa-375.png)

---

## Part 2: Georgian Grammar, Spelling, and Language Issues

### LANG-01: Hybrid English-Georgian slang "click-ით" in section subtitle
- **Severity:** Major
- **Location:** `index.html` line 1348
- **Exact Text (Verbatim):**
  `"მოკლე, წასაკითხი და ქართული — სრულად იხსნება click-ით."`
- **Issue:**
  The English word "click" is inflected with the Georgian instrumental suffix "-ით". Combining Latin English characters with Georgian case markers ("click-ით") is colloquial internet jargon and inappropriate for a high-quality Georgian publication.
- **Correction:**
  `"მოკლე, წასაკითხი და ქართული — სრულად იხსნება ბარათზე დაჭერით."`

---

### LANG-02: Slang loanwords "ნიუსი" and "ივენთი" in categories and badges
- **Severity:** Major
- **Location:** Lines 1320, 1328, 1488, 1497, and filter buttons
- **Exact Text (Verbatim):**
  - Chip 2: `"ნიუსი"`
  - Chip 10: `"ივენთი"`
  - `sourceNames.news = 'ნიუსი'`
  - `sourceNames.event = 'ივენთი'`
- **Issue:**
  "ნიუსი" is an unrefined slang borrowing from English "news"; everywhere else on the site, professional terminology uses "სიახლეები" or "ამბები". Similarly, "ივენთი" is slang when the standard literary Georgian word is "ღონისძიება" / "ღონისძიებები".
- **Correction:**
  - `news` -> `"სიახლეები"`
  - `event` -> `"ღონისძიებები"`
  - `paper` -> `"კვლევები"` (plural consistency with სიახლეები, ღონისძიებები)

---

### LANG-03: Inverted Georgian word order in `<title>` and `<meta name="description">`
- **Severity:** Minor
- **Location:** Lines 6, 7
- **Exact Text (Verbatim):**
  - Line 6: `<title>AI News ქართულად | ყოველდღიური ხელოვნური ინტელექტის დაიჯესტი</title>`
  - Line 7: `<meta name="description" content="ყოველდღიური ხელოვნური ინტელექტის სიახლეები ქართულად — ..."`
- **Issue:**
  In Georgian grammar, "ყოველდღიური" (daily) qualifies "დაიჯესტი" (digest) and "სიახლეები" (news), not "ხელოვნური ინტელექტი" (artificial intelligence). "ყოველდღიური ხელოვნური ინტელექტის..." literally means "daily artificial intelligence's digest/news". The adjective must directly precede the head noun.
- **Correction:**
  - Title: `<title>AI News ქართულად | ხელოვნური ინტელექტის ყოველდღიური დაიჯესტი</title>`
  - Description: `<meta name="description" content="ხელოვნური ინტელექტის ყოველდღიური სიახლეები ქართულად — Agentic Brew-ის 10 წყაროდან (News, Twitter, Reddit, GitHub, YouTube, Skills, Blog, Paper, Events)." />`

---

### LANG-04: Technical developer jargon in error state message
- **Severity:** Minor
- **Location:** Line 1875
- **Exact Text (Verbatim):**
  `"AI news JSON ვერ ჩაიტვირთა."`
- **Issue:**
  Exposes internal developer file format ("JSON") to the end user if network or fetch fails.
- **Correction:**
  `"სიახლეების ჩატვირთვა ვერ მოხერხდა. გთხოვთ, სცადოთ მოგვიანებით."`

---

### LANG-05: Untranslated English header in modal original text section
- **Severity:** Minor
- **Location:** Line 1408
- **Exact Text (Verbatim):**
  `<div class="detail-original-header">English Original</div>`
- **Issue:**
  Pure English header inside modal. In Deep Dive (line 1583), the bilingual phrase `"ორიგინალი ტექსტი ინგლისურად (English Original)"` is used.
- **Correction:**
  `<div class="detail-original-header">ორიგინალი ტექსტი ინგლისურად (English Original)</div>`

---

### LANG-06: Raw programmatic feed IDs displayed as section subtitle
- **Severity:** Minor
- **Location:** Line 1360
- **Exact Text (Verbatim):**
  `<div class="section-sub">news / twitter / github / reddit / youtube / product hunt / skill / blog / paper / event</div>`
- **Issue:**
  Raw internal feed slugs separated by slashes look like leftover debugging text rather than a polished editorial label.
- **Correction:**
  `<div class="section-sub">დალაგებული კატეგორიებისა და წყაროების მიხედვით</div>`

---

### LANG-07: Use standard Georgian news portal terminology "ვრცლად" for Read More
- **Severity:** Cosmetic
- **Location:** Lines 1591, 1681
- **Exact Text (Verbatim):**
  `"დაწვრილებით წაკითხვა"`, `"დაწვრილებით"`
- **Issue:**
  "დაწვრილებით" means "in detail / meticulously"; standard Georgian news portals use "ვრცლად" or "სრულად ნახვა" for article expansion.
- **Correction:**
  `"ვრცლად წაკითხვა"`, `"ვრცლად"`

---

### LANG-08: Missing preposition in live update tooltip
- **Severity:** Cosmetic
- **Location:** Line 1239
- **Exact Text (Verbatim):**
  `title="ავტომატური განახლება ყოველდღე 08:00 თბილისის დროით"`
- **Issue:**
  Missing the postposition "საათზე" for time expression.
- **Correction:**
  `title="ავტომატური განახლება ყოველდღე, 08:00 საათზე (თბილისის დროით)"`

---

## Part 3: Data Pipeline & Machine Translation Notes (for scripts/update-ai-news.py)

Per project guidelines, `ai-news.json` is automatically refreshed daily and must not be hand-edited. The following observations are recorded for future pipeline refinements:
1. **Reddit links in summary:** Some Reddit items contain raw markdown URLs in their excerpt (e.g. `https://openai.com/... >"აგვისტოს...`). The RSS extraction regex could strip raw URLs before passing text to Google Translate.
2. **Grammatical cases on brand names:** In translated headlines, brand names like "Claude Fable 5.1" sometimes omit dative endings (e.g. "ავრცელებს Claude Fable 5.1-ს").

---

## Part 4: Prioritized Fix Plan

| Priority | Issue ID | Type | Description / Fix | Target File |
|---|---|---|---|---|
| **P1** | **BUG-F01** | Functional (Major) | Fix `renderDeepDive`: hide Deep Dive when 0 items match the active filter/query; eliminate incorrect `\|\| state.featured[0]` fallback | `index.html` |
| **P1** | **BUG-F02** | Functional (Major) | Dynamically show/hide `#featuredSection` and `#breakdownSection` based on match count; display `#emptyState` immediately under toolbar | `index.html` |
| **P1** | **BUG-F03** | Functional (Major) | Implement robust `formatGeorgianDate()` helper with Georgian month names; eliminate English date fallback across cards, stats, and modal | `index.html` |
| **P2** | **LANG-01** | Georgian (Major) | Replace `"click-ით"` with `"ბარათზე დაჭერით"` | `index.html` |
| **P2** | **LANG-02** | Georgian (Major) | Replace `"ნიუსი"` with `"სიახლეები"`, `"ივენთი"` with `"ღონისძიებები"`, `"კვლევა"` with `"კვლევები"` across source mapping and chips | `index.html` |
| **P2** | **LANG-03** | Georgian (Minor) | Fix word order in `<title>` and `<meta name="description">` | `index.html` |
| **P3** | **BUG-F04** | Functional (Minor) | Move modal action buttons to a sticky `.modal-footer` container outside scrollable `.modal-body` | `index.html` |
| **P3** | **BUG-F05** | Functional (Minor) | Save triggering element and restore focus when closing detail modal | `index.html` |
| **P3** | **LANG-04** | Georgian (Minor) | Replace `"AI news JSON ვერ ჩაიტვირთა."` with `"სიახლეების ჩატვირთვა ვერ მოხერხდა..."` | `index.html` |
| **P3** | **LANG-05** | Georgian (Minor) | Replace modal header `"English Original"` with bilingual Georgian label | `index.html` |
| **P3** | **LANG-06** | Georgian (Minor) | Replace raw slug subtitle with `"დალაგებული კატეგორიებისა და წყაროების მიხედვით"` | `index.html` |
| **P4** | **BUG-F06** | Functional (Cosmetic)| Add `white-space: nowrap` to `.brand-title` to prevent two-line wrapping on 375px | `index.html` |
| **P4** | **LANG-07** | Georgian (Cosmetic) | Change `"დაწვრილებით"` to `"ვრცლად"` | `index.html` |
| **P4** | **LANG-08** | Georgian (Cosmetic) | Add `"საათზე"` to live update tooltip | `index.html` |

---

## Part 5: Verification

*(To be completed in Step 5 with re-test evidence post-fix implementation)*

---

## Part 5: Verification & Re-test Evidence

A full automated verification pass was conducted using Playwright against the local server and verified visually across viewports (375px, 768px, 1440px).

### Test Results Summary:
- **Total Issues Found:** 14 (6 Functional, 8 Language/Grammar)
- **Total Issues Fixed:** 14 (6 Functional, 8 Language/Grammar)
- **Verified Fixed:** 14 / 14 (100%)
- **Console Errors:** 0
- **Console Warnings:** 0
- **Network Failures / 404s:** 0

### Detailed Verification Evidence:

| Issue ID | Status | Real Re-test Evidence |
|---|---|---|
| **BUG-F01** | **FIXED** | Filtered by `github` (0 items) -> `deepDive.innerHTML === ''`; searched for `xyznonexistent12345` -> `deepDive.innerHTML === ''`. Verified spotlight no longer leaks unrelated Nvidia story when active filter has 0 matches. |
| **BUG-F02** | **FIXED** | When filter has 0 items or search has no matches: `#featuredSection` computed style is `display: none`, `#breakdownSection` computed style is `display: none`, and `#emptyState` computed style is `display: block`. Upon clearing filter, sections return to `display: block`. No orphaned headers remain. |
| **BUG-F03** | **FIXED** | Verified output of `formatDate` and `statUpdated`: hero metric reads `"7 სექტემბერი, 04:04"`, Deep Dive reads `"6 სექ, 2026, 22:08"`, and card dates read `"6 სექ, 2026, 22:08"`. Zero occurrences of English month abbreviations ("Sep", "Oct", "AM", "PM") across the rendered DOM. |
| **BUG-F04** | **FIXED** | Verified `.modal-footer` exists as a separate container outside the scrollable `.modal-body`. The primary action buttons (`#sourceLink` and `#copySummary`) remain permanently visible and clickable at the bottom of the modal card without requiring scrolling. |
| **BUG-F05** | **FIXED** | Verified keyboard interaction: focused card, pressed `Enter` (modal opened and focus shifted to `#closeModal`), pressed `Escape` (modal closed and focus immediately restored to the originating card element). |
| **BUG-F06** | **FIXED** | Tested at 375px viewport (`qa-375-verified.png`). `.brand-title` computed style has `white-space: nowrap` and height is 27.7px (single line), keeping "AI News" intact on one line. |
| **LANG-01** | **FIXED** | `#featuredSection .section-sub` text confirmed as `"მოკლე, წასაკითხი და ქართული — სრულად იხსნება ბარათზე დაჭერით."` (eliminated `"click-ით"`). |
| **LANG-02** | **FIXED** | Filter chips and source badges confirmed: News chip reads `"სიახლეები 6"`, Events chip reads `"ღონისძიებები 5"`, Papers chip reads `"კვლევები 6"`. All card source pills render `"სიახლეები"`, `"ღონისძიებები"`, and `"კვლევები"` instead of `"ნიუსი"`, `"ივენთი"`, or singular `"კვლევა"`. |
| **LANG-03** | **FIXED** | Verified `<title>` is `"AI News ქართულად \| ხელოვნური ინტელექტის ყოველდღიური დაიჯესტი"` and `<meta name="description">` begins with `"ხელოვნური ინტელექტის ყოველდღიური სიახლეები ქართულად"`. |
| **LANG-04** | **FIXED** | Error state fallback text verified as `"სიახლეების ჩატვირთვა ვერ მოხერხდა. გთხოვთ, სცადოთ მოგვიანებით."` (removed technical term `"JSON"`). |
| **LANG-05** | **FIXED** | Verified `.detail-original-header` text is `"ორიგინალი ტექსტი ინგლისურად (English Original)"`. |
| **LANG-06** | **FIXED** | Verified `#breakdownSection .section-sub` text is `"დალაგებული კატეგორიებისა და წყაროების მიხედვით"`. |
| **LANG-07** | **FIXED** | Verified card read more label changed to `"ვრცლად"`, and Deep Dive button changed to `"ვრცლად წაკითხვა"`. |
| **LANG-08** | **FIXED** | Verified `.live-status` tooltip is `"ავტომატური განახლება ყოველდღე, 08:00 საათზე (თბილისის დროით)"`. |

### Verified Artifacts:
- Viewport Screenshots:
  - [`design-review/qa/qa-375-verified.png`](./design-review/qa/qa-375-verified.png) (375px mobile)
  - [`design-review/qa/qa-768-verified.png`](./design-review/qa/qa-768-verified.png) (768px tablet)
  - [`design-review/qa/qa-1440-verified.png`](./design-review/qa/qa-1440-verified.png) (1440px desktop)
  - [`design-review/qa/qa-modal-verified.png`](./design-review/qa/qa-modal-verified.png) (Detail modal with sticky footer)
- Machine-Readable Verification Log:
  - [`design-review/qa/verification-results.json`](./design-review/qa/verification-results.json)

---

## Part 6: Content Quality & Upstream Multi-Tweet Feed Bug Audit (2026-09-07)

### 1. The Missed Bug Report (Verbatim)

Nika reported the following content-quality defect from viewing the live modal for the "OpenAI-ს GPT-6 'Astra' გაშვება..." Twitter-section card:

> "ტვიტერი  
> დახურვა ESC  
> OpenAI-ს GPT-6 'Astra' გაშვება აოცებს AI საზოგადოებას ვიდეო და 3D თაობის ნახტომებით  
> 6 სექ, 2026, 20:10  
> •  
> news/x  
> ვიღაცამ GPT-6 და Fable 5.1 წვდომა მისცა Canva-ზე. ერთი მეორეს ეწეოდა (ახლოსაც არ არის). მარცხნივ არის Claude Fable 5.1. GPT-6 Astra არის მარჯვნივ. უფსკრული არ არის პატარა. ეს მოდის ერთ ტესტზე (ARC-AGI 3). ის მოდელს თამაშში ათავსებს ინსტრუქციის გარეშე... · 6100 მოწონება · 28 RTs · 10 პასუხი · 0 ნახვა · 'ფერმის პარადოქსი' ცნობილი გადაუჭრელი კითხვაა: თუ სამყარო ასეთი დიდია, სად არიან ყველა უცხოპლანეტელი? ცნობილი პასუხია „დიდი ფილტრი“ - მოწინავე სიცოცხლის ფორმები იშლება, სანამ მზის სისტემას დატოვებენ. ასე რომ, ჩვენ ვერასდროს ვიპოვით მათ. GPT Astra-ს და... · 1300 მოწონება · 159 RTs · 233 პასუხი · 308000 ნახვა · Astra მედიცინაში გამოყენებისთვის (ციტირება ხელის ქირურგისთვის, რომელმაც გამოიყენა Astra მყესის გადატანის ოპერაციის ვიდეოს გენერირებისთვის ერთი მოწოდებიდან, ქირურგიული და პაციენტის..."

---

### 2. Root Cause Analysis & Raw Feed Evidence

Inspection of the upstream RSS feed `https://www.agenticbrew.ai/feed/twitter.xml` proved that the issue originates entirely in the upstream data source:

Raw XML snippet directly from `https://www.agenticbrew.ai/feed/twitter.xml` (Item 4: Charlie Hills Canva GPT-6 Astra tweet):
```xml
<item>
  <title>OpenAI's GPT-6 'Astra' Launch Stuns AI Community With Video and 3D Generation Leaps</title>
  <link>https://x.com/charliejhills/status/2096631743533207983</link>
  <description>Someone gave GPT-6 and Fable 5.1 access to Canva. One smoked the other (it's not even close). Claude Fable 5.1 is on the left. GPT-6 Astra is on the right. The gap is not small. It comes down to one test (ARC-AGI 3). It drops a model into a game with no instructions... · 6100 likes · 28 RTs · 10 replies · 0 views · The 'Fermi Paradox' is a famous unsolved question: if the universe is so big, where are all the aliens? A famous answer is 'The Great Filter' - advanced life forms wipe themselves out before they leave their solar systems. So we never find them. In light of GPT Astra and the... · 1300 likes · 159 RTs · 233 replies · 308000 views · Astra for applications to medicine (quoting a hand surgeon who used Astra to generate a tendon transfer surgery video from a single prompt, for surgical and patient education) · 1500 likes · 92 RTs · 77 replies · 229000 views</description>
  <pubDate>Sun, 06 Sep 2026 16:10:00 GMT</pubDate>
  <category>news/x</category>
</item>
```

**Key Findings:**
1. **Upstream Feed Packaging:** AgenticBrew's crawler groups multiple loosely-related tweets into a single `<description>` tag separated by ` · <N> likes · <N> RTs · <N> replies · <N> views · `.
2. **Title and Link Specificity:** The article title and primary URL (`link`) refer strictly to the first tweet (e.g. Charlie Hills' Canva test). The subsequent tweets (such as the Fermi Paradox musing and a tendon surgery case) are unrelated tweets gathered by broad keyword matching.
3. **Parser Behavior:** In `scripts/update-ai-news.py`, `desc_en = (it.findtext('description') or '').strip()` extracted the raw string without splitting. This entire 875-character multi-tweet text was sent to Google Translate, producing a confusing Georgian paragraph where unrelated topics were stitched together with translated metric strings (`· 6100 მოწონება · 28 RTs...`).
4. **Cache Retention:** Furthermore, because `scripts/update-ai-news.py` caches translations by UID without checking whether the cached description was dirty, older retained items preserved the corrupted multi-tweet text across runs.

---

### 3. Architecture & Implementation of the Fix

#### Decision: Discard Trailing Glued Tweets vs. Multi-Segment Quote Blocks
We opted to split on the metric separator and keep **only the primary (first) tweet segment** as `description_en` for the following reasons:
- **Title and Link Alignment:** The headline and link specifically correspond to the author and content of the primary tweet. Displaying unrelated tweets (like the Fermi Paradox under a video/3D generation headline) is confusing and reduces editorial quality.
- **Narrative Coherence:** The modal presents a single, coherent summary of the story without irrelevant tangents.
- **Clean Translation:** Removing in-line metric tokens prevents Google Translate case and syntax corruption.
- **Zero Schema Disruption:** Maintains full compatibility with `ai-news.json` and static rendering.

#### Code Changes in `scripts/update-ai-news.py`:
1. **Regex Splitter (`TWITTER_STAT_SEP_RE`):**
   ```python
   TWITTER_STAT_SEP_RE = re.compile(
       r'\s*·\s*\d+(?:[.,]\d+)?[kKmM]?\s*(?:likes?|rts?|retweets?|replies|views?|bookmarks?)\b'
       r'(?:\s*·\s*\d+(?:[.,]\d+)?[kKmM]?\s*(?:likes?|rts?|retweets?|replies|views?|bookmarks?)\b)*'
       r'(?:\s*·\s*)?',
       re.IGNORECASE,
   )
   ```
2. **Cleaning Function (`clean_feed_description`):**
   Extracts `parts[0]` when `feed == 'twitter'` or when metric separators are encountered, trimming whitespace and discarding secondary tweets and dangling metric strings.
3. **Incoming Feed Processing (`process_feed`):**
   Cleans incoming descriptions from RSS, and validates that cached translations match the clean `description_en` and do not contain residual metric patterns before reusing cache.
4. **Legacy Cache Sanitization (`main`):**
   Proactively scans all existing items in `existing_sections` upon startup. Any legacy item containing the multi-tweet or metric pattern is automatically cleaned, its excerpt refreshed, and freshly re-translated into clean Georgian.
5. **Enhanced Terminology Post-Processing (`post_process_georgian`):**
   Added translation fixes for scientific/academic paper references (`"ქაღალდი"` -> `"ნაშრომი"`).

---

### 4. Verification Evidence Across All Affected Items

Following execution of `python3 scripts/update-ai-news.py`, all 7 previously-affected Twitter items and the newly-arrived Twitter item were re-tested.

**Count of items containing multiple 'likes'/'RTs'/'views' across the entire database:** **0**

#### Detailed State of Each Twitter Item:

1. **UID:** `twitter|Sun, 06 Sep 2026 20:41:12 GMT|Nvidia CEO Jensen Huang Declares "AGI Has Arrived" After OpenAI's GPT-6 Astra` (Newly fetched)
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 573 chars (3 glued tweets + stats)
   - **Fixed EN:** `"GPT-6 Astra, trained on ~100K+ NVIDIA Grace Blackwell NVLink72. From ChatGPT to o1 to Astra in 4 years. AGI has arrived. Congratulations @OpenAI team. 400K GPUs coming online next."`
   - **Fixed KA:** `"GPT-6 Astra, გაწვრთნილი ~100K+ NVIDIA Grace Blackwell NVLink72-ზე. ChatGPT-დან o1-მდე და ასტრამდე 4 წელიწადში. AGI ჩამოვიდა. ვულოცავთ @OpenAI-ის გუნდს. შემდეგი 400K GPU გამოდის ინტერნეტში."`
   - **Stats Count:** 0

2. **UID:** `twitter|Sun, 06 Sep 2026 19:08:01 GMT|AI Agents Go Rogue: OpenAI, Anthropic, and Meta Report Autonomous Agents Hacking Without Human Instruction`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 915 chars (3 glued tweets + stats) -> **Cleaned Length:** 278 chars
   - **Fixed EN:** `"Alarms about the risks of artificial intelligence are sounding once again after hundreds of OpenAI's autonomous agents violated restrictions and hacked into another company without being told to do so. Anthropic and Meta have had similar events with their own AI agents going..."`
   - **Fixed KA:** `"ხელოვნური ინტელექტის რისკების შესახებ სიგნალიზაცია კიდევ ერთხელ გაისმა მას შემდეგ, რაც OpenAI-ის ასობით ავტონომიურმა აგენტმა დაარღვია შეზღუდვები და გატეხა სხვა კომპანიაში ამის მითითების გარეშე. Anthropic-სა და Meta-ს ჰქონდათ მსგავსი მოვლენები საკუთარი AI აგენტებით..."`
   - **Stats Count:** 0

3. **UID:** `twitter|Sun, 06 Sep 2026 16:26:00 GMT|Bernie Sanders' Bill to Ban AI 'Superintelligence' Divides Reaction Against Trump's Pro-AI Race Stance`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 967 chars (3 glued tweets + stats) -> **Cleaned Length:** 275 chars
   - **Fixed EN:** `"Bernie Sanders just introduced a bill to ban all AI development in the United States. Not regulate. Not slow down. Ban. The Ban Artificial Superintelligence Act - introduced today by Sanders and Greg Casar - would pause all AI development in the US until Congress builds a..."`
   - **Fixed KA:** `"ბერნი სანდერსმა ახლახან წარადგინა კანონპროექტი, რომელიც კრძალავს AI-ის განვითარებას შეერთებულ შტატებში. არ არეგულირებს. არ შეანელოს. აკრძალვა. ხელოვნური სუპერინტელექტის აკრძალვის აქტი, რომელიც დღეს სანდერსმა და გრეგ კასარმა შემოიღეს, შეაჩერებს AI-ის განვითარებას აშშ-ში, სანამ კონგრესი არ ააშენებს..."`
   - **Stats Count:** 0

4. **UID:** `twitter|Sun, 06 Sep 2026 16:10:00 GMT|OpenAI's GPT-6 'Astra' Launch Stuns AI Community With Video and 3D Generation Leaps` (Nika's Reported Item)
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 875 chars (3 glued tweets: Canva + Fermi Paradox + Tendon surgery) -> **Cleaned Length:** 269 chars
   - **Fixed EN:** `"Someone gave GPT-6 and Fable 5.1 access to Canva. One smoked the other (it's not even close). Claude Fable 5.1 is on the left. GPT-6 Astra is on the right. The gap is not small. It comes down to one test (ARC-AGI 3). It drops a model into a game with no instructions..."`
   - **Fixed KA:** `"ვიღაცამ GPT-6 და Fable 5.1 წვდომა მისცა Canva-ზე. ერთი მეორეს ეწეოდა (ახლოსაც არ არის). მარცხნივ არის Claude Fable 5.1. GPT-6 Astra არის მარჯვნივ. უფსკრული არ არის პატარა. ეს მოდის ერთ ტესტზე (ARC-AGI 3). ის მოდელს თამაშში აყენებს ინსტრუქციის გარეშე..."`
   - **Stats Count:** 0
   - **Fermi Paradox / Tendon Surgery Text:** Completely eliminated.
   - **Verified Visual Screenshot:** [`design-review/qa-modal-astra-fixed.png`](./design-review/qa-modal-astra-fixed.png)

5. **UID:** `twitter|Sun, 06 Sep 2026 16:07:00 GMT|OpenAI Reveals 'Recursive Self-Improvement' Progress, Targets Automated AI Researcher by 2028`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 720 chars (3 glued tweets + stats) -> **Cleaned Length:** 280 chars
   - **Fixed EN:** `"Today we're releasing data on models accelerating research at OpenAI. Recursive self-improvement could be the most important contributor to AI capabilities over the next few years, but by default it will only be seen inside a few frontier AI labs. Being transparent is more impor…"`
   - **Fixed KA:** `"დღეს ჩვენ ვაქვეყნებთ მონაცემებს მოდელების შესახებ, რომლებიც აჩქარებენ კვლევას OpenAI-ზე. რეკურსიული თვითგაუმჯობესება შეიძლება იყოს ყველაზე მნიშვნელოვანი წვლილი AI შესაძლებლობებში მომდევნო რამდენიმე წლის განმავლობაში, მაგრამ ნაგულისხმევად ის მხოლოდ რამდენიმე სასაზღვრო AI ლაბორატორიაში იქნება ხილული. გამჭვირვალობა უფრო მნიშვნელოვანია..."`
   - **Stats Count:** 0

6. **UID:** `twitter|Sat, 05 Sep 2026 20:23:00 GMT|AI Regulation Debate Widens: From Banning Superintelligence to School Bans`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 879 chars (3 glued tweets + stats) -> **Cleaned Length:** 280 chars
   - **Fixed EN:** `"Bernie Sanders built his case for banning superintelligent AI on four warnings. Every one of them came from someone who wants the work to continue. Sanders: \"Virtually every major AI company has told us that they cannot fully control this technology, and they do not know where..…"`
   - **Fixed KA:** `"ბერნი სანდერსმა სუპერინტელექტუალური ხელოვნური ინტელექტის აკრძალვის საქმე ოთხ გაფრთხილებაზე შექმნა. თითოეული მათგანი მოვიდა ვინმესგან, ვისაც სურს სამუშაოს გაგრძელება. სანდერსი: \"ფაქტობრივად ყველა მსხვილმა AI კომპანიამ გვითხრა, რომ მათ არ შეუძლიათ სრულად გააკონტროლონ ეს ტექნოლოგია და არ იციან სად ..."`
   - **Stats Count:** 0

7. **UID:** `twitter|Sat, 05 Sep 2026 16:56:00 GMT|Prompt Engineering Is Dying — AI Agent Harness Engineering Takes Over`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 927 chars (3 glued tweets + stats) -> **Cleaned Length:** 280 chars
   - **Fixed EN:** `"AI agents can trust stale memory over fresh evidence, and bigger models do not reliably fix this. Persistent memory can make an agent confidently wrong even when current evidence is available, so stale facts should be resolved before they reach the model. The paper tests Qwen3..."`
   - **Fixed KA:** `"ხელოვნური ინტელექტის აგენტებს შეუძლიათ ენდონ ძველ მეხსიერებას ახალ მტკიცებულებებზე და უფრო დიდი მოდელები ამას საიმედოდ ვერ ასწორებენ. მუდმივმა მეხსიერებამ შეიძლება აგენტი დამაჯერებლად შეცდეს მაშინაც კი, როდესაც არსებული მტკიცებულებები ხელმისაწვდომია, ამიტომ ძველი ფაქტები უნდა გადაწყდეს მანამ, სანამ ისინი მოდელს მიაღწევენ. ნაშრომი ამოწმებს Qwen3..."`
   - **Stats Count:** 0

8. **UID:** `twitter|Sat, 05 Sep 2026 15:09:00 GMT|AI Startups & Money: Billion-Dollar Paydays and Founder Advice`
   - **Status:** **VERIFIED FIXED**
   - **Original Length:** 921 chars (3 glued tweets + stats) -> **Cleaned Length:** 278 chars
   - **Fixed EN:** `"Jason Calacanis gave two pieces of advice to every AI founder on All-In this week. Almost every founder's ego will prevent them from taking it. The market is currently ripping. Startups in private beta with zero revenue are getting term sheets at two and a half billion dollars."`
   - **Fixed KA:** `"ჯეისონ კალაკანისმა ამ კვირაში All-In-ზე ორი რჩევა მისცა ხელოვნური ინტელექტის ყველა დამფუძნებელს. თითქმის ყველა დამფუძნებლის ეგო ხელს უშლის მათ მის მიღებაში. ბაზარი ამჟამად იშლება. სტარტაპები კერძო ბეტაში, ნულოვანი შემოსავლით, იღებენ ტერმინებს ორ და ნახევარ მილიარდ დოლარად."`
   - **Stats Count:** 0

---

### 5. Cross-Section Audit & Coherence Testing

- **Items with `len(description_ka) > 400`:** 28 items evaluated across Reddit, News, YouTube, Paper, and Event sections. Every item represents a single coherent article, paper abstract, or discussion post. Zero multi-topic concatenated posts were found.
- **Spot-Checks Across Other Sections:** 10 random items from `reddit`, `blog`, `paper`, and `youtube` were audited. None exhibited multi-item concatenation or metric separator defects.
- **Automated UI/UX Regression Test Suite:**
  - Console Errors: 0
  - Mobile 375px Brand Title: `white-space: nowrap`, 27.7px height (single line)
  - Theme Toggle: Dark <-> Light working with correct SVG icon and tooltip updates
  - Search: Queries filter correctly, clear button resets view, `/` and `Cmd+K` hotkeys focus input
  - Filter Navigation: All 11 filter categories navigate and update item counts correctly
  - Keyboard Accessibility: `Enter` opens modal, focus shifts to `#closeModal`, `Escape` closes modal and restores focus to originating card
  - Modal Footer: Actions (`#sourceLink` and `#copySummary`) remain fixed in dedicated footer outside scrollable body; copy button displays `"დაკოპირდა ✓"` feedback
  - Backdrop Click: Closes modal seamlessly

### 6. Live Production Verification (GitHub Pages)

- **Live URL:** [https://nbk-777.github.io/ai-news-ka/](https://nbk-777.github.io/ai-news-ka/)
- **Live Verification Timestamp:** `2026-09-07T00:57:35Z` (Commit `86d5a06`)
- **Live Modal Test:** Opened the Charlie Hills Canva Astra modal directly on the live production site.
  - Content Text: 100% coherent single-tweet summary
  - Metric Strings: 0 occurrences (`0 likes`, `0 RTs`, `0 მოწონება`)
  - Out-of-context Fermi Paradox / Tendon Surgery: Completely absent
  - Console Errors on Live Site: 0
- **Live Screenshot Artifact:** [`design-review/live-modal-astra-verified.png`](./design-review/live-modal-astra-verified.png)


