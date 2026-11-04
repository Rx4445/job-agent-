# Manual Retry Loop & Error Handling

## Approach
To build a resilient agent without external frameworks (like LangChain or Tenacity), we implemented a pure-Python asynchronous retry loop wrapping the Google GenAI extraction call.

1. **Async Structure**: Encapsulated within `async def async_extract_job(posting: str, max_retries: int = 3) -> JobPosting`.
2. **Error Categorization & Fail-Fast**:
   - **429 (Quota/Rate Limit)**: Fails immediately by re-raising the error without sleeping or retrying, as exhausted quotas cannot recover within short backoff intervals.
   - **503 (Service Unavailable) & Timeouts**: Transient server/network errors are caught and retried.
3. **Exponential Backoff**: Computes `delay = 2 ** attempt` (1s, 2s, 4s) using non-blocking `await asyncio.sleep(delay)` so the event loop remains free to serve other requests.
4. **Request Timeout**: Configured via `http_options=types.HttpOptions(timeout=10000)` inside `GenerateContentConfig` to abort hanging requests after 10 seconds.
5. **Failure Escalation**: Re-raises the exception if all retry attempts are exhausted (`attempt == max_retries - 1`).

## Decisions Made
- **Pure Python Async**: Unified on `async_extract_job` and removed the duplicate synchronous copy, ensuring single-source-of-truth maintenance.
- **Fail-Fast on Quotas**: Immediately surfaces 429 quota errors to allow upstream callers (like FastAPI endpoints or multi-agent fallbacks) to handle them cleanly.
- **Top-Level Execution**: The script runs `async_extract_job` directly in `__main__` via `asyncio.run()`.

## How to Test
We test asynchronous execution using Python's `unittest.IsolatedAsyncioTestCase` and `unittest.mock.AsyncMock`:
1. **Mocking sleep**: `@patch("extract.asyncio.sleep", new_callable=AsyncMock)` simulates backoff delays instantly.
2. **Mocking Gemini**: `@patch("extract.client.aio.models.generate_content", new_callable=AsyncMock)` intercepts async API requests.
3. **Test Scenarios**:
   - Retry on 503 failure then succeed (verifying call counts and exact backoff sleep delay).
   - Maximum retries exceeded (3 consecutive failures re-raise the exception).
   - Immediate abort on 429 quota error (verifies call count is 1 and sleep is never called).
   - Retry on 503 service unavailable error.

### Run tests:
```powershell
python -m unittest test_extract.py
```
Expected output:
```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.040s

OK
```
