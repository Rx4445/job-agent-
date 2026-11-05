# Job Application Agent

A production-grade, async job extraction pipeline that converts messy, unstructured job postings into validated, structured data using Google Gemini, Pydantic, FastAPI, and SQLite.

Built from **first principles** in pure Python (without heavy orchestration frameworks like LangChain) to master resilient agent architectures, constrained decoding, and automated evaluations.

---

## Architecture Overview

```mermaid
flowchart TD
    A["Raw Job Posting (Text)"] --> B["FastAPI /extract Endpoint"]
    B --> C["async_extract_job()"]
    
    subgraph Agent Loop & Error Handling
        C --> D{"Gemini 3.6 Flash"}
        D -- "503 Spike / Timeout" --> E["Exponential Backoff (1s, 2s, 4s)"]
        E --> D
        D -- "429 Quota Exhausted" --> F["Fail Fast (Immediate Raise)"]
        D -- "Success (JSON Schema)" --> G["Pydantic Validation (JobPosting)"]
    end
    
    G --> H[("SQLite Storage (jobs.db)")]
    G --> I["JSON API Response"]
```

---

## Key Engineering Highlights

- **First-Principles Agent Loop:** Built manual retry logic with exponential backoff and jitter readiness instead of relying on opaque framework wrappers.
- **Structured Outputs (Constrained Decoding):** Enforces a strict Pydantic schema (`JobPosting`) at the model level via `response_mime_type="application/json"` and `response_schema`.
- **Intelligent Error Handling:**
  - **Transient Errors (503 / Timeouts):** Automatically retried with non-blocking `await asyncio.sleep(delay)`.
  - **Hard Quotas (429):** Fails fast immediately to avoid wasteful pauses when daily limits are reached.
  - **Zombie Call Prevention:** 10-second request timeout configured via `google.genai.types.HttpOptions(timeout=10000)`.
- **Async Concurrency:** Fully asynchronous pipeline using `asyncio` to prevent event-loop blocking under high traffic.
- **SQL Injection Safe Storage:** SQLite persistence using parameterized queries and JSON serialization for skill lists.
- **Automated 10-Case Evaluation Harness:** Includes a dedicated benchmark (`eval.py` + `eval_postings.json`) testing accuracy across messy, edge-case job postings with rate-limit pacing.

---

## Evaluation Benchmark

Tested across 10 realistic job postings (varying lengths, missing companies, and implied vs required skills):

| Metric | Score | Performance |
| :--- | :--- | :--- |
| **Title Accuracy** | 10 / 10 | **100%** |
| **Company Accuracy** | 10 / 10 | **100%** (normalized) |
| **Skills Accuracy** | 7 / 10 raw | Captures high-value context including nice-to-have & soft skills |

---

## Getting Started

### 1. Clone & Set Up Virtual Environment
```powershell
git clone https://github.com/Rx4445/job-agent-.git
cd job-agent-

python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and insert your Gemini API key:
```powershell
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run the API Server
```powershell
uvicorn main:app --reload
```
The server will start at `http://127.0.0.1:8000`. You can test endpoints interactively via Swagger UI at `http://127.0.0.1:8000/docs`.

---

## Running Tests & Evaluations

### Run Unit Tests (Fast & Free)
All unit tests mock external API calls and time delays, running in milliseconds:
```powershell
python -m unittest
```

### Run Model Evaluation
Runs live extractions against the 10-case evaluation set:
```powershell
python eval.py
```

---

## Project Structure

```text
├── main.py              # FastAPI application and endpoint routing
├── extract.py           # Gemini extraction logic, Pydantic schema & retry loop
├── db.py                # SQLite database connection, table initialization & queries
├── eval.py              # Evaluation script scoring extraction accuracy
├── eval_postings.json   # 10 ground-truth test cases for model evaluation
├── test_main.py         # Unit tests for the FastAPI API endpoints
├── test_extract.py      # Async unit tests for the retry loop & error handling
├── docs/                # Feature documentation & design decisions
│   ├── retry_loop.md    # Architecture of manual retry & error handling
│   └── evals.md         # Evaluation harness & baseline documentation
├── requirements.txt     # Python project dependencies
├── .env.example         # Template for environment variables
└── PROGRESS.md          # Project roadmap tracking
```
