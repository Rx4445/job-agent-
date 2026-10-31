from fastapi import FastAPI
from pydantic import BaseModel
from extract import JobPosting,async_extract_job



class JobRequest(BaseModel):
    posting: str

app = FastAPI()
@app.post("/extract", response_model=JobPosting)                                                  
async def extract(request: JobRequest) -> JobPosting:                                             
    return await async_extract_job(request.posting)




