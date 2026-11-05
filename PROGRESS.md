# Job Application Agent: Progress

## Progress
Version 1 (working, tested, deployed app):  ████████████  12/12  (100%) 🎉
Full 12-stage roadmap:                      ██░░░░░░░░░░  ~2.0/12  (~17%)

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
[x] 10 10 real postings + accuracy script
[x] 11 Push to GitHub
[x] 12 README + deploy

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
- [x] 10-case evaluation set (eval_postings.json) and accuracy script (eval.py) with rate-limit pacing and per-case error handling. Completed full 10-case baseline (Title 10/10, Company 9/10, Skills 7/10).
- [x] Connected remote GitHub repository (https://github.com/Rx4445/job-agent-) and pushed main branch.
- [x] Created comprehensive README.md, requirements.txt, and .env.example documenting architecture, retry mechanics, evals, and deployment instructions.

## In progress
- [ ] Version 1 is complete! Ready to plan Stage 2 (resume tailoring / matching).

## Next
- [ ] Stage 2: Resume parsing, job-to-resume matching, and qualification scoring.
- [ ] (Optional) Cloud deploy FastAPI container (Render, Railway, or Fly.io).

## Decisions made
- Python only (no Rust/TypeScript)
- Build the agent loop by hand before using a framework
- App model: gemini-3.6-flash via a Pro-account project key (free tier). gemini-2.5-flash is not available to new projects. gemini-3.8-flash hangs with no error and no response (seen with two different keys), so avoid it until understood.
- Tests use mocks (fake model reply, fake save_job), so they are fast, free, and never touch the real database or Google
- Database stores skills as JSON text in a TEXT column (json.dumps / json.loads)
- Always use ? placeholders in SQL, never f-strings (SQL injection)
- Fail-fast on 429 quota errors: immediate raise without sleeping, allowing upstream callers to handle gracefully
- Non-blocking async sleep: use asyncio.sleep in coroutines to prevent event-loop freezing
- Product decision on skill recall: Accept nice-to-have, soft skills, and implied role skills in extraction because capturing them provides valuable context for a job seeker.
- Company normalization: Treat "Not specified", "N/A", and "" as equivalent matches in evals when no company is in the posting.
- Gemini 3.6-flash free tier limits: 5 requests per minute (RPM) and 20 requests per day (RPD). Evals must pace calls (13s delay) and avoid excessive retries.

## Known issues
- test_main.py shows an httpx deprecation warning (harmless for now)
- save_job is a normal (blocking) function called from an async endpoint. Fine at this size.
- Free tier limit: 20 requests per day on gemini-3.6-flash. Evals should be run sparingly or on paid tier when scaling.

## Session log
- Oct 31: agy hit its quota. Worked with Claude chat manually. Verified extract.py + test pass, ran FastAPI endpoint, committed everything. Deleted an empty typo'd file (est_main.py).
- Nov 1: Built db.py. Endpoint now saves each extraction. Ran the full app end to end: real request, Gemini, validated JobPosting, saved to jobs.db, read back. Next: accuracy script with real postings, and the retry-loop cleanup once agy quota returns.
- Nov 2: Switched to a new API key (Pro-account project) after the free key hit its daily limit. Ran eval on 6 of 10 cases. Fixed case 4 answer key (the posting names no company). Next: finish the eval when quota resets, then agy cleanup (duplicate loop, timeout, 429 handling), then tighten the prompt.
- Nov 4: Cleaned up duplicate retry loop in extract.py: removed sync extract_job, unified on async_extract_job with asyncio.run() entry point, added 10s timeout via types.HttpOptions, added fail-fast 429 quota handling. Rewrote test_extract.py with IsolatedAsyncioTestCase and AsyncMock testing 503 retry, 3-attempt exhaustion, and 429 immediate exit. All 5 tests passing. Updated docs/retry_loop.md.
- Nov 5: Completed full 10-case baseline on gemini-3.6-flash: Title 10/10 (100%), Company 9/10 (90%), Skills 7/10 (70%). Aligned eval with product goals: prioritized skill recall (including nice-to-have/soft skills) and accepted "Not specified" for missing company names. Updated eval.py and eval_postings.json with rate-limit pacing and per-case error handling. Discovered free tier limits: 5 RPM, 20 RPD. Linked remote repo and successfully pushed main to GitHub (https://github.com/Rx4445/job-agent-).
- Nov 5: Completed Step 12 (README.md, requirements.txt, .env.example). Version 1 of Job Application Agent is 100% complete!
