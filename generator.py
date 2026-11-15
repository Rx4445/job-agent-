import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from extract import JobPosting
from matcher import MatchResult

load_dotenv()
client = genai.Client()


def build_cover_letter_prompt(job: JobPosting, match: MatchResult, resume_text: str) -> str:
    matching_str = ", ".join(match.matching_skills) if match.matching_skills else "None specified"
    missing_str = ", ".join(match.missing_skills) if match.missing_skills else "None"
    job_skills_str = ", ".join(job.skills) if job.skills else "General engineering"

    return f"""You are drafting a cold outreach cover letter from a sharp, ambitious software/AI engineer to an engineering hiring manager.
The candidate speaks directly, peer-to-peer, with zero corporate fluff and complete self-awareness.

Target Role: {job.title} at {job.company}
Job Requirements: {job_skills_str}

Verified Matched Skills: {matching_str}
Missing / Gap Skills: {missing_str}

Candidate Resume:
{resume_text}

STRICT WRITING RULES:
1. OPENING HOOK (HUMAN & SELF-AWARE):
   - Start with a natural greeting: "Hi [Team / Hiring Manager at {job.company}],"
   - Acknowledge this is a cold outreach and they get 10 of these an hour.
   - Be refreshingly honest: acknowledge using AI to assist ("of course I used AI to help draft this—it would be stupid not to"), but note that you took the time to strip out all the monotonous buzzwords, clichés, and robotic corporate filler that usually makes recruiters throw out a resume.
2. PROBLEM-TO-PROOF BRIDGE:
   - Identify the actual engineering problem {job.company} is trying to solve with {job.title} based on requirements ({job_skills_str}).
   - For the matched skills ({matching_str}), pull the exact project from the resume that demonstrates solving that type of problem (use exact metrics like document scale, slide counts, accuracy % gains, or latency numbers).
3. GAP HONESTY:
   - If addressing missing skills ({missing_str}), be completely upfront and honest. Don't claim to have run production clusters if you haven't. Frame them with related tools you use daily and rapid ramp-up ability.
4. CLOSING:
   - Close simply and directly: "You have real problems with [X], and I've built projects that solve those exact challenges. I'd appreciate any opportunity to chat and see if I can help the team."
   - Sign off: "Best, [Candidate Name]".
5. STRICT GROUNDING:
   - NEVER invent projects, metrics, numbers, or past employers not in the resume.
   - Keep it to 3-4 clean, punchy paragraphs in Markdown. Never use words like "delve", "tapestry", "moreover", "spearheaded", "testament", or "passion".
"""


async def async_generate_cover_letter(
    job: JobPosting,
    match: MatchResult,
    resume_text: str,
    max_retries: int = 3,
) -> str:
    prompt = build_cover_letter_prompt(job, match, resume_text)

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                config=types.GenerateContentConfig(
                    http_options=types.HttpOptions(timeout=30000),
                ),
                model="gemini-3.6-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            if getattr(e, "code", None) == 429 or "429" in str(e):
                raise

            delay = 2 ** attempt
            print(f"[Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)


if __name__ == "__main__":
    sample_job = JobPosting(
        title="AI Engineer",
        company="Nexus AI",
        skills=["Python", "RAG", "Vector DBs", "Kubernetes"],
    )
    sample_match = MatchResult(
        field_match=True,
        match_score=75.0,
        matching_skills=["Python", "RAG", "Vector DBs"],
        missing_skills=["Kubernetes"],
        is_recommended=True,
    )
    sample_resume = "Aarya Pradhan. Built RAG with Chroma and FAISS over 10k docs under 180ms."

    result = asyncio.run(async_generate_cover_letter(sample_job, sample_match, sample_resume))
    print("\n--- Generated Cover Letter ---")
    print(result)
