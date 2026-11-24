import asyncio
from datetime import datetime
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from extract import JobPosting
from matcher import MatchResult

load_dotenv()
client = genai.Client()


class OutreachDraft(BaseModel):
    company: str = Field(description="Target company name")
    role: str = Field(description="Target job title")
    subject_lines: list[str] = Field(description="2-3 punchy, high-open-rate email subject lines")
    hook: str = Field(description="1 conversational sentence connecting to the company or team")
    proof_points: list[str] = Field(
        description="1-2 concise bullet points highlighting authentic candidate metrics/achievements"
    )
    email_body: str = Field(
        description="Complete, polished cold email under 120 words with a low-friction CTA"
    )
    linkedin_dm: str = Field(
        description="Ultra-concise LinkedIn InMail or DM under 75 words"
    )


def build_outreach_prompt(job: JobPosting, match: MatchResult, resume_text: str) -> str:
    matching_str = ", ".join(match.matching_skills) if match.matching_skills else "General engineering"
    missing_str = ", ".join(match.missing_skills) if match.missing_skills else "None"
    job_skills_str = ", ".join(job.skills) if job.skills else "Software/AI engineering"

    return f"""You are drafting a high-converting recruiter cold outreach packet from an engineer to a hiring manager or technical recruiter.

TARGET ROLE:
- Company: {job.company}
- Role: {job.title}
- Required Skills: {job_skills_str}

MATCH & GAP CONTEXT:
- Matched Skills: {matching_str}
- Gaps / Missing: {missing_str}

CANDIDATE GROUND-TRUTH RESUME:
{resume_text}

STRICT WRITING RULES:
1. SUBJECT LINES: Provide 2-3 punchy, high-open-rate options (e.g., referencing a key metric or the specific role).
2. HOOK: 1 conversational sentence referencing what {job.company} is building. Never say "I hope this email finds you well" or "I am thrilled to apply".
3. PROOF POINTS: 1-2 bullet points with exact quantitative proof from the resume (e.g. 180+ SQL scripts, 150+ client walkthroughs, HITL portal).
4. EMAIL BODY: Complete cold email under 120 words with a low-friction CTA (e.g., 10-min chat).
5. LINKEDIN DM: Ultra-concise version under 75 words.
6. ZERO HALLUCINATION: Only use real numbers and projects from the resume.

OUTPUT FORMAT:
Output ONLY a valid JSON object matching this schema:
{{
  "company": "{job.company}",
  "role": "{job.title}",
  "subject_lines": ["..."],
  "hook": "...",
  "proof_points": ["..."],
  "email_body": "...",
  "linkedin_dm": "..."
}}
"""


async def async_generate_outreach(
    job: JobPosting,
    match: MatchResult,
    resume_text: str,
    model: str = "gemini-3.1-flash-lite",
    max_retries: int = 3,
) -> OutreachDraft:
    prompt = build_outreach_prompt(job, match, resume_text)

    for attempt in range(max_retries):
        try:
            response = await client.aio.models.generate_content(
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    http_options=types.HttpOptions(timeout=120000),
                ),
                model=model,
                contents=prompt,
            )
            return OutreachDraft.model_validate_json(response.text)
        except Exception as e:
            # 1. 429 Fail-Fast
            if getattr(e, "code", None) == 429 or "429" in str(e):
                raise

            # 2. Exponential Backoff on 503 / Network Errors
            delay = 2 * (2 ** attempt)
            print(f"[Outreach Agent Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)


def save_outreach_packet(
    draft: OutreachDraft,
    output_dir: str = "applications",
) -> str:
    """Saves the cold outreach packet into a structured Markdown document on disk."""
    os.makedirs(output_dir, exist_ok=True)
    safe_company = "".join(c for c in draft.company if c.isalnum() or c in ("-", "_")).strip()
    safe_title = "".join(c for c in draft.role if c.isalnum() or c in ("-", "_")).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_company}_{safe_title}_Outreach_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    lines = [
        f"# Recruiter Cold Outreach Packet: {draft.role} at {draft.company}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Target Company:** {draft.company} | **Role:** {draft.role}",
        "",
        "---",
        "",
        "## 📧 Recommended Subject Lines",
    ]
    for s in draft.subject_lines:
        lines.append(f"- `{s}`")

    lines.extend([
        "",
        "---",
        "",
        "## 🎣 Conversational Hook",
        f"{draft.hook}",
        "",
        "## 📊 Verified Proof Points",
    ])
    for p in draft.proof_points:
        lines.append(f"- {p}")

    lines.extend([
        "",
        "---",
        "",
        "## ✉️ Cold Email Draft (<120 words)",
        "",
        "```text",
        draft.email_body.strip(),
        "```",
        "",
        "---",
        "",
        "## 💬 LinkedIn InMail / Direct Message (<75 words)",
        "",
        "```text",
        draft.linkedin_dm.strip(),
        "```",
        "",
    ])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath
