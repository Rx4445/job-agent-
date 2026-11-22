import asyncio
import os
import re
from dataclasses import dataclass, field
from datetime import datetime

from extract import JobPosting, async_extract_job
from resume import Resume, async_extract_resume
from matcher import MatchResult, match_job_and_resume
from auditor import AuditCritique, async_generate_audited_cover_letter
from db import (
    compute_resume_hash,
    get_candidate_profile,
    init_db,
    save_candidate_profile,
    save_job,
)


@dataclass
class AgentState:
    posting_text: str
    resume_text: str = ""
    job: JobPosting | None = None
    candidate: Resume | None = None
    match: MatchResult | None = None
    decision: str = "PENDING"  # PENDING, APPROVED, ABORTED
    cover_letter: str | None = None
    audit_history: list[AuditCritique] = field(default_factory=list)
    output_path: str | None = None
    logs: list[str] = field(default_factory=list)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.logs.append(entry)
        print(entry)


def load_resume_text(path: str = "resume.md") -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Resume file not found at '{path}'.")
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def sanitize_filename(text: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"[-\s]+", "_", cleaned)


def save_application_packet(state: AgentState, output_dir: str = "applications") -> str:
    os.makedirs(output_dir, exist_ok=True)
    company = sanitize_filename(state.job.company if state.job else "Unknown_Company")
    title = sanitize_filename(state.job.title if state.job else "Role")
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{company}_{title}_{date_str}.md"
    filepath = os.path.join(output_dir, filename)

    matching = ", ".join(state.match.matching_skills) if state.match and state.match.matching_skills else "None"
    missing = ", ".join(state.match.missing_skills) if state.match and state.match.missing_skills else "None"
    score = state.match.match_score if state.match else 0.0

    audit_section = ""
    if state.audit_history:
        latest = state.audit_history[-1]
        audit_section = f"""---

## 🛡️ Multi-Agent Auditor Evaluation
- **Final Auditor Score:** {latest.score}/10
- **Factually Grounded:** {"✅ Yes" if latest.is_grounded else "❌ No"}
- **Tone Rating:** {latest.tone_rating}
- **Total Audit Turns / Revisions:** {len(state.audit_history)}
- **Auditor Feedback:** {latest.critique_notes}
"""
        if latest.hallucinated_claims:
            audit_section += f"- **Flagged Claims Purged:** {', '.join(latest.hallucinated_claims)}\n"

    content = f"""# Application Packet: {state.job.title if state.job else 'Role'} at {state.job.company if state.job else 'Company'}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Candidate:** {state.candidate.name if state.candidate else 'Candidate'}  
**Match Score:** {score}% (Recommended: {state.match.is_recommended if state.match else False})

---

## Skill Alignment Analysis
- **Matching Skills ({len(state.match.matching_skills) if state.match else 0}):** {matching}
- **Missing Skills ({len(state.match.missing_skills) if state.match else 0}):** {missing}

{audit_section}---

## Tailored Cover Letter
{state.cover_letter or "No cover letter generated."}

---

## Execution Audit Logs
"""
    for entry in state.logs:
        content += f"- {entry}\n"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return filepath


def evaluate_decision_gate(match: MatchResult, interactive: bool = True) -> bool:
    if match.match_score >= 70.0:
        print(f"\n[DECISION GATE] High fit ({match.match_score}%). Auto-approved for application.")
        return True

    missing_str = ", ".join(match.missing_skills) if match.missing_skills else "None"

    if not interactive:
        # Automated / headless mode defaults to standard recommendation threshold
        return match.is_recommended

    if match.match_score < 50.0:
        print(f"\n[DECISION GATE - WARNING] Low fit score: {match.match_score}%.")
        print(f"Missing core requirements: {missing_str}")
        user_choice = input("Fit is below 50%. Do you wish to override and generate application anyway? (y/N): ").strip().lower()
        return user_choice in ("y", "yes")
    else:
        print(f"\n[DECISION GATE - REVIEW] Moderate fit score: {match.match_score}%.")
        print(f"Missing skills: {missing_str}")
        user_choice = input("Proceed with tailored cover letter generation? (Y/n): ").strip().lower()
        return user_choice not in ("n", "no")


async def run_job_agent(
    posting_text: str,
    resume_path: str = "resume.md",
    resume_text_override: str | None = None,
    interactive: bool = True,
    output_dir: str = "applications",
) -> AgentState:
    init_db()
    state = AgentState(posting_text=posting_text)
    state.log("Agent started: Orchestrating application workflow.")

    # Step 1: Load Candidate Resume
    try:
        state.resume_text = resume_text_override or load_resume_text(resume_path)
        state.log(f"Loaded candidate resume ({len(state.resume_text)} characters).")
    except Exception as e:
        state.decision = "ABORTED"
        state.log(f"Failed to load resume: {e}")
        return state

    # Step 2: Extract Job & Save to SQLite
    try:
        state.log("Step 1/4: Ingesting and extracting job posting...")
        state.job = await async_extract_job(state.posting_text)
        save_job(state.job.title, state.job.company, state.job.skills)
        state.log(f"Job extracted: '{state.job.title}' at '{state.job.company}'. Saved to SQLite.")
    except Exception as e:
        state.decision = "ABORTED"
        state.log(f"Job extraction failed: {e}")
        return state

    # Step 3: Candidate Resume Profile (Cache First)
    try:
        resume_hash = compute_resume_hash(state.resume_text)
        cached_profile = get_candidate_profile(resume_hash)
        if cached_profile:
            state.candidate = Resume(
                name=cached_profile["name"],
                experience_years=cached_profile["experience_years"],
                field=cached_profile["field"],
                skills=cached_profile["skills"],
            )
            state.log(f"Step 2/4: Loaded candidate profile from cache (0ms): '{state.candidate.name}' ({state.candidate.field}).")
        else:
            state.log("Step 2/4: Cache miss. Extracting structured candidate profile via Gemini...")
            state.candidate = await async_extract_resume(state.resume_text)
            save_candidate_profile(
                resume_hash=resume_hash,
                name=state.candidate.name,
                experience_years=state.candidate.experience_years,
                field=state.candidate.field,
                skills=state.candidate.skills,
            )
            state.log(f"Candidate extracted via Gemini & saved to cache: '{state.candidate.name}' ({state.candidate.experience_years}y exp).")
    except Exception as e:
        state.decision = "ABORTED"
        state.log(f"Resume extraction failed: {e}")
        return state

    # Step 4: Deterministic Matching
    state.log("Step 3/4: Running deterministic match & gap analysis...")
    state.match = match_job_and_resume(state.job, state.candidate)
    state.log(f"Match evaluated: {state.match.match_score}% fit ({len(state.match.matching_skills)} matches, {len(state.match.missing_skills)} gaps).")

    # Step 5: Human-in-the-Loop Decision Gate
    approved = evaluate_decision_gate(state.match, interactive=interactive)
    if not approved:
        state.decision = "ABORTED"
        state.log("Application aborted by decision gate.")
        return state

    state.decision = "APPROVED"
    state.log("Decision gate approved. Proceeding to cover letter generation.")

    # Step 6: Generate Grounded Cover Letter via Multi-Agent Reflection
    try:
        state.log("Step 4/4: Generating tailored cover letter via Multi-Agent Reflection Loop...")
        state.cover_letter, state.audit_history = await async_generate_audited_cover_letter(
            state.job, state.match, state.resume_text
        )
        final_score = state.audit_history[-1].score if state.audit_history else 0
        state.log(f"Cover letter approved by Auditor (Score: {final_score}/10, Turns: {len(state.audit_history)}).")
    except Exception as e:
        state.decision = "FAILED_GENERATION"
        state.log(f"Cover letter generation failed: {e}")
        return state

    # Step 7: Persist Application Packet to Disk
    filepath = save_application_packet(state, output_dir=output_dir)
    state.output_path = filepath
    state.log(f"Complete application packet saved to: {filepath}")

    return state


if __name__ == "__main__":
    sample_posting = """
    Nexus AI is seeking a Junior AI Systems Engineer in Bangalore.
    We are building production RAG pipelines, vector search infrastructure, and RESTful microservices.
    Requirements:
    - Strong Python programming and RESTful API design
    - Hands-on experience with Vector DBs (Chroma or FAISS) and RAG
    - Familiarity with SQLite or relational databases
    - Experience with Docker or containerization is a plus
    - Kubernetes experience preferred
    """

    print("=" * 60)
    print("       JOB APPLICATION AGENT — AUTONOMOUS WORKFLOW       ")
    print("=" * 60)
    final_state = asyncio.run(run_job_agent(sample_posting, interactive=True))
    print("\n" + "=" * 60)
    print(f"Workflow Finished: {final_state.decision}")
    if final_state.output_path:
        print(f"Artifact created: {final_state.output_path}")
    print("=" * 60)
