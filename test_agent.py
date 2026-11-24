import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from extract import JobPosting
from resume import Resume
from agent import AgentState, evaluate_decision_gate, run_job_agent, save_application_packet
from matcher import MatchResult
from auditor import AuditCritique
from outreach import OutreachDraft


class TestJobAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_job = JobPosting(
            title="AI Systems Engineer",
            company="Nexus AI",
            skills=["Python", "RAG", "Vector DBs", "Kubernetes"],
        )
        self.sample_resume = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "RAG", "Vector DBs"],
        )
        self.raw_resume_text = "Aarya Pradhan. Built RAG with Python and Chroma across 10k docs."
        self.sample_critique = AuditCritique(
            score=9,
            is_grounded=True,
            hallucinated_claims=[],
            tone_rating="authentic",
            critique_notes="Well grounded on resume facts.",
        )
        self.sample_outreach = OutreachDraft(
            company="Nexus AI",
            role="AI Systems Engineer",
            subject_lines=["Nexus AI Systems role + RAG pipelines"],
            hook="Saw Nexus AI is scaling production RAG pipelines.",
            proof_points=["Built RAG pipeline across 10k docs."],
            email_body="Hi Alex,\n\nSaw Nexus AI is expanding...\n\nBest,\nAarya",
            linkedin_dm="Hi Alex - saw your team at Nexus AI. Open to a quick chat?",
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("agent.async_generate_outreach", new_callable=AsyncMock)
    @patch("agent.save_candidate_profile")
    @patch("agent.get_candidate_profile", return_value=None)
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_auto_approval_on_high_match(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_save_profile, mock_outreach
    ):
        mock_extract_job.return_value = self.sample_job
        mock_extract_resume.return_value = self.sample_resume
        mock_generate_letter.return_value = ("Dear Nexus AI Team, I built a RAG system...", [self.sample_critique])
        mock_outreach.return_value = self.sample_outreach

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=False,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.decision, "APPROVED")
        self.assertIsNotNone(state.cover_letter)
        self.assertIsNotNone(state.output_path)
        self.assertIsNotNone(state.outreach_path)
        self.assertTrue(os.path.exists(state.output_path))
        self.assertTrue(os.path.exists(state.outreach_path))
        self.assertEqual(len(state.audit_history), 1)
        self.assertEqual(state.audit_history[0].score, 9)
        mock_generate_letter.assert_called_once()
        mock_outreach.assert_called_once()
        mock_save.assert_called_once()

    @patch("builtins.input", return_value="n")
    @patch("agent.save_candidate_profile")
    @patch("agent.get_candidate_profile", return_value=None)
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_decision_gate_moderate_fit_aborted(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_save_profile, mock_input
    ):
        # 2 of 4 skills = 50%
        mock_extract_job.return_value = self.sample_job
        mock_extract_resume.return_value = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "RAG"],
        )

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=True,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.decision, "ABORTED")
        self.assertIsNone(state.cover_letter)
        self.assertIsNone(state.output_path)
        mock_generate_letter.assert_not_called()

    @patch("agent.async_generate_outreach", new_callable=AsyncMock)
    @patch("builtins.input", return_value="y")
    @patch("agent.save_candidate_profile")
    @patch("agent.get_candidate_profile", return_value=None)
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_decision_gate_moderate_fit_approved(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_save_profile, mock_input, mock_outreach
    ):
        # 2 of 4 skills = 50%
        mock_extract_job.return_value = self.sample_job
        mock_extract_resume.return_value = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "RAG"],
        )
        mock_generate_letter.return_value = ("Cover letter text...", [self.sample_critique])
        mock_outreach.return_value = self.sample_outreach

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=True,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.decision, "APPROVED")
        self.assertIsNotNone(state.cover_letter)
        mock_generate_letter.assert_called_once()

    @patch("builtins.input", return_value="n")
    @patch("agent.save_candidate_profile")
    @patch("agent.get_candidate_profile", return_value=None)
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_decision_gate_low_fit_aborted(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_save_profile, mock_input
    ):
        # 0 skills = 0%
        mock_extract_job.return_value = self.sample_job
        mock_extract_resume.return_value = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="Graphic Design",
            skills=["Photoshop"],
        )

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=True,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.decision, "ABORTED")
        mock_generate_letter.assert_not_called()

    async def test_missing_resume_file_aborts_gracefully(self):
        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_path="non_existent_file_path_12345.md",
            interactive=False,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.decision, "ABORTED")
        self.assertTrue(any("Failed to load resume" in log for log in state.logs))

    @patch("agent.async_generate_outreach", new_callable=AsyncMock)
    @patch("agent.get_candidate_profile")
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_resume_cache_hit_skips_llm_extraction(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_outreach
    ):
        mock_extract_job.return_value = self.sample_job
        mock_get_profile.return_value = {
            "name": "Cached Candidate",
            "experience_years": 3,
            "field": "AI Engineering",
            "skills": ["Python", "RAG", "Vector DBs"],
        }
        mock_generate_letter.return_value = ("Cover letter text...", [self.sample_critique])
        mock_outreach.return_value = self.sample_outreach

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=False,
            output_dir=self.test_dir,
        )

        self.assertEqual(state.candidate.name, "Cached Candidate")
        self.assertEqual(state.candidate.skills, ["Python", "RAG", "Vector DBs"])
        # Crucial assertion: Gemini was NEVER called for resume extraction!
        mock_extract_resume.assert_not_called()
        self.assertTrue(any("Loaded candidate profile from cache (0ms)" in log for log in state.logs))

    @patch("agent.async_generate_outreach", new_callable=AsyncMock)
    @patch("agent.save_candidate_profile")
    @patch("agent.get_candidate_profile", return_value=None)
    @patch("agent.async_generate_audited_cover_letter", new_callable=AsyncMock)
    @patch("agent.async_extract_resume", new_callable=AsyncMock)
    @patch("agent.async_extract_job", new_callable=AsyncMock)
    @patch("agent.save_job")
    async def test_resume_cache_miss_calls_gemini_and_saves_profile(
        self, mock_save, mock_extract_job, mock_extract_resume, mock_generate_letter, mock_get_profile, mock_save_profile, mock_outreach
    ):
        mock_extract_job.return_value = self.sample_job
        mock_extract_resume.return_value = self.sample_resume
        mock_generate_letter.return_value = ("Cover letter text...", [self.sample_critique])
        mock_outreach.return_value = self.sample_outreach

        state = await run_job_agent(
            posting_text="Job posting text...",
            resume_text_override=self.raw_resume_text,
            interactive=False,
            output_dir=self.test_dir,
        )

        # On miss, Gemini is called and profile is saved to SQLite
        mock_extract_resume.assert_called_once()
        mock_save_profile.assert_called_once()
        self.assertTrue(any("Cache miss" in log for log in state.logs))


if __name__ == "__main__":
    unittest.main()
