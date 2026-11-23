import asyncio
import html
import re
import sys
import httpx

from agent import load_resume_text
from batch import BatchJobResult, classify_batch_decision, generate_batch_applications, render_leaderboard
from db import (
    compute_resume_hash,
    get_candidate_profile,
    get_existing_job,
    init_db,
    save_candidate_profile,
    save_job,
)
from extract import JobPosting, async_extract_job
from matcher import match_job_and_resume
from resume import Resume, async_extract_resume


def clean_html_content(raw_html: str) -> str:
    """Converts raw job posting HTML from Greenhouse/Lever into clean, readable text."""
    if not raw_html:
        return ""

    text = raw_html

    # 1. Convert bullet points <li> to Markdown list items
    text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.IGNORECASE)

    # 2. Convert block boundaries to newlines
    text = re.sub(r"<(?:/p|br\s*/?|/div|/tr|/h[1-6])>", "\n", text, flags=re.IGNORECASE)

    # 3. Strip all remaining HTML tags (<span ...>, <strong>, etc.)
    text = re.sub(r"<[^>]+>", "", text)

    # 4. Unescape HTML entities (&amp; -> &, &nbsp; -> ' ', &lt; -> <)
    text = html.unescape(text)

    # 5. Clean up excessive whitespace and blank lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    return text.strip()


async def fetch_greenhouse_jobs(
    company_slug: str,
    timeout: float = 15.0,
) -> list[dict]:
    """Fetches all live open jobs for a company from Greenhouse's public API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs?content=true"

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to Greenhouse for '{company_slug}': {e}")

        if response.status_code == 404:
            raise ValueError(f"Company board '{company_slug}' not found on Greenhouse.")

        if response.status_code != 200:
            raise RuntimeError(
                f"Greenhouse API returned HTTP {response.status_code} for '{company_slug}'."
            )

        data = response.json()
        raw_jobs = data.get("jobs", [])

        parsed_jobs = []
        for j in raw_jobs:
            job_id = str(j.get("id", ""))
            title = j.get("title", "").strip()
            location = j.get("location", {}).get("name", "Remote / Not Specified").strip()
            raw_content = j.get("content", "")
            clean_text = clean_html_content(raw_content)

            parsed_jobs.append(
                {
                    "id": job_id,
                    "title": title,
                    "company": company_slug.capitalize(),
                    "location": location,
                    "raw_content": clean_text,
                    "url": j.get("absolute_url", ""),
                }
            )

        return parsed_jobs


async def fetch_lever_jobs(
    company_slug: str,
    timeout: float = 15.0,
) -> list[dict]:
    """Fetches all live open jobs for a company from Lever's public API."""
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(url)
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to Lever for '{company_slug}': {e}")

        if response.status_code == 404:
            raise ValueError(f"Company board '{company_slug}' not found on Lever.")

        if response.status_code != 200:
            raise RuntimeError(
                f"Lever API returned HTTP {response.status_code} for '{company_slug}'."
            )

        raw_jobs = response.json()
        if not isinstance(raw_jobs, list):
            error_msg = raw_jobs.get("error", f"Unexpected response from Lever for '{company_slug}'")
            raise ValueError(f"Lever error for '{company_slug}': {error_msg}")

        parsed_jobs = []
        for j in raw_jobs:
            job_id = str(j.get("id", ""))
            title = j.get("text", "").strip()
            categories = j.get("categories", {}) or {}
            location = categories.get("location", "Remote / Not Specified").strip()

            parts = []
            if j.get("descriptionPlain"):
                parts.append(j["descriptionPlain"].strip())

            for item in j.get("lists", []) or []:
                header = item.get("text", "").strip()
                content = clean_html_content(item.get("content", ""))
                if header and content:
                    parts.append(f"{header}:\n{content}")
                elif content:
                    parts.append(content)

            if j.get("additionalPlain"):
                parts.append(j["additionalPlain"].strip())

            full_text = "\n\n".join(parts) if parts else clean_html_content(j.get("description", ""))

            parsed_jobs.append(
                {
                    "id": job_id,
                    "title": title,
                    "company": company_slug.capitalize(),
                    "location": location,
                    "raw_content": full_text,
                    "url": j.get("hostedUrl", ""),
                }
            )

        return parsed_jobs


async def fetch_live_jobs(
    company_slug: str,
    platform: str = "auto",
    timeout: float = 15.0,
) -> tuple[list[dict], str]:
    """Unified ATS router: fetches jobs from Greenhouse, Lever, or auto-detects."""
    platform_clean = platform.lower().strip()

    if platform_clean == "greenhouse":
        jobs = await fetch_greenhouse_jobs(company_slug, timeout=timeout)
        return jobs, "greenhouse"

    if platform_clean == "lever":
        jobs = await fetch_lever_jobs(company_slug, timeout=timeout)
        return jobs, "lever"

    if platform_clean == "auto":
        # 1. Probe Greenhouse first
        try:
            jobs = await fetch_greenhouse_jobs(company_slug, timeout=timeout)
            return jobs, "greenhouse"
        except (ValueError, RuntimeError):
            pass

        # 2. Fallback to Lever
        try:
            jobs = await fetch_lever_jobs(company_slug, timeout=timeout)
            return jobs, "lever"
        except (ValueError, RuntimeError):
            pass

        raise ValueError(
            f"Company board '{company_slug}' not found on either Greenhouse or Lever."
        )

    raise ValueError(f"Unsupported ATS platform '{platform}'. Supported: 'greenhouse', 'lever', 'auto'.")


def filter_relevant_jobs(
    jobs: list[dict],
    keywords: list[str] = ["ai", "engineer", "machine learning", "backend", "software", "python"],
) -> list[dict]:
    """Filters a list of jobs by matching keywords against the role title."""
    if not keywords:
        return jobs

    lower_keywords = [kw.lower() for kw in keywords]
    relevant = []

    for job in jobs:
        title_lower = job.get("title", "").lower()
        if any(kw in title_lower for kw in lower_keywords):
            relevant.append(job)

    return relevant


async def ingest_live_board_and_rank(
    company_slug: str,
    platform: str = "auto",
    limit: int = 5,
    resume_path: str = "resume.md",
    auto_generate_approved: bool = False,
    output_dir: str = "applications",
) -> list[BatchJobResult]:
    """Fetches real jobs from Greenhouse/Lever, filters relevant engineering roles, scores and ranks them."""
    init_db()
    print("=" * 80)
    print(f"      LIVE BOARD INGESTION: '{company_slug.upper()}' (PLATFORM: {platform.upper()})      ")
    print("=" * 80)

    # 1. Fetch & Filter Live Postings via Unified Router
    print(f"\n[1/4] Querying {platform.capitalize()} ATS for '{company_slug}' open positions...")
    all_jobs, detected_platform = await fetch_live_jobs(company_slug, platform=platform)
    print(f"      Connected via: {detected_platform.upper()} (Found {len(all_jobs)} total open positions).")

    relevant_jobs = filter_relevant_jobs(all_jobs)
    print(f"      Filtered to {len(relevant_jobs)} relevant engineering/technical roles.")

    if not relevant_jobs:
        print("\nNo matching technical jobs found for this company.")
        return []

    target_jobs = relevant_jobs[:limit]
    print(f"      Evaluating top {len(target_jobs)} roles (limit={limit})...\n")

    # 2. Ingest Candidate Profile (from 0ms SQLite Cache)
    resume_text = load_resume_text(resume_path)
    resume_hash = compute_resume_hash(resume_text)
    cached_profile = get_candidate_profile(resume_hash)

    if cached_profile:
        candidate = Resume(
            name=cached_profile["name"],
            experience_years=cached_profile["experience_years"],
            field=cached_profile["field"],
            skills=cached_profile["skills"],
        )
        print(f"[2/4] Loaded candidate profile from cache (0ms): '{candidate.name}'")
    else:
        print("[2/4] Extracting candidate profile via Gemini...")
        candidate = await async_extract_resume(resume_text)
        save_candidate_profile(
            resume_hash, candidate.name, candidate.experience_years, candidate.field, candidate.skills
        )

    # 3. Process Each Job (Deduplicated against SQLite)
    print(f"\n[3/4] Processing and scoring {len(target_jobs)} jobs against resume...")
    results: list[BatchJobResult] = []

    for i, j in enumerate(target_jobs, 1):
        title = j["title"]
        company = j["company"]
        existing = get_existing_job(title, company)

        if existing:
            job = JobPosting(title=existing["title"], company=existing["company"], skills=existing["skills"])
            print(f"  [{i}/{len(target_jobs)}] Loaded '{title}' from SQLite cache (0ms).")
        else:
            print(f"  [{i}/{len(target_jobs)}] Extracting requirements for '{title}' via Gemini...")
            job = await async_extract_job(j["raw_content"])
            # Ensure title & company from Greenhouse are preserved if model generalizes
            if not job.title or job.title.lower() == "not specified":
                job.title = title
            if not job.company or job.company.lower() == "not specified":
                job.company = company
            save_job(job.title, job.company, job.skills)

        match = match_job_and_resume(job, candidate)
        decision = classify_batch_decision(match.match_score)

        results.append(
            BatchJobResult(
                source_file=j.get("url", f"greenhouse:{j['id']}"),
                job=job,
                match=match,
                decision=decision,
            )
        )

    # 4. Rank by Match Score Descending & Render
    results.sort(key=lambda r: r.match.match_score, reverse=True)
    render_leaderboard(results)

    # 5. Application Dispatch Gate
    if auto_generate_approved:
        approved = [r for r in results if r.decision == "APPROVED"]
        if approved:
            await generate_batch_applications(approved, resume_text, candidate, output_dir)
        return results

    print("\nBatch Actions:")
    print("  [1] Auto-generate applications for all APPROVED jobs (Score >= 70%)")
    print("  [2] Select specific job rank numbers (e.g. '1, 2')")
    print("  [3] Exit without generating")

    choice = input("\nEnter choice (1/2/3, default: 1): ").strip()

    if choice == "2":
        selection = input("Enter job rank numbers separated by commas (e.g. 1, 3): ").strip()
        selected = []
        for s in selection.split(","):
            s_clean = s.strip()
            if s_clean.isdigit():
                idx = int(s_clean) - 1
                if 0 <= idx < len(results):
                    selected.append(results[idx])
        if selected:
            await generate_batch_applications(selected, resume_text, candidate, output_dir)
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
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Platform Live Job Board Ingestion Agent (Greenhouse & Lever)")
    parser.add_argument("--company", "-c", required=True, help="Company slug (e.g. cloudflare, observeai, palantir)")
    parser.add_argument("--platform", "-p", default="auto", choices=["auto", "greenhouse", "lever"], help="ATS platform (default: auto)")
    parser.add_argument("--limit", "-l", type=int, default=3, help="Max number of jobs to evaluate (default: 3)")
    parser.add_argument("--auto-generate", action="store_true", help="Auto-generate packets for approved jobs")
    args = parser.parse_args()

    asyncio.run(
        ingest_live_board_and_rank(
            company_slug=args.company,
            platform=args.platform,
            limit=args.limit,
            auto_generate_approved=args.auto_generate,
        )
    )

