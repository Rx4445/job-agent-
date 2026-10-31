# Job Application Agent: Progress

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

## In progress
- [ ] Nothing yet

## Next
- [ ] Store results in SQLite
- [ ] 10 test postings + script that scores extraction accuracy
- [ ] Push project to GitHub

## Decisions made
- Python only (no Rust/TypeScript)
- Build the agent loop by hand before using a framework
- App model: gemini-3.8-flash via Google AI Studio free tier (fallbacks agy added are unverified)
- API key lives in .env, never in code
- Tests use fast fake model replies where possible (to confirm in test_main.py)

## Known issues
- test_main.py shows an httpx deprecation warning (harmless for now)
- I have not yet explained the retry loop in my own words (interview prep)

## Session log
- Oct 31: agy hit its quota (resets in ~3.5 days). Worked with Claude chat manually. Verified extract.py + test pass, ran FastAPI endpoint, committed everything. Deleted an empty typo'd file (est_main.py). Next: SQLite storage.