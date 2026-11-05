import asyncio
import json

from extract import async_extract_job


def normalize(text):
    return text.strip().lower()


def normalize_company(text):
    t = text.strip().lower()
    return "" if t in ("not specified", "n/a", "none", "unknown") else t


async def run_eval():
    with open("eval_postings.json", encoding="utf-8") as f:
        cases = json.load(f)

    title_hits = 0
    company_hits = 0
    skills_hits = 0

    total = len(cases)
    for i, case in enumerate(cases, start=1):
        try:
            result = await async_extract_job(case["posting"], max_retries=5)
        except Exception as e:
            print(f"Case {i}: FAILED with error: {e}")
            if i < total:
                print(f"Waiting 13s to respect 5 RPM limit before Case {i + 1}...")
                await asyncio.sleep(13)
            continue

        expected = case["expected"]

        title_ok = normalize(result.title) == normalize(expected["title"])
        company_ok = normalize_company(result.company) == normalize_company(expected["company"])
        skills_ok = {normalize(s) for s in result.skills} == {
            normalize(s) for s in expected["skills"]
        }

        title_hits += title_ok
        company_hits += company_ok
        skills_hits += skills_ok

        print(f"Case {i}: title={title_ok} company={company_ok} skills={skills_ok}")
        if not (title_ok and company_ok and skills_ok):
            print("   got:     ", result)
            print("   expected:", expected)

        if i < total:
            print(f"Waiting 13s to respect 5 RPM limit before Case {i + 1}...")
            await asyncio.sleep(13)

    print()
    print(f"Title:   {title_hits}/{total}")
    print(f"Company: {company_hits}/{total}")
    print(f"Skills:  {skills_hits}/{total}")


if __name__ == "__main__":
    asyncio.run(run_eval())
