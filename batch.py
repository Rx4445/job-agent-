import os                                                                                         
import glob                                                                                       
import asyncio                                                                                    
from dataclasses import dataclass                                                                 
from extract import JobPosting, async_extract_job                                                 
from resume import Resume, async_extract_resume                                                   
from matcher import MatchResult, match_job_and_resume                                             
from auditor import async_generate_audited_cover_letter                                                 
from outreach import async_generate_outreach, save_outreach_packet
from db import init_db, save_job, compute_resume_hash, get_candidate_profile,save_candidate_profile                                                                            
from agent import load_resume_text, save_application_packet, AgentState                           
                                                                                                    
@dataclass                                                                                        
class BatchJobResult:                                                                             
    source_file: str                                                                              
    job: JobPosting                                                                               
    match: MatchResult                                                                            
    decision: str  # "APPROVED", "REVIEW", "ABORTED"                                              
    cover_letter: str | None = None                                                               
    outreach_path: str | None = None
    output_path: str | None = None                                                                
                                                                                                    
def scan_job_files(directory: str) -> list[tuple[str, str]]:
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"Directory not found: '{directory}'")

    results = []

    # 1. os.listdir gets all file names in the folder
    # We sort them so they are read in a clean, alphabetical order
    for filename in sorted(os.listdir(directory)):

        # 2. Filter: only grab files ending in .txt or .md
        if filename.endswith(".txt") or filename.endswith(".md"):

            # 3. Create the full path (e.g. sample_jobs/01_nexus.txt)
            filepath = os.path.join(directory, filename)

            # 4. Open and read the text
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()

            # 5. Append (filepath, content) tuple
            results.append((filepath, content))

    return results


def classify_batch_decision(score: float) -> str:
    if score >= 70.0:
        return "APPROVED"
    elif score >= 50.0:
        return "REVIEW"
    return "ABORTED"


async def evaluate_batch_jobs(
    directory: str,
    resume_path: str = "resume.md",
) -> tuple[list[BatchJobResult], str, Resume]:
    """Ingests, parses, scores, and ranks all job files in a directory against the candidate resume."""
    init_db()
    resume_text = load_resume_text(resume_path)

    # 1. Load candidate profile from cache or extract
    resume_hash = compute_resume_hash(resume_text)
    cached = get_candidate_profile(resume_hash)
    if cached:
        candidate = Resume(
            name=cached["name"],
            experience_years=cached["experience_years"],
            field=cached["field"],
            skills=cached["skills"],
        )
    else:
        candidate = await async_extract_resume(resume_text)
        save_candidate_profile(
            resume_hash=resume_hash,
            name=candidate.name,
            experience_years=candidate.experience_years,
            field=candidate.field,
            skills=candidate.skills,
        )

    # 2. Scan and evaluate all job postings
    files = scan_job_files(directory)
    results: list[BatchJobResult] = []

    for filepath, posting_text in files:
        job = await async_extract_job(posting_text)
        save_job(job.title, job.company, job.skills)
        match = match_job_and_resume(job, candidate)
        decision = classify_batch_decision(match.match_score)

        results.append(
            BatchJobResult(
                source_file=filepath,
                job=job,
                match=match,
                decision=decision,
            )
        )

    # 3. Rank jobs by match score descending (highest fit first)
    results.sort(key=lambda r: r.match.match_score, reverse=True)
    return results, resume_text, candidate


def render_leaderboard(results: list[BatchJobResult]) -> None:
    """Renders a clean ASCII leaderboard table ranking evaluated jobs."""
    print("\n" + "=" * 95)
    print("                              BATCH JOB FIT LEADERBOARD                              ")
    print("=" * 95)
    header = f"{'Rank':<5} {'Score':<8} {'Decision':<11} {'Company':<18} {'Role':<26} {'Gaps'}"
    print(header)
    print("-" * 95)

    for rank, res in enumerate(results, 1):
        score_str = f"{res.match.match_score:.1f}%"
        company = (res.job.company[:16] + "..") if len(res.job.company) > 18 else res.job.company
        role = (res.job.title[:24] + "..") if len(res.job.title) > 26 else res.job.title
        gaps = ", ".join(res.match.missing_skills[:3]) if res.match.missing_skills else "None"
        if len(res.match.missing_skills) > 3:
            gaps += f" (+{len(res.match.missing_skills) - 3} more)"
        gaps_str = (gaps[:24] + "..") if len(gaps) > 26 else gaps

        row = f"{rank:<5} {score_str:<8} {res.decision:<11} {company:<18} {role:<26} {gaps_str}"
        print(row)

    print("=" * 95)


async def generate_batch_applications(
    selected_results: list[BatchJobResult],
    resume_text: str,
    candidate: Resume,
    output_dir: str = "applications",
) -> list[str]:
    """Generates tailored cover letters and persists application packets for selected jobs."""
    generated_paths: list[str] = []
    print(f"\n[GENERATING] Building application packets for {len(selected_results)} selected job(s)...")

    for res in selected_results:
        print(f"  -> Drafting and auditing letter for '{res.job.title}' at '{res.job.company}'...")
        res.cover_letter, audit_history = await async_generate_audited_cover_letter(res.job, res.match, resume_text)

        outreach_draft = None
        outreach_path = None
        try:
            print(f"  -> Drafting recruiter cold outreach for '{res.job.title}'...")
            outreach_draft = await async_generate_outreach(res.job, res.match, resume_text)
            outreach_path = save_outreach_packet(outreach_draft, output_dir=output_dir)
            res.outreach_path = outreach_path
            print(f"     Outreach Saved: {outreach_path}")
        except Exception as e:
            print(f"     [Warning] Outreach generation skipped: {e}")

        state = AgentState(
            posting_text="",
            resume_text=resume_text,
            job=res.job,
            candidate=candidate,
            match=res.match,
            decision=res.decision,
            cover_letter=res.cover_letter,
            audit_history=audit_history,
            outreach_draft=outreach_draft,
            outreach_path=outreach_path,
        )
        filepath = save_application_packet(state, output_dir=output_dir)
        res.output_path = filepath
        generated_paths.append(filepath)
        print(f"     Saved: {filepath}")

    return generated_paths


async def run_batch_workflow(
    directory: str = "sample_jobs",
    resume_path: str = "resume.md",
    auto_generate_approved: bool = False,
    output_dir: str = "applications",
) -> list[BatchJobResult]:
    """Orchestrates the complete batch ingestion, evaluation, and application flow."""
    print("=" * 75)
    print(f"     BATCH JOB AGENT — INGESTING JOBS FROM '{directory}'     ")
    print("=" * 75)

    results, resume_text, candidate = await evaluate_batch_jobs(directory, resume_path)
    if not results:
        print("\nNo job posting files found to evaluate.")
        return []

    render_leaderboard(results)

    if auto_generate_approved:
        approved = [r for r in results if r.decision == "APPROVED"]
        if approved:
            await generate_batch_applications(approved, resume_text, candidate, output_dir)
        else:
            print("\nNo approved jobs (>= 70%) to auto-generate.")
        return results

    # Interactive Action Menu
    print("\nBatch Actions:")
    print("  [1] Auto-generate applications for all APPROVED jobs (Score >= 70%)")
    print("  [2] Select specific job numbers to generate (e.g. '1, 2')")
    print("  [3] Exit without generating")

    choice = input("\nEnter choice (1/2/3, default: 1): ").strip()

    if choice == "2":
        selection = input("Enter job rank numbers separated by commas (e.g. 1, 3): ").strip()
        selected_indices = []
        for s in selection.split(","):
            s_clean = s.strip()
            if s_clean.isdigit():
                idx = int(s_clean) - 1
                if 0 <= idx < len(results):
                    selected_indices.append(idx)
        selected = [results[i] for i in selected_indices]
        if selected:
            await generate_batch_applications(selected, resume_text, candidate, output_dir)
        else:
            print("No valid ranks selected. Exiting.")
    elif choice in ("", "1"):
        approved = [r for r in results if r.decision == "APPROVED"]
        if approved:
            await generate_batch_applications(approved, resume_text, candidate, output_dir)
        else:
            print("\nNo approved jobs (>= 70%) found to generate.")
    else:
        print("\nExiting without generating application packets.")

    return results


if __name__ == "__main__":
    import sys

    target_dir = sys.argv[1] if len(sys.argv) > 1 else "sample_jobs"
    asyncio.run(run_batch_workflow(directory=target_dir))


