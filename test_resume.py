import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from resume import Resume, async_extract_resume


class TestAsyncExtractResume(unittest.IsolatedAsyncioTestCase):
    @patch("resume.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_extract_resume_success(self, mock_generate):
        mock_success = MagicMock()
        mock_success.parsed = Resume(
            name="Jane Doe",
            experience_years=5,
            field="Backend Engineering",
            skills=["Python", "FastAPI", "PostgreSQL"],
        )
        mock_generate.return_value = mock_success

        result = await async_extract_resume("Sample resume text")

        self.assertEqual(result.name, "Jane Doe")
        self.assertEqual(result.experience_years, 5)
        self.assertIn("Python", result.skills)
        self.assertEqual(mock_generate.call_count, 1)

    @patch("resume.asyncio.sleep", new_callable=AsyncMock)
    @patch("resume.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_retry_on_503_then_succeed(self, mock_generate, mock_sleep):
        mock_success = MagicMock()
        mock_success.parsed = Resume(
            name="Jane Doe",
            experience_years=5,
            field="Backend Engineering",
            skills=["Python"],
        )
        mock_generate.side_effect = [Exception("503 High Demand"), mock_success]

        result = await async_extract_resume("Sample resume text")

        self.assertEqual(result.name, "Jane Doe")
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_awaited_once_with(1)

    @patch("resume.asyncio.sleep", new_callable=AsyncMock)
    @patch("resume.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_fail_fast_on_429(self, mock_generate, mock_sleep):
        mock_generate.side_effect = Exception("429 Resource Exhausted")

        with self.assertRaises(Exception):
            await async_extract_resume("Sample resume text")

        self.assertEqual(mock_generate.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
