from fastapi import FastAPI
from pydantic import BaseModel
from extract import JobPosting, async_extract_job
from resume import Resume, async_extract_resume
from matcher import MatchResult, match_job_and_resume
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
