from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from extract import JobPosting, async_extract_job
from resume import Resume, async_extract_resume
from matcher import MatchResult, match_job_and_resume
from generator import async_generate_cover_letter
from db import init_db, save_job, get_jobs


class JobRequest(BaseModel):
    posting: str


class MatchRequest(BaseModel):
    posting: str
    resume: str


class ResumeRequest(BaseModel):
    resume: str


class JobMatchItem(BaseModel):
    job_id: int
    title: str
    company: str
    match: MatchResult


class CoverLetterRequest(BaseModel):
    posting: str = ""
    job_id: int | None = None
    resume: str = ""


class CoverLetterResponse(BaseModel):
    cover_letter: str
    match: MatchResult


init_db()
app = FastAPI()


@app.post("/extract", response_model=JobPosting)
async def extract(request: JobRequest) -> JobPosting:
    result = await async_extract_job(request.posting)
    save_job(result.title, result.company, result.skills)
    return result


@app.post("/match", response_model=MatchResult)
async def match(request: MatchRequest) -> MatchResult:
    job = await async_extract_job(request.posting)
    save_job(job.title, job.company, job.skills)
    candidate = await async_extract_resume(request.resume)
    return match_job_and_resume(job, candidate)


@app.post("/match-all", response_model=list[JobMatchItem])
async def match_all(request: ResumeRequest) -> list[JobMatchItem]:
    candidate = await async_extract_resume(request.resume)
    saved_jobs = get_jobs()
    results = []
    for j in saved_jobs:
        job = JobPosting(title=j["title"], company=j["company"], skills=j["skills"])
        match_result = match_job_and_resume(job, candidate)
        results.append(
            JobMatchItem(
                job_id=j["id"],
                title=j["title"],
                company=j["company"],
                match=match_result,
            )
        )
    results.sort(key=lambda x: x.match.match_score, reverse=True)
    return results


@app.post("/cover-letter", response_model=CoverLetterResponse)
async def generate_letter(request: CoverLetterRequest) -> CoverLetterResponse:
    resume_text = request.resume.strip()
    if not resume_text:
        try:
            with open("resume.md", "r", encoding="utf-8") as f:
                resume_text = f.read().strip()
        except FileNotFoundError:
            pass

    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="No resume text provided and resume.md not found.",
        )

    if request.job_id is not None:
        saved_jobs = get_jobs()
        matched = [j for j in saved_jobs if j["id"] == request.job_id]
        if not matched:
            raise HTTPException(
                status_code=404,
                detail=f"Job with id {request.job_id} not found in database.",
            )
        target_job = matched[0]
        job = JobPosting(
            title=target_job["title"],
            company=target_job["company"],
            skills=target_job["skills"],
        )
    elif request.posting.strip():
        job = await async_extract_job(request.posting)
        save_job(job.title, job.company, job.skills)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either posting text or a valid job_id.",
        )

    candidate = await async_extract_resume(resume_text)
    match = match_job_and_resume(job, candidate)
    letter = await async_generate_cover_letter(job, match, resume_text)
    return CoverLetterResponse(cover_letter=letter, match=match)

