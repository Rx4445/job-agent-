import asyncio
from datetime import datetime
import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from extract import JobPosting
from matcher import MatchResult

load_dotenv()
client = genai.Client()


class STARResponse(BaseModel):
    situation: str
    task: str
    action: str
    result: str


class InterviewQuestion(BaseModel):
    category: str
    question: str
    interviewer_intent: str
    pitfalls_to_avoid: str
    star_response: STARResponse
    proof_metrics: list[str]


class InterviewBattlecard(BaseModel):
    role_title: str
    company: str
    positioning_hook: str
    questions: list[InterviewQuestion]


def build_interview_prompt(job: JobPosting, match: MatchResult, resume_text: str) -> str:
    matching_str = ", ".join(match.matching_skills) if match.matching_skills else "General engineering"
    missing_str = ", ".join(match.missing_skills) if match.missing_skills else "None"
    job_skills_str = ", ".join(job.skills) if job.skills else "Software/AI engineering"

    return f"""You are a Principal AI Engineer and Bar Raiser at {job.company}.
You are conducting a rigorous technical and behavioral interview for the '{job.title}' role.
Your goal is to test candidate competence, evaluate system design trade-offs, and stress-test gaps.

TARGET ROLE:
- Company: {job.company}
- Role: {job.title}
- Required Skills: {job_skills_str}

MATCH & GAP ANALYSIS:
- Matched Skills: {matching_str}
- Gaps / Missing Skills: {missing_str}

CANDIDATE'S GROUND-TRUTH RESUME:
{resume_text}

INSTRUCTIONS:
1. POSITIONING HOOK:
   - Provide a 30-45 second authentic elevator pitch ("Tell me about yourself") that directly connects the candidate's real background (business analysis/demo environments at HighRadius + production RAG/ML building) to {job.company}'s mission.
2. GENERATE 5 TARGETED QUESTIONS:
   Generate exactly 5 high-signal questions across these critical dimensions:
   - Question 1 (Technical Deep-Dive): Drill down into verified matching skills ({matching_str}) like vector chunking, RAG latency, or data normalization.
   - Question 2 (System Design & Trade-Offs): Test architectural trade-offs (e.g. latency vs cost, SQLite vs Vector DB, caching strategies, rate limits).
   - Question 3 (Gap Defense / Trap Question): Target the missing skills ({missing_str}) or the career pivot from business analyst/sales to engineering.
   - Question 4 (Client-Facing & Enterprise Workflow): Test how the candidate communicates technical solutions, handles demo environments, or deals with difficult stakeholders.
   - Question 5 (Debugging & Failure Recovery): Ask for a real scenario where an AI model, data pipeline, or application broke in production and how it was diagnosed.
3. FOR EACH QUESTION:
   - Explain the interviewer's hidden intent (what they are secretly testing for).
   - Identify common pitfalls and trap answers that get candidates rejected.
   - Craft a model STAR response (Situation, Task, Action, Result) grounded strictly in the candidate's real resume metrics (10k docs, <180ms latency, 8k slides, 120+ environments, 35% time cut).
   - List the exact verified proof metrics to quote.

OUTPUT FORMAT:
Output ONLY a JSON object strictly matching this schema:
{{
  "role_title": "{job.title}",
  "company": "{job.company}",
  "positioning_hook": "...",
  "questions": [
    {{
      "category": "Technical Deep-Dive",
      "question": "...",
      "interviewer_intent": "...",
      "pitfalls_to_avoid": "...",
      "star_response": {{
        "situation": "...",
        "task": "...",
        "action": "...",
        "result": "..."
      }},
      "proof_metrics": ["..."]
    }}
  ]
}}
"""


async def async_generate_interview_battlecard(
    job: JobPosting,
    match: MatchResult,
    resume_text: str,
    model: str = "gemini-3.1-flash-lite",
    max_retries: int = 4,
) -> InterviewBattlecard:
    """Agent 3 (Interview Simulator): Generates an elite, grounded interview prep battlecard."""
    prompt = build_interview_prompt(job, match, resume_text)

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
            return InterviewBattlecard.model_validate_json(response.text)
        except Exception as e:
            if getattr(e, "code", None) == 429 or "429" in str(e):
                raise

            delay = 2 * (2 ** attempt)
            print(f"[Interview Prep Attempt {attempt + 1}/{max_retries}] Error: {e}. Retrying in {delay}s...")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay)


def save_interview_battlecard(
    battlecard: InterviewBattlecard,
    output_dir: str = "applications",
) -> str:
    """Renders the battlecard to a structured Markdown document on disk."""
    os.makedirs(output_dir, exist_ok=True)
    safe_company = "".join(c for c in battlecard.company if c.isalnum() or c in ("-", "_")).strip()
    safe_title = "".join(c for c in battlecard.role_title if c.isalnum() or c in ("-", "_")).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_company}_{safe_title}_Interview_Prep_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)

    lines = [
        f"# Interview Battlecard: {battlecard.role_title} at {battlecard.company}",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Role:** {battlecard.role_title} | **Target Company:** {battlecard.company}",
        "",
        "---",
        "",
        "## 🎯 30-Second Positioning Hook ('Tell Me About Yourself')",
        f"{battlecard.positioning_hook}",
        "",
        "---",
        "",
        "## 🛡️ Targeted Interview Questions & STAR Responses",
        "",
    ]

    for i, q in enumerate(battlecard.questions, 1):
        lines.extend([
            f"### Question {i} [{q.category}]: {q.question}",
            f"- **🕵️ What the Interviewer Is Really Testing:** {q.interviewer_intent}",
            f"- **⚠️ Pitfalls / Trap Answers to Avoid:** {q.pitfalls_to_avoid}",
            f"- **📊 Verified Proof Metrics to Quote:** {', '.join(q.proof_metrics) if q.proof_metrics else 'N/A'}",
            "",
            "#### Recommended STAR Answer:",
            f"- **Situation:** {q.star_response.situation}",
            f"- **Task:** {q.star_response.task}",
            f"- **Action:** {q.star_response.action}",
            f"- **Result:** {q.star_response.result}",
            "",
            "---",
            "",
        ])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath
