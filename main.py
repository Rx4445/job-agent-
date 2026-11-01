from fastapi import FastAPI
from pydantic import BaseModel
from extract import JobPosting,async_extract_job
from db import init_db, save_job



class JobRequest(BaseModel):
    posting: str

init_db() 
app = FastAPI()
@app.post("/extract", response_model=JobPosting)                                                  
async def extract(request: JobRequest) -> JobPosting:                                             
    result= await async_extract_job(request.posting)
    save_job(result.title, result.company, result.skills)
    return result




