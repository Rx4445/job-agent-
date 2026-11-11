# Job-to-Resume Matching Engine

## Approach
To evaluate how well a candidate fits a job posting without introducing expensive vector embeddings or external libraries, we built a deterministic, first-principles matching engine in `matcher.py`.

1. **Candidate Profile (`Resume`)**:
   - Represents structured candidate data: `name: str`, `experience_years: int`, `field: str`, `skills: list[str]`.
   - Extracted asynchronously via `async_extract_resume()` using Gemini 3.6 Flash with retry and timeout protection.

2. **Match Analysis (`MatchResult`)**:
   - **3-Layer Field Alignment (`field_match`)**:
     Checks whether the candidate's professional field aligns with the job title using a 3-layer safety net:
     - Substring check: `resume.field in job.title`
     - Reverse substring: `job.title in resume.field`
     - Word overlap: `resume_words & job_words` (catches synonym variations like "Backend Engineer" vs. "Junior Backend Developer").
   - **Skill Intersect & Gaps**:
     - Matching skills: Overlap between candidate skills and job required skills (`job_skills & candidate_skills`).
     - Missing skills: Required skills not present on the candidate's resume (`job_skills - candidate_skills`).
   - **Scoring**:
     $$\text{match\_score} = \left(\frac{\text{len(matching\_skills)}}{\text{len(job.skills)}}\right) \times 100$$
     *(Defaults to 100.0% if the posting specifies zero required skills, avoiding division by zero).*
   - **Recommendation**:
     Candidate is recommended if `field_match == True` and `match_score >= 60.0%`.

## Decisions Made
- **First-Principles Set Theory**: Used Python sets for matching and difference calculation. It executes in microseconds, is 100% deterministic, costs $0, and produces explainable skill gaps.
- **Case-Insensitive Matching with Preserved Casing**: Lowercases tokens internally so `"python"` matches `"Python"`, but preserves original title casing (`"SQL"`, `"FastAPI"`) in the output for professional presentation.
- **Skill Gaps over Pure Booleans**: Rather than a simple boolean flag, returning `missing_skills` gives the candidate or agent actionable feedback on what requirements are lacking.

## How to Test
```powershell
python -m unittest test_matcher.py
```
Tests cover:
- 100% full match
- 75% partial match with gap identification
- Field mismatches (e.g. Graphic Designer applying to Backend role)
- Case insensitivity
- Safe handling of zero-skill job postings
