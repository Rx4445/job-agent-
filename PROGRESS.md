# Job Application Agent: Progress

## Progress
Version 1 (working, tested, deployed app):  █████████░░░  9/12  (75%)
Full 12-stage roadmap:                      █░░░░░░░░░░░  ~1.5/12  (~12%)

V1 checklist:
[x] 1  Tools set up (git, Node, VS Code, agy)
[x] 2  Python env, .gitignore, API key
[x] 3  First extraction script
[x] 4  Pydantic structured output
[x] 5  Retry with backoff + test
[x] 6  FastAPI endpoint + test
[x] 7  SQLite: create, save, read
[x] 8  Endpoint saves to the database (test mocks save_job)
[x] 9  Remove duplicate retry loop, async test (agy)
[ ] 10 10 real postings + accuracy script
[ ] 11 Push to GitHub
[ ] 12 README + deploy

## Done
- [x] Set up git, Node, VS Code
- [x] Install Antigravity CLI and log in
- [x] Create GEMINI.md rules
- [x] Set up Python, virtual environment, .gitignore
- [x] Get Gemini API key, store in .env
- [x] Script that sends a job posting to the model (extract.py)
- [x] Pydantic schema + structured output (extract.py)
- [x] Retry loop with exponential backoff for 503 errors + test (extract.py, test_extract.py)
- [x] Async FastAPI /extract endpoint + test (main.py, test_main.py)
- [x] SQLite storage: db.py (init_db, save_job, get_jobs); endpoint saves each extraction; test mocks save_job
- [x] Clean up duplicate retry loop in extract.py: unified on async_extract_job, added 10s request timeout, fail-fast on 429 quota errors, and updated test_extract.py with IsolatedAsyncioTestCase and AsyncMock

## In progress
- [ ] Nothing yet

## Next
- [ ] 10 test postings + script that scores extraction accuracy (finish full baseline run)
- [ ] Tighten extraction prompt (address skills over-extraction)
- [ ] Make company optional in schema
- [ ] Push project to GitHub
- [ ] README + deploy

## Decisions made
- Python only (no Rust/TypeScript)
- Build the agent loop by hand before using a framework
- App model: gemini-3.6-flash via a Pro-account project key (free tier). gemini-2.5-flash is not available to new projects. gemini-3.8-flash hangs with no error and no response (seen with two different keys), so avoid it until understood.
- Tests use mocks (fake model reply, fake save_job), so they are fast, free, and never touch the real database or Google
- Database stores skills as JSON text in a TEXT column (json.dumps / json.loads)
- Always use ? placeholders in SQL, never f-strings (SQL injection)
- Fail-fast on 429 quota errors: immediate raise without sleeping, allowing upstream callers to handle gracefully
- Non-blocking async sleep: use asyncio.sleep in coroutines to prevent event-loop freezing

## Known issues
- test_main.py shows an httpx deprecation warning (harmless for now)
- save_job is a normal (blocking) function called from an async endpoint. Fine at this size.
- Eval baseline (4 postings, 1 run): title 4/4, company 4/4, skills 2/4. Skills over-extraction: model adds job duties and invents skills when none are listed. Results vary between runs (non-deterministic). Fix to try: tighten the prompt, then re-run.
- Eval, partial run on gemini-3.6-flash (6 of 10 cases, daily quota ran out): title 6/6, company 5/6, skills 4/6. Not a full baseline yet.
- Prompt problems: model invents skills when none are listed (case 3, seen 3 times), and includes "nice to have" skills (case 6, GraphQL). Fix: tighten the prompt, then re-run.
- Schema problem: company is a required string, so the model writes "Not specified" when a posting names none. Fix: make company optional.

## Session log
- Oct 31: agy hit its quota. Worked with Claude chat manually. Verified extract.py + test pass, ran FastAPI endpoint, committed everything. Deleted an empty typo'd file (est_main.py).
- Nov 1: Built db.py. Endpoint now saves each extraction. Ran the full app end to end: real request, Gemini, validated JobPosting, saved to jobs.db, read back. Next: accuracy script with real postings, and the retry-loop cleanup once agy quota returns.
- Nov 2: Switched to a new API key (Pro-account project) after the free key hit its daily limit. Ran eval on 6 of 10 cases. Fixed case 4 answer key (the posting names no company). Next: finish the eval when quota resets, then agy cleanup (duplicate loop, timeout, 429 handling), then tighten the prompt.
- Nov 4: Cleaned up duplicate retry loop in extract.py: removed sync extract_job, unified on async_extract_job with asyncio.run() entry point, added 10s timeout via types.HttpOptions, added fail-fast 429 quota handling. Rewrote test_extract.py with IsolatedAsyncioTestCase and AsyncMock testing 503 retry, 3-attempt exhaustion, and 429 immediate exit. All 5 tests passing. Updated docs/retry_loop.md.
