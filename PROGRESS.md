# Job Application Agent: Progress

## Done
- [x] Set up git, Node, VS Code
- [x] Install Antigravity CLI and log in
- [x] Create GEMINI.md rules
- [x] Set up Python, virtual environment, .gitignore
- [x] Get Gemini API key, store in .env
- [x] Script that sends a job posting to the model and prints the response (extract.py)

## In progress
- [ ] Pydantic schema + structured output with retry on invalid output

## Next
- [ ] Add retry with delay for 503 errors
- [ ] FastAPI endpoint using async
- [ ] Store results in SQLite
- [ ] 10 test postings + script that scores extraction accuracy
- [ ] Push project to GitHub

## Decisions made
- Python only (no Rust/TypeScript)
- Build the agent loop by hand before using a framework
- App model: gemini-3.8-flash via Google AI Studio free tier (fall back to gemini-3.6-flash if busy)
- API key lives in .env, never in code

## Known issues
- Free-tier model returned 503 "high demand" once; needs retry logic