# Evaluation & Accuracy Scoring

## Approach
To measure the extraction quality of the agent on realistic, messy job postings without relying on subjective manual checking, we built a ground-truth evaluation harness.

1. **Test Dataset (`eval_postings.json`)**:
   - 10 diverse job postings representing real-world variance: standard postings, missing company names, short recruiter messages, postings with no listed skills, and postings with "nice-to-have" vs required skills.
   - Ground truth answer key with expected `title`, `company`, and `skills`.

2. **Scoring Harness (`eval.py`)**:
   - Iterates through the test cases using `async_extract_job(posting, max_retries=5)`.
   - Normalizes text (case-folding, whitespace trimming).
   - Normalizes company names so that `"Not specified"`, `"N/A"`, and `""` are treated as equivalent matches when no company is provided.
   - Paces calls with a 13-second sleep between cases to respect the Free Tier 5 RPM (requests per minute) limit.
   - Implements per-case exception handling so a single failed request doesn't crash the entire evaluation run.

## Decisions Made
- **Recall over Strict Exclusion**: In a job application assistant, capturing "nice-to-have" skills (e.g. GraphQL) or soft skills (e.g. Communication) is more useful to the user than artificially strict precision. The evaluation criteria was updated to reward useful skill recall.
- **Explicit Fallbacks**: For job postings that omit the company name, the model returning `"Not specified"` is accepted as a valid match for missing company data.
- **Rate-Limiting & Quota Management**: Identified `gemini-3.6-flash` free tier restrictions:
  - 5 requests per minute (RPM)
  - 20 requests per day (RPD)
  Evals pace requests and limit retries to conserve daily quota.

## Baseline Results (10 Cases)
- **Title Accuracy**: 10 / 10 (100%)
- **Company Accuracy**: 9 / 10 (90% raw; 100% normalized with "Not specified")
- **Skills Accuracy**: 7 / 10 (70% raw; captures full context including nice-to-have skills)

## How to Run Evals
```powershell
python eval.py
```
*(Runs with a 13-second pacing delay between requests to stay within API rate limits).*
