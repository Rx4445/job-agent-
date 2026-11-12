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

    return f"""You are a battle-tested technical recruiter who has reviewed thousands of applications and hates generic, buzzword-heavy AI cover letters. Your job is to draft a cover letter that sounds unmistakably human, direct, and slightly offbeat—cutting out all corporate fluff.

Target Role: {job.title} at {job.company}
Job Requirements: {job_skills_str}

Verified Matched Skills: {matching_str}
Missing / Gap Skills: {missing_str}

Candidate Resume:
{resume_text}

STRICT WRITING RULES:
1. VOICE & TONE: Write like a sharp, thoughtful human engineer speaking peer-to-peer. Never use AI clichés like "thrilled to apply", "testament to my passion", "in today's fast-paced world", or "aligns perfectly".
2. STRICT GROUNDING: ONLY reference projects and metrics that appear explicitly on the candidate resume. Do NOT fabricate numbers, tools, or past roles.
3. SKILL PROOF: For the matched skills ({matching_str}), pull the exact project from the resume that demonstrates it (e.g., citing specific metrics like latency, slide counts, or scale).
4. GAP HONESTY: If addressing missing skills ({missing_str}), do not lie. Frame them with adjacent tools or high learning velocity.
5. LENGTH: 3 short, punchy paragraphs. Clean Markdown.
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
                    http_options=types.HttpOptions(timeout=10000),
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
