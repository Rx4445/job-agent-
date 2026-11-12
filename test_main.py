import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from extract import JobPosting
from resume import Resume
from main import app


class TestMainAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("main.async_extract_job", new_callable=AsyncMock)
    @patch("main.save_job")
    def test_extract_endpoint(self, mock_save, mock_extract):
        mock_extract.return_value = JobPosting(
            title="Backend Dev",
            company="Acme Corp",
            skills=["Python", "FastAPI"],
        )

        response = self.client.post(
            "/extract",
            json={"posting": "Junior Backend Engineer at Acme Corp."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], "Backend Dev")
        self.assertEqual(response.json()["company"], "Acme Corp")
        self.assertEqual(response.json()["skills"], ["Python", "FastAPI"])
        mock_save.assert_called_once_with("Backend Dev", "Acme Corp", ["Python", "FastAPI"])

    @patch("main.async_extract_resume", new_callable=AsyncMock)
    @patch("main.async_extract_job", new_callable=AsyncMock)
    @patch("main.save_job")
    def test_match_endpoint(self, mock_save, mock_extract_job, mock_extract_resume):
        mock_extract_job.return_value = JobPosting(
            title="Backend Dev",
            company="Acme Corp",
            skills=["Python", "FastAPI", "SQL"],
        )
        mock_extract_resume.return_value = Resume(
            name="Jane Doe",
            experience_years=3,
            field="Backend Engineer",
            skills=["Python", "FastAPI"],
        )

        response = self.client.post(
            "/match",
            json={
                "posting": "Junior Backend Engineer at Acme Corp...",
                "resume": "Jane Doe, Backend Engineer with 3 years...",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["field_match"])
        self.assertEqual(data["matching_skills"], ["Python", "FastAPI"])
        self.assertEqual(data["missing_skills"], ["SQL"])
        self.assertEqual(data["match_score"], 66.7)
        self.assertTrue(data["is_recommended"])
        mock_save.assert_called_once_with("Backend Dev", "Acme Corp", ["Python", "FastAPI", "SQL"])

    @patch("main.get_jobs")
    @patch("main.async_extract_resume", new_callable=AsyncMock)
    def test_match_all_endpoint(self, mock_extract_resume, mock_get_jobs):
        mock_extract_resume.return_value = Resume(
            name="Jane Doe",
            experience_years=3,
            field="Backend Engineer",
            skills=["Python", "FastAPI"],
        )
        mock_get_jobs.return_value = [
            {
                "id": 1,
                "title": "Junior Backend Engineer",
                "company": "Company A",
                "skills": ["Python", "FastAPI", "SQL", "Docker"],  # 2 of 4 = 50%
            },
            {
                "id": 2,
                "title": "Backend Python Developer",
                "company": "Company B",
                "skills": ["Python", "FastAPI"],  # 2 of 2 = 100%
            },
            {
                "id": 3,
                "title": "Graphic Designer",
                "company": "Company C",
                "skills": ["Photoshop", "Illustrator"],  # 0 of 2 = 0%
            },
        ]

        response = self.client.post(
            "/match-all",
            json={"resume": "Jane Doe, Backend Engineer with Python and FastAPI..."},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 3)

        # Ranked #1: Company B (100% match)
        self.assertEqual(data[0]["company"], "Company B")
        self.assertEqual(data[0]["match"]["match_score"], 100.0)
        self.assertTrue(data[0]["match"]["is_recommended"])

        # Ranked #2: Company A (50% match)
        self.assertEqual(data[1]["company"], "Company A")
        self.assertEqual(data[1]["match"]["match_score"], 50.0)

        # Ranked #3: Company C (0% match)
        self.assertEqual(data[2]["company"], "Company C")
        self.assertEqual(data[2]["match"]["match_score"], 0.0)
        self.assertFalse(data[2]["match"]["is_recommended"])

    @patch("main.async_generate_cover_letter", new_callable=AsyncMock)
    @patch("main.async_extract_resume", new_callable=AsyncMock)
    @patch("main.async_extract_job", new_callable=AsyncMock)
    @patch("main.save_job")
    def test_cover_letter_with_posting_text(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter
    ):
        mock_extract_job.return_value = JobPosting(
            title="AI Systems Engineer",
            company="Anthropic Labs",
            skills=["Python", "FastAPI", "Vector DBs"],
        )
        mock_extract_resume.return_value = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "FastAPI"],
        )
        mock_generate_letter.return_value = "Dear Anthropic Team, ..."

        response = self.client.post(
            "/cover-letter",
            json={
                "posting": "Looking for an AI Systems Engineer with Python and FastAPI...",
                "resume": "Aarya Pradhan. Built RAG with Python...",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cover_letter"], "Dear Anthropic Team, ...")
        self.assertEqual(data["match"]["matching_skills"], ["Python", "FastAPI"])
        self.assertEqual(data["match"]["missing_skills"], ["Vector DBs"])
        mock_save.assert_called_once()
        mock_generate_letter.assert_called_once()

    @patch("main.async_generate_cover_letter", new_callable=AsyncMock)
    @patch("main.async_extract_resume", new_callable=AsyncMock)
    @patch("main.get_jobs")
    def test_cover_letter_with_job_id(
        self, mock_get_jobs, mock_extract_resume, mock_generate_letter
    ):
        mock_get_jobs.return_value = [
            {
                "id": 42,
                "title": "ML Engineer",
                "company": "DeepMind",
                "skills": ["Python", "PyTorch"],
            }
        ]
        mock_extract_resume.return_value = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="Machine Learning",
            skills=["Python"],
        )
        mock_generate_letter.return_value = "Dear DeepMind, ..."

        response = self.client.post(
            "/cover-letter",
            json={"job_id": 42, "resume": "Aarya Pradhan..."},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cover_letter"], "Dear DeepMind, ...")
        self.assertEqual(data["match"]["matching_skills"], ["Python"])
        self.assertEqual(data["match"]["missing_skills"], ["PyTorch"])

    @patch("main.get_jobs")
    def test_cover_letter_job_id_not_found(self, mock_get_jobs):
        mock_get_jobs.return_value = []
        response = self.client.post(
            "/cover-letter",
            json={"job_id": 999, "resume": "Aarya Pradhan..."},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found in database", response.json()["detail"])

    def test_cover_letter_missing_posting_and_job_id(self):
        response = self.client.post(
            "/cover-letter",
            json={"resume": "Aarya Pradhan..."},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Provide either posting text or a valid job_id", response.json()["detail"])



if __name__ == "__main__":
    unittest.main()
