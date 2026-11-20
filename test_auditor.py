import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from auditor import (
    AuditCritique,
    async_audit_cover_letter,
    async_generate_audited_cover_letter,
    build_auditor_prompt,
    build_revision_prompt,
)
from extract import JobPosting
from matcher import MatchResult


class TestAuditor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.job = JobPosting(
            title="AI Systems Engineer",
            company="Nexus AI",
            skills=["Python", "RAG", "Chroma", "Docker"],
        )
        self.match = MatchResult(
            field_match=True,
            match_score=75.0,
            matching_skills=["Python", "RAG", "Chroma"],
            missing_skills=["Docker"],
            is_recommended=True,
        )
        self.resume_text = (
            "Aarya Pradhan. Built RAG pipeline using Python and Chroma across 10k documents."
        )
        self.cover_letter = "Hi Nexus AI Team, I built a production RAG system with Chroma..."

    def test_build_auditor_prompt(self):
        prompt = build_auditor_prompt(self.cover_letter, self.resume_text, self.job)
        self.assertIn("Nexus AI", prompt)
        self.assertIn("AI Systems Engineer", prompt)
        self.assertIn("Python, RAG, Chroma, Docker", prompt)
        self.assertIn("Aarya Pradhan", prompt)
        self.assertIn("production RAG system", prompt)
        self.assertIn("ZERO TOLERANCE FOR HALLUCINATIONS", prompt)

    def test_build_revision_prompt(self):
        critique = AuditCritique(
            score=4,
            is_grounded=False,
            hallucinated_claims=["Managed 20 Kubernetes nodes"],
            tone_rating="too_robotic",
            critique_notes="Remove Kubernetes. Sound more human.",
        )
        rev_prompt = build_revision_prompt(
            self.cover_letter, critique, self.job, self.match, self.resume_text
        )
        self.assertIn("Managed 20 Kubernetes nodes", rev_prompt)
        self.assertIn("Score: 4/10", rev_prompt)
        self.assertIn("Remove Kubernetes. Sound more human.", rev_prompt)
        self.assertIn("PURGE", rev_prompt)

    @patch("auditor.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_audit_cover_letter_success(self, mock_generate):
        mock_critique = AuditCritique(
            score=9,
            is_grounded=True,
            hallucinated_claims=[],
            tone_rating="authentic",
            critique_notes="Excellent alignment with resume metrics.",
        )
        mock_response = MagicMock()
        mock_response.parsed = mock_critique
        mock_generate.return_value = mock_response

        critique = await async_audit_cover_letter(self.cover_letter, self.resume_text, self.job)

        self.assertEqual(critique.score, 9)
        self.assertTrue(critique.is_grounded)
        self.assertEqual(critique.tone_rating, "authentic")
        self.assertEqual(len(critique.hallucinated_claims), 0)

    @patch("auditor.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_audit_cover_letter_catches_hallucination(self, mock_generate):
        mock_critique = AuditCritique(
            score=3,
            is_grounded=False,
            hallucinated_claims=["Led a team of 15 engineers", "Architected AWS SageMaker"],
            tone_rating="too_aggressive",
            critique_notes="Candidate invented leadership and AWS experience not in resume.",
        )
        mock_response = MagicMock()
        mock_response.parsed = mock_critique
        mock_generate.return_value = mock_response

        critique = await async_audit_cover_letter(self.cover_letter, self.resume_text, self.job)

        self.assertEqual(critique.score, 3)
        self.assertFalse(critique.is_grounded)
        self.assertIn("Led a team of 15 engineers", critique.hallucinated_claims)

    @patch("auditor.asyncio.sleep", new_callable=AsyncMock)
    @patch("auditor.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_audit_retry_on_503(self, mock_generate, mock_sleep):
        mock_critique = AuditCritique(
            score=8,
            is_grounded=True,
            hallucinated_claims=[],
            tone_rating="authentic",
            critique_notes="Good.",
        )
        success_response = MagicMock()
        success_response.parsed = mock_critique

        mock_generate.side_effect = [
            RuntimeError("503 UNAVAILABLE: Model overloaded"),
            success_response,
        ]

        critique = await async_audit_cover_letter(self.cover_letter, self.resume_text, self.job)

        self.assertEqual(critique.score, 8)
        self.assertEqual(mock_generate.call_count, 2)
        mock_sleep.assert_called_once_with(1)

    @patch("auditor.async_audit_cover_letter", new_callable=AsyncMock)
    @patch("auditor.async_generate_cover_letter", new_callable=AsyncMock)
    async def test_reflection_loop_approves_on_first_try(self, mock_draft, mock_audit):
        mock_draft.return_value = "Initial perfect cover letter."
        mock_audit.return_value = AuditCritique(
            score=9,
            is_grounded=True,
            hallucinated_claims=[],
            tone_rating="authentic",
            critique_notes="Perfect draft.",
        )

        letter, history = await async_generate_audited_cover_letter(
            self.job, self.match, self.resume_text, max_refinements=2, pass_score=8
        )

        self.assertEqual(letter, "Initial perfect cover letter.")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].score, 9)
        mock_draft.assert_called_once()
        mock_audit.assert_called_once()

    @patch("auditor.client.aio.models.generate_content", new_callable=AsyncMock)
    @patch("auditor.async_audit_cover_letter", new_callable=AsyncMock)
    @patch("auditor.async_generate_cover_letter", new_callable=AsyncMock)
    async def test_reflection_loop_refines_flawed_draft(self, mock_draft, mock_audit, mock_gen_rev):
        # 1. Drafter writes draft with an ungrounded claim
        mock_draft.return_value = "Draft 1 with hallucination."

        # 2. Auditor fails round 1, then approves round 2
        critique_round_1 = AuditCritique(
            score=5,
            is_grounded=False,
            hallucinated_claims=["Kubernetes cluster management"],
            tone_rating="too_robotic",
            critique_notes="Remove Kubernetes. Cite Docker.",
        )
        critique_round_2 = AuditCritique(
            score=9,
            is_grounded=True,
            hallucinated_claims=[],
            tone_rating="authentic",
            critique_notes="Excellent revision. Fully grounded.",
        )
        mock_audit.side_effect = [critique_round_1, critique_round_2]

        # 3. Drafter revises
        mock_rev_response = MagicMock()
        mock_rev_response.text = "Draft 2: Cleaned, only Docker cited."
        mock_gen_rev.return_value = mock_rev_response

        letter, history = await async_generate_audited_cover_letter(
            self.job, self.match, self.resume_text, max_refinements=2, pass_score=8
        )

        self.assertEqual(letter, "Draft 2: Cleaned, only Docker cited.")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].score, 5)
        self.assertFalse(history[0].is_grounded)
        self.assertEqual(history[1].score, 9)
        self.assertTrue(history[1].is_grounded)
        mock_gen_rev.assert_called_once()

    @patch("auditor.client.aio.models.generate_content", new_callable=AsyncMock)
    @patch("auditor.async_audit_cover_letter", new_callable=AsyncMock)
    @patch("auditor.async_generate_cover_letter", new_callable=AsyncMock)
    async def test_reflection_loop_respects_max_refinements(self, mock_draft, mock_audit, mock_gen_rev):
        mock_draft.return_value = "Persistent stubborn draft."
        stubborn_critique = AuditCritique(
            score=4,
            is_grounded=False,
            hallucinated_claims=["Persistent hallucination"],
            tone_rating="too_aggressive",
            critique_notes="Still ungrounded.",
        )
        mock_audit.return_value = stubborn_critique

        mock_rev_response = MagicMock()
        mock_rev_response.text = "Persistent stubborn draft attempt 2."
        mock_gen_rev.return_value = mock_rev_response

        letter, history = await async_generate_audited_cover_letter(
            self.job, self.match, self.resume_text, max_refinements=2, pass_score=8
        )

        # 1 initial audit + 2 refinement audits = 3 total audits
        self.assertEqual(len(history), 3)
        self.assertEqual(mock_audit.call_count, 3)
        self.assertEqual(mock_gen_rev.call_count, 2)


if __name__ == "__main__":
    unittest.main()
