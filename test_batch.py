import os
import shutil
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from batch import (
    BatchJobResult,
    classify_batch_decision,
    evaluate_batch_jobs,
    generate_batch_applications,
    render_leaderboard,
    run_batch_workflow,
    scan_job_files,
)
from extract import JobPosting
from matcher import MatchResult
from resume import Resume


class TestBatchProcessing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()

        # Create dummy job files
        self.file_ai = os.path.join(self.temp_dir, "01_ai.txt")
        self.file_backend = os.path.join(self.temp_dir, "02_backend.md")
        self.file_ignored = os.path.join(self.temp_dir, "03_ignored.pdf")

        with open(self.file_ai, "w", encoding="utf-8") as f:
            f.write("AI Engineer posting text")
        with open(self.file_backend, "w", encoding="utf-8") as f:
            f.write("Backend Engineer posting text")
        with open(self.file_ignored, "w", encoding="utf-8") as f:
            f.write("Binary PDF dummy content")

        self.sample_candidate = Resume(
            name="Aarya Pradhan",
            experience_years=2,
            field="AI Engineering",
            skills=["Python", "Vector DBs", "RAG"],
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_scan_job_files_filters_and_sorts(self):
        files = scan_job_files(self.temp_dir)
        self.assertEqual(len(files), 2)
        self.assertTrue(files[0][0].endswith("01_ai.txt"))
        self.assertTrue(files[1][0].endswith("02_backend.md"))
        self.assertEqual(files[0][1], "AI Engineer posting text")

    def test_scan_job_files_missing_directory(self):
        with self.assertRaises(FileNotFoundError):
            scan_job_files("non_existent_folder_xyz123")

    def test_classify_batch_decision(self):
        self.assertEqual(classify_batch_decision(85.0), "APPROVED")
        self.assertEqual(classify_batch_decision(70.0), "APPROVED")
        self.assertEqual(classify_batch_decision(65.0), "REVIEW")
        self.assertEqual(classify_batch_decision(50.0), "REVIEW")
        self.assertEqual(classify_batch_decision(49.9), "ABORTED")
        self.assertEqual(classify_batch_decision(0.0), "ABORTED")

    @patch("batch.save_job")
    @patch("batch.async_extract_job", new_callable=AsyncMock)
    @patch("batch.get_candidate_profile")
    @patch("batch.load_resume_text", return_value="Candidate resume raw text")
    @patch("batch.init_db")
    async def test_evaluate_batch_jobs_ranks_descending(
        self, mock_init, mock_load_resume, mock_get_profile, mock_extract_job, mock_save_job
    ):
        mock_get_profile.return_value = {
            "name": "Aarya Pradhan",
            "experience_years": 2,
            "field": "AI Engineering",
            "skills": ["Python", "Vector DBs", "RAG"],
        }

        # Return 2 jobs: first has 1 match (33%), second has 3 matches (100%)
        job_low = JobPosting(title="Designer", company="Studio", skills=["Photoshop", "Figma", "UI"])
        job_high = JobPosting(title="AI Eng", company="Nexus", skills=["Python", "Vector DBs", "RAG"])

        mock_extract_job.side_effect = [job_low, job_high]

        results, resume_text, candidate = await evaluate_batch_jobs(self.temp_dir)

        self.assertEqual(len(results), 2)
        # Leaderboard sorting check: job_high (100%) must be ranked #1
        self.assertEqual(results[0].job.title, "AI Eng")
        self.assertEqual(results[0].decision, "APPROVED")
        self.assertEqual(results[0].match.match_score, 100.0)

        # job_low (0%) must be ranked #2
        self.assertEqual(results[1].job.title, "Designer")
        self.assertEqual(results[1].decision, "ABORTED")
        self.assertEqual(results[1].match.match_score, 0.0)

    @patch("batch.save_application_packet", return_value="applications/sample.md")
    @patch("batch.async_generate_audited_cover_letter", new_callable=AsyncMock)
    async def test_generate_batch_applications(self, mock_generate_letter, mock_save_packet):
        mock_generate_letter.return_value = ("Cover letter body...", [])
        job = JobPosting(title="AI Eng", company="Nexus", skills=["Python"])
        match = MatchResult(
            field_match=True, match_score=100.0, matching_skills=["Python"], missing_skills=[], is_recommended=True
        )
        res = BatchJobResult(source_file="01.txt", job=job, match=match, decision="APPROVED")

        paths = await generate_batch_applications([res], "Resume text", self.sample_candidate, self.output_dir)

        self.assertEqual(len(paths), 1)
        self.assertEqual(res.cover_letter, "Cover letter body...")
        self.assertEqual(res.output_path, "applications/sample.md")
        mock_generate_letter.assert_called_once()
        mock_save_packet.assert_called_once()

    @patch("batch.generate_batch_applications", new_callable=AsyncMock)
    @patch("batch.evaluate_batch_jobs")
    async def test_run_batch_workflow_auto_generate(self, mock_evaluate, mock_generate_apps):
        job = JobPosting(title="AI Eng", company="Nexus", skills=["Python"])
        match = MatchResult(
            field_match=True, match_score=80.0, matching_skills=["Python"], missing_skills=[], is_recommended=True
        )
        res_approved = BatchJobResult(source_file="01.txt", job=job, match=match, decision="APPROVED")
        res_review = BatchJobResult(source_file="02.txt", job=job, match=match, decision="REVIEW")

        mock_evaluate.return_value = ([res_approved, res_review], "resume text", self.sample_candidate)

        results = await run_batch_workflow(
            directory=self.temp_dir,
            auto_generate_approved=True,
            output_dir=self.output_dir,
        )

        self.assertEqual(len(results), 2)
        # Asserts only the APPROVED job was sent to batch generator
        mock_generate_apps.assert_called_once_with(
            [res_approved], "resume text", self.sample_candidate, self.output_dir
        )

    def test_render_leaderboard_smoke_test(self):
        job = JobPosting(title="AI Systems Engineer", company="Nexus AI", skills=["Python"])
        match = MatchResult(
            field_match=True,
            match_score=85.7,
            matching_skills=["Python"],
            missing_skills=["Kubernetes"],
            is_recommended=True,
        )
        res = BatchJobResult(source_file="01.txt", job=job, match=match, decision="APPROVED")
        # Ensure render_leaderboard runs cleanly without throwing formatting exceptions
        render_leaderboard([res])


if __name__ == "__main__":
    unittest.main()
