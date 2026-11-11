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


if __name__ == "__main__":
    unittest.main()
