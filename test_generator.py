import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from extract import JobPosting
from matcher import MatchResult
from generator import async_generate_cover_letter, build_cover_letter_prompt


class TestCoverLetterGenerator(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.job = JobPosting(
            title="AI Systems Engineer",
            company="Anthropic Labs",
            skills=["Python", "FastAPI", "Vector DBs", "Kubernetes"],
        )
        self.match = MatchResult(
            field_match=True,
            match_score=75.0,
            matching_skills=["Python", "FastAPI", "Vector DBs"],
            missing_skills=["Kubernetes"],
            is_recommended=True,
        )
        self.resume_text = (
            "Aarya Pradhan. Built RAG pipeline using Python, FastAPI, and Chroma/FAISS across 10k docs with <180ms latency."
        )

    def test_build_cover_letter_prompt(self):
        prompt = build_cover_letter_prompt(self.job, self.match, self.resume_text)
        self.assertIn("AI Systems Engineer", prompt)
        self.assertIn("Anthropic Labs", prompt)
        self.assertIn("Python, FastAPI, Vector DBs", prompt)
        self.assertIn("Kubernetes", prompt)
        self.assertIn("10k docs", prompt)
        self.assertIn("STRICT GROUNDING", prompt)

    @patch("generator.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_generate_cover_letter_success(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = "Dear Anthropic Team, I built a RAG system with sub-180ms latency..."
        mock_generate.return_value = mock_response

        letter = await async_generate_cover_letter(self.job, self.match, self.resume_text)

        self.assertEqual(letter, "Dear Anthropic Team, I built a RAG system with sub-180ms latency...")
        self.assertEqual(mock_generate.call_count, 1)

    @patch("generator.asyncio.sleep", new_callable=AsyncMock)
    @patch("generator.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_retry_on_503_then_succeed(self, mock_generate, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = "Generated cover letter after retry."
        mock_generate.side_effect = [Exception("503 Service Unavailable"), mock_response]

        letter = await async_generate_cover_letter(self.job, self.match, self.resume_text)

        self.assertEqual(letter, "Generated cover letter after retry.")
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_awaited_once_with(1)

    @patch("generator.asyncio.sleep", new_callable=AsyncMock)
    @patch("generator.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_fail_fast_on_429(self, mock_generate, mock_sleep):
        mock_generate.side_effect = Exception("429 Resource Exhausted")

        with self.assertRaises(Exception):
            await async_generate_cover_letter(self.job, self.match, self.resume_text)

        self.assertEqual(mock_generate.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("generator.asyncio.sleep", new_callable=AsyncMock)
    @patch("generator.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_exhaustion_on_persistent_503(self, mock_generate, mock_sleep):
        mock_generate.side_effect = [
            Exception("503 Server Error"),
            Exception("503 Server Error"),
            Exception("503 Server Error"),
        ]

        with self.assertRaises(Exception) as context:
            await async_generate_cover_letter(self.job, self.match, self.resume_text, max_retries=3)

        self.assertIn("503 Server Error", str(context.exception))
        self.assertEqual(mock_generate.call_count, 3)
        self.assertEqual(mock_sleep.await_count, 2)


if __name__ == "__main__":
    unittest.main()
