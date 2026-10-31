# Manual Retry Loop & Error Handling

## Approach
To build a resilient agent without external frameworks (like LangChain or Tenacity), we implemented a pure-Python retry loop wrapping the Google GenAI extraction call.

1. **Loop Structure**: Encapsulated within `extract_job(posting: str, max_retries: int = 3) -> JobPosting`.
2. **Error Handling**: Uses a `try...except` block catching transient server errors (such as 503 Service Unavailable, 504 Deadline Exceeded, or connection timeouts).
3. **Exponential Backoff**: Computes `delay = 2 ** attempt` (1s, 2s, 4s) to prevent hammering the server during high-demand spikes.
4. **Failure Escalation**: Re-raises the exception if all retry attempts are exhausted (`attempt == max_retries - 1`).

## Decisions Made
- **Build from scratch**: Implemented using basic Python (`for`, `try/except`, `time.sleep`) to understand the core agent loop mechanics before relying on orchestration libraries.
- **Model Fallback**: Identified that preview models (`gemini-3.8-flash`) hit frequent 503 capacity limits on free tier, establishing `gemini-2.5-flash` as a reliable fallback.
- **Modular Entry Point**: Wrapped top-level script execution in `if __name__ == "__main__":` to allow clean importing in automated tests without triggering live API calls.

## How to Test
We use Python's built-in `unittest` and `unittest.mock` to simulate failures without using API quota or waiting for real-world delays:
1. **Mocking sleep**: `@patch("extract.time.sleep")` replaces pause operations with instant no-ops.
2. **Mocking Gemini**: `@patch("extract.client.models.generate_content")` intercepts API requests.
3. **Side Effects**: Set `mock_generate.side_effect = [Exception("503 High Demand"), mock_success]` to ensure the function recovers on the second attempt.

### Run tests:
```powershell
python test_extract.py
```
Expected output:
```text
[Attempt 1/3] Error: 503 High Demand. Retrying in 1s...
.
----------------------------------------------------------------------
Ran 1 test in 0.020s

OK
```
