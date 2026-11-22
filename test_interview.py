import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from extract import JobPosting
from interview import (
    InterviewBattlecard,
    InterviewQuestion,
    STARResponse,
    async_generate_interview_battlecard,
    build_interview_prompt,
    save_interview_battlecard,
)
from matcher import MatchResult


class TestInterviewPrep(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.job = JobPosting(
            title="AI Systems Engineer",
            company="Nexus AI",
            skills=["Python", "RAG", "Chroma", "Kubernetes"],
        )
        self.match = MatchResult(
            field_match=True,
            match_score=75.0,
            matching_skills=["Python", "RAG", "Chroma"],
            missing_skills=["Kubernetes"],
            is_recommended=True,
        )
        self.resume_text = (
            "Aarya Pradhan. Built RAG pipeline using Python and Chroma across 10k documents with <180ms latency."
        )
        self.mock_battlecard = InterviewBattlecard(
            role_title="AI Systems Engineer",
            company="Nexus AI",
            positioning_hook="I am an engineer with hands-on RAG experience bridging technical pipelines with client impact.",
            questions=[
                InterviewQuestion(
                    category="Technical Deep-Dive",
                    question="How did you achieve sub-180ms latency in your RAG system?",
                    interviewer_intent="Testing vector indexing and chunking strategies.",
                    pitfalls_to_avoid="Do not say you used default configurations without optimization.",
                    star_response=STARResponse(
                        situation="Building semantic search across 10,000+ domain documents.",
                        task="Maintain sub-200ms retrieval latencies for production client applications.",
                        action="Engineered custom chunking strategies and deployed Chroma and FAISS vector indices.",
                        result="Achieved sustained retrieval latencies under 180ms.",
                    ),
                    proof_metrics=["10,000+ documents", "<180ms latency"],
                ),
                InterviewQuestion(
                    category="Gap Defense",
                    question="We require Kubernetes in production, but you only list Docker. How will you ramp up?",
                    interviewer_intent="Assessing whether candidate bluffs or understands container orchestration fundamentals.",
                    pitfalls_to_avoid="Do not pretend to have run production K8s clusters.",
                    star_response=STARResponse(
                        situation="Transitioning containerized applications to distributed orchestration.",
                        task="Quickly master Kubernetes manifest design and deployment.",
                        action="Leveraged extensive Docker experience and Linux fundamentals to study container lifecycles.",
                        result="Capable of rapid operational ramp-up within days.",
                    ),
                    proof_metrics=["Docker", "Linux"],
                ),
            ],
        )

    def test_build_interview_prompt(self):
        prompt = build_interview_prompt(self.job, self.match, self.resume_text)
        self.assertIn("Nexus AI", prompt)
        self.assertIn("AI Systems Engineer", prompt)
        self.assertIn("Python, RAG, Chroma", prompt)
        self.assertIn("Kubernetes", prompt)
        self.assertIn("10k documents", prompt)
        self.assertIn("POSITIONING HOOK", prompt)
        self.assertIn("STAR", prompt)

    @patch("interview.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_interview_battlecard_success(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = self.mock_battlecard.model_dump_json()
        mock_generate.return_value = mock_response

        battlecard = await async_generate_interview_battlecard(self.job, self.match, self.resume_text)

        self.assertEqual(battlecard.role_title, "AI Systems Engineer")
        self.assertEqual(battlecard.company, "Nexus AI")
        self.assertEqual(len(battlecard.questions), 2)
        self.assertEqual(battlecard.questions[0].category, "Technical Deep-Dive")
        self.assertEqual(battlecard.questions[0].star_response.result, "Achieved sustained retrieval latencies under 180ms.")

    @patch("interview.asyncio.sleep", new_callable=AsyncMock)
    @patch("interview.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_retry_on_503(self, mock_generate, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = self.mock_battlecard.model_dump_json()

        mock_generate.side_effect = [
            RuntimeError("503 UNAVAILABLE: Model overloaded"),
            mock_response,
        ]

        battlecard = await async_generate_interview_battlecard(self.job, self.match, self.resume_text)

        self.assertEqual(battlecard.company, "Nexus AI")
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_called_once_with(2)

    @patch("interview.asyncio.sleep", new_callable=AsyncMock)
    @patch("interview.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_fail_fast_429(self, mock_generate, mock_sleep):
        mock_generate.side_effect = RuntimeError("429 RESOURCE_EXHAUSTED")

        with self.assertRaises(RuntimeError):
            await async_generate_interview_battlecard(self.job, self.match, self.resume_text)

        mock_generate.assert_called_once()
        mock_sleep.assert_not_called()

    def test_save_interview_battlecard(self):
        temp_dir = tempfile.mkdtemp()
        try:
            filepath = save_interview_battlecard(self.mock_battlecard, output_dir=temp_dir)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Interview Battlecard: AI Systems Engineer at Nexus AI", content)
            self.assertIn("30-Second Positioning Hook", content)
            self.assertIn("How did you achieve sub-180ms latency", content)
            self.assertIn("What the Interviewer Is Really Testing", content)
            self.assertIn("Recommended STAR Answer", content)
            self.assertIn("10,000+ documents", content)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
