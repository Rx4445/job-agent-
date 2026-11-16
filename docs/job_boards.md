# Stage 7: Automated Job Board Ingestion (`boards.py`)

## Overview
Stage 7 connects our autonomous agent directly to live web job feeds. Instead of requiring manual copy-pasting of job postings into text files, the agent queries public career APIs (starting with **Greenhouse**, the ATS powering companies like Anthropic, Cloudflare, Figma, and Stripe), sanitizes the raw HTML job content, filters for engineering relevance, deduplicates against SQLite, and feeds them into the batch matching pipeline.

---

## Architecture Flow

```mermaid
flowchart TD
    CMD["CLI Command: python boards.py --company cloudflare --limit 5"] --> FETCH["1. fetch_greenhouse_jobs('cloudflare')"]
    FETCH --> FILTER["2. filter_relevant_jobs(keywords=['ai', 'engineer', 'python'])"]
    FILTER --> CLEAN["3. clean_html_content() (Strip HTML, format bullets)"]
    
    CLEAN --> RESUME["4. Load Candidate Profile (SQLite Cache: 0ms)"]
    RESUME --> LOOP["5. Job Ingestion Loop"]
    
    LOOP --> DEDUP{"Already in SQLite (jobs.db)?"}
    DEDUP -->|Hit: 0ms| LOAD_DB["Load Job from SQLite (0 tokens)"]
    DEDUP -->|Miss: New| EXTRACT_LLM["Extract via Gemini & Save to SQLite"]
    
    LOAD_DB --> MATCH["6. match_job_and_resume()"]
    EXTRACT_LLM --> MATCH
    
    MATCH --> RANK["7. Sort Descending by Match Score"]
    RANK --> TABLE["8. render_leaderboard()"]
    TABLE --> ACTION{"9. Action Gate"}
    ACTION -->|Auto-Generate| GEN["generate_batch_applications()"]
    ACTION -->|Select Specific| GEN
    ACTION -->|Exit| STOP["Exit cleanly"]
```

---

## Key Components

### 1. Public Greenhouse Ingestion (`fetch_greenhouse_jobs`)
- Queries the open Greenhouse REST endpoint:
  `https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true`
- Unauthenticated, fast, and not blocked by bot-detection or CAPTCHAs.
- Asynchronously reads job IDs, titles, locations, URLs, and HTML job descriptions.

### 2. Lightweight HTML Sanitization (`clean_html_content`)
- Converts `<li>` items into clean Markdown bullet points (`- `).
- Replaces block elements (`</p>`, `<br>`, `</div>`, `</h1-h6>`) with newlines.
- Strips remaining tags (`<...>` via regex) without heavy external libraries.
- Unescapes HTML entities (`&amp;` $\rightarrow$ `&`, `&nbsp;` $\rightarrow$ ` `).

### 3. Relevance Filtering (`filter_relevant_jobs`)
- Pre-filters large company boards (e.g. 400+ jobs) down to technical/engineering roles.
- Prevents wasting Gemini tokens on irrelevant positions (e.g., Sales, HR, Legal).

### 4. SQLite Deduplication (`get_existing_job`)
- Checks `jobs.db` before calling Gemini.
- If a role from that company has already been analyzed in a previous session, loads requirements in **0ms** and saves 100% of the extraction tokens.

---

## Live Usage

Query live jobs for any company on Greenhouse:
```powershell
python boards.py --company cloudflare --limit 3
```

Automatically generate applications for all approved roles ($\ge 70\%$):
```powershell
python boards.py --company cloudflare --limit 3 --auto-generate
```

---

## Verification & Testing

Run the job board unit test suite:
```powershell
python -m unittest test_boards.py
```
- Tests HTML sanitization (tag stripping, bullet preservation, entity decoding)
- Tests keyword relevance filtering
- Tests Greenhouse API response handling (200 OK, 404 Not Found, timeouts)
- Tests live ingestion workflow and deduplication bypass

Run the full project test suite:
```powershell
python -m unittest discover
```
- **64 unit tests passing** across 9 modules in ~1.08 seconds.
