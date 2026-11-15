import unittest
from extract import JobPosting
from matcher import match_job_and_resume
from resume import Resume


class TestMatcher(unittest.TestCase):
    def setUp(self):
        self.candidate = Resume(
            name="Jane Doe",
            experience_years=4,
            field="Backend Engineer",
            skills=["Python", "FastAPI", "SQL", "Git"],
        )

    def test_full_match(self):
        job = JobPosting(
            title="Backend Developer",
            company="Acme Corp",
            skills=["Python", "SQL"],
        )
        result = match_job_and_resume(job, self.candidate)

        self.assertTrue(result.field_match)
        self.assertEqual(result.match_score, 100.0)
        self.assertEqual(result.matching_skills, ["Python", "SQL"])
        self.assertEqual(result.missing_skills, [])
        self.assertTrue(result.is_recommended)

    def test_partial_match_and_gap_identification(self):
        job = JobPosting(
            title="Senior Backend Engineer",
            company="Acme Corp",
            skills=["Python", "FastAPI", "SQL", "Docker"],
        )
        result = match_job_and_resume(job, self.candidate)

        self.assertTrue(result.field_match)
        self.assertEqual(result.match_score, 75.0)
        self.assertEqual(result.matching_skills, ["Python", "FastAPI", "SQL"])
        self.assertEqual(result.missing_skills, ["Docker"])
        self.assertTrue(result.is_recommended)

    def test_field_mismatch_not_recommended(self):
        job = JobPosting(
            title="Graphic Designer",
            company="DesignStudio",
            skills=["Photoshop", "Illustrator"],
        )
        result = match_job_and_resume(job, self.candidate)

        self.assertFalse(result.field_match)
        self.assertEqual(result.match_score, 0.0)
        self.assertFalse(result.is_recommended)

    def test_case_insensitivity(self):
        job = JobPosting(
            title="backend engineer",
            company="Tech Corp",
            skills=["PYTHON", "fastapi"],
        )
        result = match_job_and_resume(job, self.candidate)

        self.assertEqual(result.match_score, 100.0)
        self.assertIn("PYTHON", result.matching_skills)
        self.assertIn("fastapi", result.matching_skills)

    def test_job_with_no_skills_required(self):
        job = JobPosting(
            title="Backend Associate",
            company="Startup Inc",
            skills=[],
        )
        result = match_job_and_resume(job, self.candidate)

        self.assertEqual(result.match_score, 100.0)
        self.assertEqual(result.matching_skills, [])
        self.assertEqual(result.missing_skills, [])

    def test_substring_skill_alignment(self):
        job = JobPosting(
            title="Backend Associate",
            company="Startup Inc",
            skills=["Python programming", "Docker or containerization"],
        )
        cand = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "Docker"],
        )
        result = match_job_and_resume(job, cand)
        self.assertEqual(result.match_score, 100.0)
        self.assertEqual(len(result.matching_skills), 2)
        self.assertEqual(result.missing_skills, [])

    def test_token_overlap_skill_alignment(self):
        job = JobPosting(
            title="AI Engineer",
            company="Nexus AI",
            skills=["RESTful API design", "Vector DBs (Chroma or FAISS)"],
        )
        cand = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["RESTful APIs", "Vector DBs (Chroma, FAISS)"],
        )
        result = match_job_and_resume(job, cand)
        self.assertEqual(result.match_score, 100.0)
        self.assertEqual(len(result.matching_skills), 2)



if __name__ == "__main__":
    unittest.main()
