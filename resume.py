import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel

load_dotenv()
client = genai.Client()


class Resume(BaseModel):
    name: str
    experience_years: int
    field: str
    skills: list[str]


async def async_extract_resume(resume_text: str, max_retries: int = 3) -> Resume:
    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Resume,
                    http_options=types.HttpOptions(timeout=10000),
                ),
                model="gemini-3.6-flash",
                contents=f"Extract the candidate's name, total years of experience as an integer, primary professional field, and technical skills from this resume:\n{resume_text}",
            )
            return response.parsed
        except Exception as e:
            if getattr(e, "code", None) == 429 or "429" in str(e):
                raise

            delay = 2 ** attempt
            print(f"[Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)


sample_resume = """
Jane Doe
Senior Backend Engineer with 5 years of experience in distributed systems.
Primary focus in Python, FastAPI, PostgreSQL, Docker, and AWS.
Built scalable microservices and led team migration to Kubernetes.
"""

if __name__ == "__main__":
    result = asyncio.run(async_extract_resume(sample_resume))
    print("\n--- Extracted Resume ---")
    print("Name:", result.name)
    print("Experience (years):", result.experience_years)
    print("Field:", result.field)
    print("Skills:", result.skills)
