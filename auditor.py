import asyncio
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from extract import JobPosting
from generator import async_generate_cover_letter
from matcher import MatchResult

load_dotenv()
client = genai.Client()


class AuditCritique(BaseModel):
    # 1. An integer rating from 1 to 10
    score: int

    # 2. A boolean: True if every metric & claim comes strictly from the resume
    is_grounded: bool

    # 3. A list of strings: Any specific claims that were invented or exaggerated
    hallucinated_claims: list[str] = []

    # 4. Tone evaluation: e.g. "authentic", "too_robotic", "too_aggressive"
    tone_rating: str

    # 5. Clear, actionable instructions for the Drafter on what to fix
    critique_notes: str


def build_auditor_prompt(cover_letter: str, resume_text: str, job: JobPosting) -> str:
    job_skills_str = ", ".join(job.skills) if job.skills else "General software/AI engineering"

    return f"""You are an elite, highly skeptical Technical Recruiter and Engineering Hiring Manager at {job.company}.
Your job is to rigorously audit this draft cold outreach cover letter for the '{job.title}' position before it is approved.

TARGET JOB:
- Company: {job.company}
- Role: {job.title}
- Required Skills: {job_skills_str}

CANDIDATE'S GROUND-TRUTH RESUME:
{resume_text}

DRAFT COVER LETTER TO AUDIT:
{cover_letter}

AUDITING RULES:
1. FACT-CHECKING (ZERO TOLERANCE FOR HALLUCINATIONS):
   - Compare every claim, tool, metric, number, and company in the letter against the candidate's resume.
   - If ANY metric, past employer, or unlisted skill is claimed without evidence in the resume, set is_grounded=False and list the exact claim in hallucinated_claims.
   - A letter with ANY hallucinations MUST NOT receive a score higher than 5.
2. TONE & ANTI-AI EVALUATION:
   - Must be natural, peer-to-peer, confident, and direct.
   - Flag generic AI filler (e.g. "I am thrilled to apply", "testament to my dedication", "delve into").
   - Classify tone_rating as "authentic", "too_robotic", or "too_aggressive".
3. RELEVANCE & PROBLEM-PROOF BRIDGE:
   - Does the letter connect the candidate's real projects to the specific problems {job.company} is solving?
   - If missing skills are addressed, is the candidate honest about them rather than bluffing?
4. SCORING & ACTIONABLE CRITIQUE:
   - Assign an integer score from 1 to 10.
   - Letters that are grounded, authentic, and persuasive score 8+.
   - Provide concrete, actionable notes in critique_notes explaining exactly what the Drafter must fix or improve.
"""


async def async_audit_cover_letter(
    cover_letter: str,
    resume_text: str,
    job: JobPosting,
    model: str = "gemini-3.1-flash-lite",
    max_retries: int = 3,
) -> AuditCritique:
    """Agent 2 (Auditor): Rigorously audits a draft cover letter against resume facts."""
    prompt = build_auditor_prompt(cover_letter, resume_text, job)

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=AuditCritique,
                    http_options=types.HttpOptions(timeout=120000),
                ),
                model=model,
                contents=prompt,
            )
            return response.parsed
        except Exception as e:
            if getattr(e, "code", None) == 429 or "429" in str(e):
                raise

            delay = 2 ** attempt
            print(f"[Auditor Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)


def build_revision_prompt(
    previous_draft: str,
    critique: AuditCritique,
    job: JobPosting,
    match: MatchResult,
    resume_text: str,
) -> str:
    """Constructs instructions for the Drafter to revise its cover letter based on Auditor feedback."""
    hallucinations_str = (
        "\n".join(f"- {c}" for c in critique.hallucinated_claims)
        if critique.hallucinated_claims
        else "None"
    )

    return f"""You are revising a cold outreach cover letter based on strict feedback from an elite Engineering Hiring Manager Auditor.

TARGET JOB: {job.title} at {job.company}

CANDIDATE'S GROUND-TRUTH RESUME:
{resume_text}

PREVIOUS DRAFT:
{previous_draft}

AUDITOR'S CRITIQUE:
- Score: {critique.score}/10
- Tone Rating: {critique.tone_rating}
- Hallucinated Claims to PURGE:
{hallucinations_str}
- Specific Revision Instructions:
{critique.critique_notes}

REVISION INSTRUCTIONS:
1. Immediately remove or correct all hallucinated claims flagged above.
2. Fix any tone issues (ensure it is authentic, peer-to-peer, confident, with zero generic corporate filler).
3. Ground every statement strictly in the resume facts.
4. Output ONLY the complete, revised Markdown cover letter.
"""


async def async_generate_audited_cover_letter(
    job: JobPosting,
    match: MatchResult,
    resume_text: str,
    max_refinements: int = 2,
    pass_score: int = 8,
    model: str = "gemini-3.1-flash-lite",
) -> tuple[str, list[AuditCritique]]:
    """Multi-Agent Reflection Loop: Drafter writes -> Auditor critiques -> Drafter revises."""
    audit_history: list[AuditCritique] = []

    # 1. Initial Draft (Agent 1)
    print(f"  [Drafter] Generating initial cover letter for '{job.title}'...")
    current_letter = await async_generate_cover_letter(job, match, resume_text, model=model)

    # 2. Initial Audit (Agent 2)
    print(f"  [Auditor] Auditing initial draft against resume facts...")
    initial_critique = await async_audit_cover_letter(current_letter, resume_text, job, model=model)
    audit_history.append(initial_critique)

    print(
        f"  [Auditor] Round 1 Result -> Score: {initial_critique.score}/10 | Grounded: {initial_critique.is_grounded} | Tone: {initial_critique.tone_rating}"
    )

    # 3. Check if Initial Draft Passes
    if initial_critique.is_grounded and initial_critique.score >= pass_score:
        print(f"  [Auditor Gate] Initial draft APPROVED (Score >= {pass_score}). Reflection loop complete.")
        return current_letter, audit_history

    # 4. Iterative Reflection Loop
    for iteration in range(1, max_refinements + 1):
        latest_critique = audit_history[-1]
        print(
            f"\n  [Refinement Loop {iteration}/{max_refinements}] Revising draft based on Auditor critique..."
        )
        if latest_critique.hallucinated_claims:
            print(f"    - Purging flagged hallucinations: {latest_critique.hallucinated_claims}")

        # Formulate revision prompt and re-draft
        rev_prompt = build_revision_prompt(
            previous_draft=current_letter,
            critique=latest_critique,
            job=job,
            match=match,
            resume_text=resume_text,
        )

        response = await client.aio.models.generate_content(
            config=types.GenerateContentConfig(
                http_options=types.HttpOptions(timeout=120000),
            ),
            model=model,
            contents=rev_prompt,
        )
        current_letter = response.text

        # Re-audit revised draft
        print(f"  [Auditor] Re-auditing revised draft (Turn {iteration})...")
        new_critique = await async_audit_cover_letter(current_letter, resume_text, job, model=model)
        audit_history.append(new_critique)

        print(
            f"  [Auditor] Turn {iteration} Result -> Score: {new_critique.score}/10 | Grounded: {new_critique.is_grounded} | Tone: {new_critique.tone_rating}"
        )

        if new_critique.is_grounded and new_critique.score >= pass_score:
            print(f"  [Auditor Gate] Revised draft APPROVED (Score {new_critique.score} >= {pass_score}).")
            break

    return current_letter, audit_history
