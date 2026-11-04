import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from extract import JobPosting, async_extract_job


class TestAsyncExtractJob(unittest.IsolatedAsyncioTestCase):
    @patch("extract.asyncio.sleep", new_callable=AsyncMock)
    @patch("extract.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_retry_on_failure_then_succeed(self, mock_generate, mock_sleep):
        mock_success = MagicMock()
        mock_success.parsed = JobPosting(
            title="Software Engineer",
            company="Acme Corp",
            skills=["Python"],
        )
        mock_generate.side_effect = [Exception("503 High Demand"), mock_success]

        result = await async_extract_job("Dummy job posting text")

        self.assertEqual(result.title, "Software Engineer")
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_awaited_once_with(1)

    @patch("extract.asyncio.sleep", new_callable=AsyncMock)
    @patch("extract.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_three_failures_raises_error_after_three_attempts(self, mock_generate, mock_sleep):
        mock_generate.side_effect = [
            Exception("503 Server Error"),
            Exception("503 Server Error"),
            Exception("503 Server Error"),
        ]

        with self.assertRaises(Exception):
            await async_extract_job("Dummy job posting text")

        self.assertEqual(mock_generate.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("extract.asyncio.sleep", new_callable=AsyncMock)
    @patch("extract.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_stop_retrying_on_429_quota_error(self, mock_generate, mock_sleep):
        mock_generate.side_effect = Exception("429 Resource has been exhausted")

        with self.assertRaises(Exception):
            await async_extract_job("Dummy job posting text")

        self.assertEqual(mock_generate.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("extract.asyncio.sleep", new_callable=AsyncMock)
    @patch("extract.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_retry_on_503_error(self, mock_generate, mock_sleep):
        mock_success = MagicMock()
        mock_success.parsed = JobPosting(
            title="Software Engineer",
            company="Acme Corp",
            skills=["Python"],
        )
        mock_generate.side_effect = [Exception("503 Service Unavailable"), mock_success]

        result = await async_extract_job("Dummy job posting text")

        self.assertEqual(result.title, "Software Engineer")
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_awaited_once_with(1)


if __name__ == "__main__":
    unittest.main()
