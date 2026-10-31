import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel
import asyncio


class JobPosting(BaseModel):
    title: str
    company: str
    skills: list[str]


load_dotenv()
client = genai.Client()

posting = """
Junior Backend Engineer at Acme Corp (Remote, India).
We need Python, FastAPI, and SQL experience. 1-2 years preferred.
Salary: 8-12 LPA. Apply by Nov 30.
"""


def extract_job(posting: str, max_retries: int = 3) -> JobPosting:
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=JobPosting,
                ),
                model="gemini-2.5-flash",
                contents=f"List the job title, company, and required skills from this posting:\n{posting}",
            )
            return response.parsed
        except Exception as e:
            delay = 2 ** attempt
            print(f"[Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            time.sleep(delay)
async def async_extract_job(posting: str, max_retries: int = 3) -> JobPosting:                    
        for attempt in range(max_retries):                                                            
            try:                                                                                      
                response = await client.aio.models.generate_content(                                  
                    config=types.GenerateContentConfig(                                               
                        response_mime_type="application/json",                                        
                        response_schema=JobPosting,                                                   
                    ),                                                                                
                    model="gemini-2.5-flash",                                                         
                    contents=f"List the job title, company, and required skills from this posting:\n{posting}",
                )                                                                                     
                return response.parsed                                                                
            except Exception as e:                                                                    
                delay = 2 ** attempt                                                                  
                print(f"[Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")   
                if attempt == max_retries - 1:                                                        
                    raise                                                                             
                await asyncio.sleep(delay) 

    
    

if __name__ == "__main__":
    result = extract_job(posting)
    print("Extracted Result:", result)
