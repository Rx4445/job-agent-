from dataclasses import dataclass
from extract import JobPosting
from matcher import match_job_and_resume
from resume import Resume


@dataclass
class AgentTestCase:
    name: str
    job: JobPosting
    candidate: Resume
    expected_gate: str  # "AUTO_APPROVE", "REVIEW", or "WARN"
    expected_min_score: float
    expected_missing: list[str]


def classify_gate(score: float) -> str:
    """Categorizes the decision gate branch based on match percentage."""
    if score >= 70.0:
        return "AUTO_APPROVE"
    elif score >= 50.0:
        return "REVIEW"
    else:
        return "WARN"


# Evaluation Test Bank
CASES: list[AgentTestCase] = [
    # Case 1: High Fit (All skills match -> Auto-Approved)
    AgentTestCase(
        name="High Fit AI Systems Engineer",
        job=JobPosting(
            title="Junior AI Systems Engineer",
            company="Nexus AI",
            skills=["Python", "Vector DBs", "RAG", "Docker"],
        ),
        candidate=Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "Vector DBs", "RAG", "Docker"],
        ),
        expected_gate="AUTO_APPROVE",
        expected_min_score=70.0,
        expected_missing=[],
    ),
    # Case 2: Moderate Fit (Requires Operator Review)
    AgentTestCase(
        name="Moderate Fit (Operator Review Required)",
        job=JobPosting(
            title="Junior AI Systems Engineer",
            company="Nexus AI 2",
            skills=["Python", "FastAPI", "Docker", "AWS"],
        ),
        candidate=Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="Graphic Designer",
            skills=["Python", "FastAPI"],
        ),
        expected_gate="REVIEW",
        expected_min_score=50.0,
        expected_missing=["Docker", "AWS"],
    ),
    # Case 3: Severe Mismatch (Warn / Abort)
    AgentTestCase(
        name="Severe Mismatch Graphic Designer (Warn / Low Fit)",
        job=JobPosting(
            title="Junior AI Systems Engineer",
            company="Nexus AI 3",
            skills=["Python", "Pytorch", "CUDA", "C++"],
        ),
        candidate=Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="Graphic Designer",
            skills=["Photoshop", "Illustrator", "Figma"],
        ),
        expected_gate="WARN",
        expected_min_score=0.0,
        expected_missing=["Python", "Pytorch", "CUDA", "C++"],
    ),
    # Case 4: Field Pivot with High Technical Skills
    AgentTestCase(
        name="Field Pivot with High Technical Overlap",
        job=JobPosting(
            title="Junior AI Systems Engineer",
            company="Nexus AI",
            skills=["Python", "Vector DBs", "RAG", "SQL"],
        ),
        candidate=Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "Vector DBs", "RAG"],
        ),
        expected_gate="AUTO_APPROVE",
        expected_min_score=70.0,
        expected_missing=["SQL"],
    ),
    # Case 5: Single Critical Missing Requirement
    AgentTestCase(
        name="MLOps Engineer with Single Critical Gap (Kubernetes)",
        job=JobPosting(
            title="MLOps Engineer",
            company="Nexus AI",
            skills=["Python", "Docker", "Kubernetes", "Terraform"],
        ),
        candidate=Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "Docker", "Terraform"],
        ),
        expected_gate="AUTO_APPROVE",
        expected_min_score=70.0,
        expected_missing=["Kubernetes"],
    ),

   
]


def run_agent_eval():
    print("=" * 75)
    print("           AGENT DECISION & SAFETY BENCHMARK (STAGE 5)           ")
    print("=" * 75)

    passed_gates = 0
    passed_gaps = 0
    total = len(CASES)

    for i, test in enumerate(CASES, 1):
        # 1. Evaluate deterministic matching
        result = match_job_and_resume(test.job, test.candidate)
        actual_gate = classify_gate(result.match_score)

        # 2. Check Decision Gate accuracy
        gate_ok = (actual_gate == test.expected_gate) and (result.match_score >= test.expected_min_score)

        # 3. Check Gap Recall (are all expected missing skills identified?)
        actual_missing_lower = [m.lower() for m in result.missing_skills]
        expected_missing_lower = [e.lower() for e in test.expected_missing]
        gaps_ok = all(exp in actual_missing_lower for exp in expected_missing_lower)

        if gate_ok:
            passed_gates += 1
        if gaps_ok:
            passed_gaps += 1

        status = "PASS" if (gate_ok and gaps_ok) else "FAIL"
        print(f"\n[Case {i}/{total}] {test.name} -> {status}")
        print(f"  Score: {result.match_score}% (Min Expected: {test.expected_min_score}%)")
        print(f"  Gate:  {actual_gate} (Expected: {test.expected_gate})")
        print(f"  Gaps:  {result.missing_skills} (Expected: {test.expected_missing})")

    print("\n" + "=" * 75)
    gate_acc = (passed_gates / total) * 100 if total else 0
    gap_acc = (passed_gaps / total) * 100 if total else 0
    print(f"Decision Gate Accuracy: {passed_gates}/{total} ({gate_acc:.1f}%)")
    print(f"Skill Gap Recall:       {passed_gaps}/{total} ({gap_acc:.1f}%)")
    print("=" * 75)


if __name__ == "__main__":
    run_agent_eval()
