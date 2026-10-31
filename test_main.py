import unittest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from extract import JobPosting
from main import app


class TestMainAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("main.async_extract_job", new_callable=AsyncMock)
    def test_extract_endpoint(self, mock_extract):
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


if __name__ == "__main__":
    unittest.main()
