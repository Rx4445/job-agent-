import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from extract import JobPosting
from matcher import MatchResult
from outreach import (
    OutreachDraft,
    async_generate_outreach,
    build_outreach_prompt,
    save_outreach_packet,
)


class TestOutreachAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.job = JobPosting(
            title="AI Solutions Engineer",
            company="Observe.AI",
            skills=["Python", "LLMs", "Client Walkthroughs", "PostgreSQL"],
        )
        self.match = MatchResult(
            field_match=True,
            match_score=80.0,
            matching_skills=["Python", "LLMs", "Client Walkthroughs"],
            missing_skills=["PostgreSQL"],
            is_recommended=True,
        )
        self.resume_text = (
            "Aarya Pradhan. Led 150+ client technical walkthroughs. Engineered 180+ custom SQL migrations at HighRadius."
        )
        self.mock_draft = OutreachDraft(
            company="Observe.AI",
            role="AI Solutions Engineer",
            subject_lines=[
                "Observe.AI AI Solutions role + 150 enterprise walkthroughs",
                "Quick question re: client-facing agent engineering",
                "Bridging agent architectures with enterprise clients",
            ],
            hook="Saw Observe.AI is expanding client-facing agent implementations for enterprise workflows.",
            proof_points=[
                "Led 150+ live enterprise technical walkthroughs bridging complex logic with client stakeholders.",
                "Engineered 180+ custom migration scripts at HighRadius with 99.8% data fidelity.",
            ],
            email_body=(
                "Hi Alex,\n\n"
                "Saw Observe.AI is expanding client-facing AI Agent deployments.\n\n"
                "Quick background: I previously led 150+ live enterprise technical walkthroughs and authored 180+ custom "
                "data scripts at HighRadius, bridging complex backend systems with client stakeholders.\n\n"
                "Would you be open to a 10-minute chat this Thursday to see if my background fits what your team is building?\n\n"
                "Best,\nAarya"
            ),
            linkedin_dm=(
                "Hi Alex - saw you lead engineering at Observe.AI. I've led 150+ enterprise client walkthroughs and "
                "built autonomous agent loops with multi-agent reflection. Open to a quick 10-min chat this week?"
            ),
        )

    def test_build_outreach_prompt(self):
        prompt = build_outreach_prompt(self.job, self.match, self.resume_text)
        self.assertIn("Observe.AI", prompt)
        self.assertIn("AI Solutions Engineer", prompt)
        self.assertIn("Python, LLMs, Client Walkthroughs", prompt)
        self.assertIn("PostgreSQL", prompt)
        self.assertIn("150+ client technical walkthroughs", prompt)
        self.assertIn("SUBJECT LINES", prompt)
        self.assertIn("ZERO HALLUCINATION", prompt)

    def test_outreach_draft_schema_validation(self):
        data = self.mock_draft.model_dump()
        draft = OutreachDraft.model_validate(data)
        self.assertEqual(draft.company, "Observe.AI")
        self.assertEqual(len(draft.subject_lines), 3)
        self.assertEqual(len(draft.proof_points), 2)
        self.assertIn("150+ live enterprise", draft.email_body)

    @patch("outreach.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_outreach_success(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = self.mock_draft.model_dump_json()
        mock_generate.return_value = mock_response

        draft = await async_generate_outreach(self.job, self.match, self.resume_text)

        self.assertEqual(draft.company, "Observe.AI")
        self.assertEqual(draft.role, "AI Solutions Engineer")
        self.assertEqual(len(draft.subject_lines), 3)
        self.assertIn("10-minute chat", draft.email_body)

    @patch("outreach.asyncio.sleep", new_callable=AsyncMock)
    @patch("outreach.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_retry_on_503(self, mock_generate, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = self.mock_draft.model_dump_json()

        mock_generate.side_effect = [
            RuntimeError("503 Service Unavailable"),
            mock_response,
        ]

        draft = await async_generate_outreach(self.job, self.match, self.resume_text)

        self.assertEqual(mock_generate.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(draft.company, "Observe.AI")

    @patch("outreach.asyncio.sleep", new_callable=AsyncMock)
    @patch("outreach.client.aio.models.generate_content", new_callable=AsyncMock)
    async def test_async_generate_fail_fast_on_429(self, mock_generate, mock_sleep):
        mock_generate.side_effect = RuntimeError("429 Resource has been exhausted (quota exceeded)")

        with self.assertRaises(RuntimeError) as ctx:
            await async_generate_outreach(self.job, self.match, self.resume_text)

        self.assertIn("429", str(ctx.exception))
        mock_sleep.assert_not_called()
        self.assertEqual(mock_generate.call_count, 1)

    def test_save_outreach_packet(self):
        temp_dir = tempfile.mkdtemp()
        try:
            filepath = save_outreach_packet(self.mock_draft, output_dir=temp_dir)
            self.assertTrue(os.path.exists(filepath))
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# Recruiter Cold Outreach Packet: AI Solutions Engineer at Observe.AI", content)
            self.assertIn("## 📧 Recommended Subject Lines", content)
            self.assertIn("Observe.AI AI Solutions role + 150 enterprise walkthroughs", content)
            self.assertIn("## ✉️ Cold Email Draft (<120 words)", content)
            self.assertIn("## 💬 LinkedIn InMail / Direct Message (<75 words)", content)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
