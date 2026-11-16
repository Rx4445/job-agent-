import os
import tempfile
import unittest

from db import (
    compute_resume_hash,
    get_candidate_profile,
    get_existing_job,
    get_jobs,
    init_db,
    save_candidate_profile,
    save_job,
)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_jobs.db")
        init_db(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_compute_resume_hash_deterministic(self):
        text1 = "Alice. Python, Docker, RAG."
        text2 = "  Alice. Python, Docker, RAG.  \n"
        hash1 = compute_resume_hash(text1)
        hash2 = compute_resume_hash(text2)
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_candidate_profile_cache_miss_returns_none(self):
        result = get_candidate_profile("non_existent_hash", db_path=self.db_path)
        self.assertIsNone(result)

    def test_candidate_profile_save_and_retrieve(self):
        text = "Aarya Pradhan. 2 years exp in AI Engineering. Skills: Python, RAG."
        h = compute_resume_hash(text)
        save_candidate_profile(
            resume_hash=h,
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "RAG"],
            db_path=self.db_path,
        )

        profile = get_candidate_profile(h, db_path=self.db_path)
        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], "Aarya Pradhan")
        self.assertEqual(profile["experience_years"], 2)
        self.assertEqual(profile["field"], "AI Engineering")
        self.assertEqual(profile["skills"], ["Python", "RAG"])

    def test_candidate_profile_replace_on_conflict(self):
        h = "shared_hash_123"
        save_candidate_profile(
            resume_hash=h,
            name="Initial Name",
            experience_years=1,
            field="IT",
            skills=["SQL"],
            db_path=self.db_path,
        )
        save_candidate_profile(
            resume_hash=h,
            name="Updated Name",
            experience_years=2,
            field="AI",
            skills=["Python", "SQL"],
            db_path=self.db_path,
        )

        profile = get_candidate_profile(h, db_path=self.db_path)
        self.assertEqual(profile["name"], "Updated Name")
        self.assertEqual(profile["experience_years"], 2)
        self.assertEqual(profile["skills"], ["Python", "SQL"])

    def test_save_and_get_jobs(self):
        save_job("Software Engineer", "Acme Corp", ["Python", "Django"], db_path=self.db_path)
        jobs = get_jobs(db_path=self.db_path)
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Software Engineer")
        self.assertEqual(jobs[0]["company"], "Acme Corp")
        self.assertEqual(jobs[0]["skills"], ["Python", "Django"])

    def test_get_existing_job(self):
        save_job("AI Systems Engineer", "Nexus AI", ["Python", "RAG"], db_path=self.db_path)
        found = get_existing_job("ai systems engineer", "nexus ai", db_path=self.db_path)
        self.assertIsNotNone(found)
        self.assertEqual(found["title"], "AI Systems Engineer")
        self.assertEqual(found["skills"], ["Python", "RAG"])

        missing = get_existing_job("Frontend Dev", "Nexus AI", db_path=self.db_path)
        self.assertIsNone(missing)


if __name__ == "__main__":
    unittest.main()
