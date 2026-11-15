import re
from pydantic import BaseModel
from extract import JobPosting
from resume import Resume


class MatchResult(BaseModel):
    field_match: bool
    match_score: float
    matching_skills: list[str]
    missing_skills: list[str]
    is_recommended: bool


def is_skill_match(job_skill: str, candidate_skill: str) -> bool:
    j = job_skill.lower().strip()
    c = candidate_skill.lower().strip()

    # 1. Exact match or Substring match (e.g. "python" in "python programming")
    if j == c or j in c or c in j:
        return True

    # 2. Token / Keyword overlap (e.g. "RESTful APIs" vs "RESTful API design")
    stopwords = {"or", "and", "the", "in", "of", "with"}
    j_words = set(re.findall(r"\w+", j)) - stopwords
    c_words = set(re.findall(r"\w+", c)) - stopwords
    return bool(j_words & c_words)


def match_job_and_resume(job: JobPosting, resume: Resume) -> MatchResult:
    # 1. Field/Domain alignment (checks substring or common role keywords)
    resume_words = set(resume.field.lower().split())
    job_words = set(job.title.lower().split())

    field_match = (
        resume.field.lower() in job.title.lower()
        or job.title.lower() in resume.field.lower()
        or bool(resume_words & job_words)
    )

    # 2. Skill overlap with multi-layer alignment
    matching_skills = []
    missing_skills = []
    for js in job.skills:
        if any(is_skill_match(js, cs) for cs in resume.skills):
            matching_skills.append(js)
        else:
            missing_skills.append(js)

    # 3. Match score percentage
    if job.skills:
        match_score = round((len(matching_skills) / len(job.skills)) * 100, 1)
    else:
        match_score = 100.0

    # 4. Recommendation threshold (60%+ skill match with field alignment OR high skill match >= 75%)
    is_recommended = (field_match or match_score >= 75.0) and match_score >= 60.0

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
