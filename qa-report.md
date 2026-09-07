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
