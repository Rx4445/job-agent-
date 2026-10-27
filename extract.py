from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

posting = """
Junior Backend Engineer at Acme Corp (Remote, India).
We need Python, FastAPI, and SQL experience. 1-2 years preferred.
Salary: 8-12 LPA. Apply by Nov 30.
"""

response = client.models.generate_content(
    model="gemini-3.8-flash",
    contents=f"List the job title, company, and required skills from this posting:\n{posting}",
)
print(response.text)