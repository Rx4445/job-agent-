from pydantic import BaseModel
from extract import JobPosting
from resume import Resume


class MatchResult(BaseModel):
    field_match: bool
    match_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    is_recommended: bool


def match_job_and_resume(job: JobPosting, resume: Resume) -> MatchResult:
    # 1. Field/Domain alignment (checks substring or common role keywords)
    resume_words = set(resume.field.lower().split())
    job_words = set(job.title.lower().split())

    field_match = (
        resume.field.lower() in job.title.lower()
        or job.title.lower() in resume.field.lower()
        or bool(resume_words & job_words)
    )

    # 2. Skill overlap (case-insensitive)
    candidate_skills = {s.strip().lower() for s in resume.skills}
    matching_skills = [s for s in job.skills if s.strip().lower() in candidate_skills]
    missing_skills = [s for s in job.skills if s.strip().lower() not in candidate_skills]

    # 3. Match score percentage
    if job.skills:
        match_score = round((len(matching_skills) / len(job.skills)) * 100, 1)
    else:
        match_score = 100.0

    # 4. Recommendation threshold (60%+ skill match and field alignment)
    is_recommended = field_match and match_score >= 60.0

    return MatchResult(
        field_match=field_match,
        match_score=match_score,
        matching_skills=matching_skills,
        missing_skills=missing_skills,
        is_recommended=is_recommended,
    )


if __name__ == "__main__":
    sample_job = JobPosting(
        title="Junior Backend Engineer",
        company="Acme Corp",
        skills=["Python", "FastAPI", "SQL", "Docker"],
    )

    sample_candidate = Resume(
        name="Jane Doe",
        experience_years=3,
        field="Backend Engineering",
        skills=["Python", "FastAPI", "SQL", "Git"],
    )

    result = match_job_and_resume(sample_job, sample_candidate)
    print("\n--- Match Result ---")
    print("Field Match:       ", result.field_match)
    print("Match Score:       ", f"{result.match_score}%")
    print("Matching Skills:   ", result.matching_skills)
    print("Missing Skills:    ", result.missing_skills)
    print("Recommended:       ", result.is_recommended)
