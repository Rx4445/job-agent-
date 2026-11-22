# Job Application Agent: Progress

## Progress
Version 1 (working, tested, deployed app):  ████████████  12/12  (100%) 🎉
Stage 2 (Resume & Match Engine):           ████████████  6/6    (100%) 🎉
Stage 3 (Cover Letter & Application Gen):   ████████████  5/5    (100%) 🎉
Stage 4 (Autonomous CLI Agent Loop):        ████████████  7/7    (100%) 🎉
Stage 5 (Agent Evals & Interactive CLI):    ████████████  4/4    (100%) 🎉
Stage 6 (Batch Ingestion & Leaderboard):    ████████████  6/6    (100%) 🎉
Stage 7 (Live Job Board Ingestion):         ████████████  7/7    (100%) 🎉
Stage 8 (Multi-Agent Reflection & Auditor):  ████████████  6/6    (100%) 🎉
Stage 9 (Interview Simulator Agent):          ████████████  6/6    (100%) 🎉
Full 12-stage roadmap:                      ██████████░░  ~10.0/12 (~83.3%) 🚀

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

Stage 2 checklist (Resume Parsing & Match Scoring):
[x] 1 Resume schema & async extraction with retry loop (resume.py)
[x] 2 Unit tests for resume extraction with mock retries (test_resume.py)
[x] 3 Match & gap analysis engine with 3-layer role alignment (matcher.py)
[x] 4 Unit tests covering matching edge cases (test_matcher.py)
[x] 5 Expose matching via FastAPI endpoint POST /match (main.py, test_main.py)
[x] 6 Batch matching against saved SQLite database jobs POST /match-all (main.py, test_main.py)

Stage 3 checklist (Cover Letter & Tailored Application Generation):
[x] 1 Anti-AI recruiter prompt design & strict grounding logic (generator.py)
[x] 2 Async cover letter generation with 10s timeout, 503 backoff, and 429 fail-fast (generator.py)
[x] 3 Unit test suite for generator edge cases and prompt synthesis (test_generator.py)
[x] 4 Expose via FastAPI POST /cover-letter supporting raw text, job_id, and resume.md fallback (main.py, test_main.py)
[x] 5 Technical architecture and verification documentation (docs/cover_letter.md)

Stage 4 checklist (Autonomous CLI Agent Loop):
[x] 1 AgentState dataclass with execution audit logs (agent.py)
[x] 2 Multi-step tool orchestration across extract, match, generate, and persist (agent.py)
[x] 3 Human-in-the-Loop (HITL) decision gate with auto-approval, review, and warning paths (agent.py)
[x] 4 Complete application packet persistence in applications/ with gitignore protection (agent.py)
[x] 5 Unit test suite covering all decision branches, aborts, and error handling (test_agent.py)
[x] 6 Technical architecture and state machine documentation (docs/agent_loop.md)
[x] 7 Content-addressable SHA-256 resume caching layer in SQLite (db.py, test_db.py)

Stage 5 checklist (Agent Decision Evals & Interactive CLI):
[x] 1 Automated Agent Decision & Safety Benchmark across 5 diverse scenarios (eval_agent.py)
[x] 2 Interactive Job Hunter CLI with multiline console input, file input, and headless mode (cli.py)
[x] 3 Comprehensive unit test suite for CLI interaction and error handling (test_cli.py)
[x] 4 Stage 5 evaluation and CLI documentation (docs/stage5_evals_cli.md)

Stage 6 checklist (Batch Ingestion & Leaderboard Ranking):
[x] 1 Multi-file directory scanner with extension filtering and deterministic sorting (scan_job_files)
[x] 2 Batch evaluation and descending score ranking engine (evaluate_batch_jobs)
[x] 3 Fixed-width ASCII Leaderboard terminal renderer (render_leaderboard)
[x] 4 Batch application generator with selective and auto-dispatch (generate_batch_applications)
[x] 5 Isolated unit test suite with mock coverage (test_batch.py)
[x] 6 Technical architecture documentation (docs/batch_processing.md)

Stage 7 checklist (Live Job Board Ingestion):
[x] 1 Lightweight HTML text sanitizer converting web tags to clean Markdown (clean_html_content)
[x] 2 Public Greenhouse API client fetching live jobs without authentication (fetch_greenhouse_jobs)
[x] 3 Keyword relevance filtering for engineering/AI roles (filter_relevant_jobs)
[x] 4 SQLite job deduplication checking jobs.db before LLM extraction (get_existing_job)
[x] 5 Live batch ranking & dispatch pipeline (ingest_live_board_and_rank)
[x] 6 Unit test suite covering HTML cleaning, mock APIs, and deduplication (test_boards.py)
[x] 7 Technical architecture documentation (docs/job_boards.md)

Stage 8 checklist (Multi-Agent Reflection & Auditor Loop):
[x] 1 Structured critique schema with grounding & hallucination flags (AuditCritique in auditor.py)
[x] 2 Adversarial recruiter auditor persona & prompt design (build_auditor_prompt)
[x] 3 Async auditor agent with retry backoff and 120s timeout (async_audit_cover_letter)
[x] 4 Bounded multi-agent reflection loop with critique-driven revision (async_generate_audited_cover_letter)
[x] 5 Unit test suite covering audit parsing, hallucination catches, 503 retries, and multi-turn refinement (test_auditor.py - 8 tests)
[x] 6 Technical architecture documentation (docs/multi_agent_auditor.md)

Stage 9 checklist (Automated Interview Prep & Question Simulator):
[x] 1 Structured InterviewBattlecard & STARResponse schemas (interview.py)
[x] 2 Adversarial Bar Raiser persona & 5-question prompt engineering (build_interview_prompt)
[x] 3 Async battlecard generation with client-side Pydantic validation (async_generate_interview_battlecard)
[x] 4 Markdown battlecard disk persistence in applications/ (save_interview_battlecard)
[x] 5 Unit test suite covering prompt synthesis, 503 retries, 429 fail-fast, and file persistence (test_interview.py - 5 tests)
[x] 6 Technical architecture documentation (docs/interview_simulator.md)

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
- [x] Implemented Stage 2 core: Resume schema (`resume.py`), async extraction, unit tests (`test_resume.py`), deterministic matching engine (`matcher.py`), and test suite (`test_matcher.py`).
- [x] Exposed single matching via FastAPI `POST /match` and batch ranking against SQLite jobs via `POST /match-all`. Added unit tests in `test_main.py`. All 15 tests passing.
- [x] Built Stage 3: Cover letter generator (`generator.py`) with anti-AI persona and strict project grounding, unit tests (`test_generator.py`), and dual-mode FastAPI endpoint `POST /cover-letter` with `resume.md` fallback. All 24 tests passing.
- [x] Built Stage 4: Autonomous CLI Agent Loop (`agent.py`) in pure Python with state machine, Human-in-the-Loop decision gates, artifact generation, unit tests (`test_agent.py`), and docs (`docs/agent_loop.md`). All 29 tests passing.
- [x] Built Candidate Profile SHA-256 Caching layer in `db.py` & `agent.py`: added `candidate_profile` table in SQLite, content-hashing via `compute_resume_hash`, cache-hit bypass (0ms execution, 0 tokens), and dedicated tests (`test_db.py`). All 38 tests passing in ~0.38s.
- [x] Built Stage 5: Agent Decision Benchmark (`eval_agent.py`) with 100% gate accuracy and 100% gap recall, Interactive CLI Copilot (`cli.py`), and test suite (`test_cli.py`). All 46 tests passing in ~0.71s. Documented in `docs/stage5_evals_cli.md`.
- [x] Built Stage 6: Batch Job Ingestion & Leaderboard Ranking (`batch.py`) with directory scanning, descending leaderboard table, interactive and headless application generation, and unit tests (`test_batch.py`). All 53 unit tests passing in ~0.64s. Documented in `docs/batch_processing.md`.
- [x] Built Stage 7: Automated Job Board Ingestion (`boards.py`) with public Greenhouse REST API client, regex/html entity text sanitization, role keyword relevance filtering, SQLite job deduplication (`get_existing_job`), and full batch ranking integration. Added `test_boards.py` (10 tests). All 64 unit tests passing in ~1.08s. Documented in `docs/job_boards.md`.
- [x] Built Stage 8: Multi-Agent Reflection Architecture (`auditor.py`) with structured `AuditCritique` Pydantic schema, adversarial technical recruiter auditor persona, and iterative reflection feedback loop (`async_generate_audited_cover_letter`). Added `test_auditor.py` (8 tests). All 72 unit tests passing in ~1.21s. Documented in `docs/multi_agent_auditor.md`. Reached 75% on 12-stage roadmap.
- [x] Built Stage 9: Automated Interview Prep & Question Simulator (`interview.py`) with structured `InterviewBattlecard` schema, adversarial Bar Raiser persona, client-side Pydantic validation, and STAR response generator. Added `test_interview.py` (5 tests). All 77 unit tests passing in ~1.07s. Documented in `docs/interview_simulator.md`. Advanced roadmap to 83.3% (10/12 stages complete).

## In progress
- [ ] Wire up multi-agent reflection into `agent.py` and `batch.py` (replace legacy `async_generate_cover_letter` with `async_generate_audited_cover_letter`).

## Next
- [ ] Stage 10: Multi-Platform ATS Expansion (Lever & Workday API connectors).
- [ ] Stage 11: Real-time Email & Cold Outreach Notification Agent.


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
- Deterministic set matching: Used pure Python set operations (`&`, `-`) for skill matching and gap identification (instant, zero-cost, reproducible).
- 3-layer role alignment: Used substring, reverse substring, and token overlap to match titles across wording variations.
- Batch SQLite ranking: `/match-all` pulls all stored jobs from database and ranks them in memory via Python sorting (`key=lambda x: x.match.match_score, reverse=True`).
- Content-addressable resume caching: Hash `resume.md` via SHA-256 (`compute_resume_hash`). Match against `candidate_profile` table in `jobs.db` to bypass Gemini extraction on repeated runs (0ms latency, zero API quota consumed). Auto-refreshes when resume text changes.

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
- Nov 6-11: Built Stage 2: Resume schema & extraction (resume.py), unit tests (test_resume.py), matching engine (matcher.py), 5 test scenarios (test_matcher.py), POST /match endpoint, and POST /match-all batch ranking against SQLite database. All 15 tests passing.
- Nov 11: Added `*.pdf` and `resume.md` to `.gitignore` to prevent binary/sensitive resume commits and avoid PDF parsing 400 errors. Created clean markdown template `resume.md` for text-based extraction and testing.
- Nov 12: Built Stage 3 (Cover Letter Generation). Designed anti-AI recruiter prompt with strict grounding in candidate resume metrics. Created generator.py with 10s timeout, 503 backoff, and 429 fail-fast. Added test_generator.py (5 tests). Implemented POST /cover-letter in main.py supporting raw posting text, saved job_id, and resume.md fallback, plus 4 unit tests in test_main.py. All 24 tests passing. Documented in docs/cover_letter.md.
- Nov 13: Built Stage 4 (Autonomous CLI Agent Loop). Designed AgentState with execution audit logs, multi-step tool orchestration (load resume -> extract job -> SQLite -> deterministic match -> decision gate -> cover letter -> persist packet). Implemented Human-in-the-Loop decision gate (auto-approve >=70%, prompt 50-69%, warn/abort <50%). Added test_agent.py (5 tests). All 29 tests passing. Documented in docs/agent_loop.md.
- Nov 14: Added Content-Addressable SHA-256 Resume Profile Cache in `db.py` and `agent.py`. Integrated `candidate_profile` SQLite table with instant 0ms cache-hit bypass. Created `test_db.py` (5 tests) and updated `test_agent.py` to test cache hit and miss branches (7 tests). All 38 unit tests passing. Updated docs/agent_loop.md.
- Nov 15: Pushed Stage 4 commit `de97668` to GitHub. Built Stage 5: Agent Decision Benchmark (`eval_agent.py`) with 5 diverse scenarios (100% gate accuracy, 100% gap recall), Interactive Job Hunter CLI (`cli.py`), unit tests (`test_cli.py`), and documentation (`docs/stage5_evals_cli.md`). Total test suite grew to 46 unit tests passing in ~0.71s. Reached 50% milestone on 12-stage roadmap.
- Nov 16 (Morning): Pushed Stage 5 commit `545ba89` to GitHub. Built Stage 6: Batch Job Ingestion & Leaderboard Ranking (`batch.py`) with multi-file directory scanning, descending match sorting, ASCII Leaderboard rendering, and batch cover letter generation. Added `test_batch.py` (7 tests). Total test suite grew to 53 unit tests passing in ~0.64s. Documented in `docs/batch_processing.md`. Reached ~58% on 12-stage roadmap.
- Nov 16 (Afternoon): Built Stage 7: Automated Job Board Ingestion (`boards.py`) connecting directly to live public Greenhouse REST API. Built HTML text sanitizer (`clean_html_content`), engineering keyword filter, SQLite job deduplication (`get_existing_job`), and full leaderboard dispatch. Added `test_boards.py` (10 tests). Total test suite grew to 64 unit tests passing in ~1.08s. Documented in `docs/job_boards.md`. Reached ~67% on 12-stage roadmap.
- Nov 20: Built Stage 8: Multi-Agent Reflection & Auditor Loop (`auditor.py`). Implemented `AuditCritique` Pydantic schema, adversarial hiring manager auditor prompt, async audit agent, and bounded multi-turn reflection loop (`async_generate_audited_cover_letter`). Added unit test suite `test_auditor.py` (8 tests). All 72 unit tests passing in ~1.21s. Documented in `docs/multi_agent_auditor.md`. Advanced roadmap to 75.0% (9/12 stages complete).
