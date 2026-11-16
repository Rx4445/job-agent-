import unittest
from unittest.mock import AsyncMock, patch
import httpx

from boards import clean_html_content, fetch_greenhouse_jobs, filter_relevant_jobs


class TestJobBoards(unittest.IsolatedAsyncioTestCase):
    def test_clean_html_content_strips_tags(self):
        html_input = "<p>We are seeking a <strong>Senior Engineer</strong>.</p><div>Remote</div>"
        cleaned = clean_html_content(html_input)
        self.assertNotIn("<p>", cleaned)
        self.assertNotIn("<strong>", cleaned)
        self.assertIn("Senior Engineer", cleaned)
        self.assertIn("Remote", cleaned)

    def test_clean_html_content_converts_bullets(self):
        html_input = "<ul><li>Python programming</li><li>Vector search with Chroma</li></ul>"
        cleaned = clean_html_content(html_input)
        self.assertIn("- Python programming", cleaned)
        self.assertIn("- Vector search with Chroma", cleaned)

    def test_clean_html_content_unescapes_entities(self):
        html_input = "RAG &amp; Vector DBs &nbsp; &lt;Cloud&gt;"
        cleaned = clean_html_content(html_input)
        self.assertIn("RAG & Vector DBs", cleaned)
        self.assertIn("<Cloud>", cleaned)

    def test_clean_html_content_handles_empty(self):
        self.assertEqual(clean_html_content(""), "")
        self.assertEqual(clean_html_content(None), "")

    def test_filter_relevant_jobs(self):
        jobs = [
            {"title": "Senior AI Systems Engineer", "company": "Anthropic"},
            {"title": "Office Operations Manager", "company": "Anthropic"},
            {"title": "Backend Python Developer", "company": "Anthropic"},
            {"title": "Executive Assistant", "company": "Anthropic"},
        ]
        filtered = filter_relevant_jobs(jobs, keywords=["ai", "engineer", "python"])
        self.assertEqual(len(filtered), 2)
        titles = [j["title"] for j in filtered]
        self.assertIn("Senior AI Systems Engineer", titles)
        self.assertIn("Backend Python Developer", titles)

    @patch("httpx.AsyncClient.get")
    async def test_fetch_greenhouse_jobs_success(self, mock_get):
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jobs": [
                {
                    "id": 101,
                    "title": "AI Systems Engineer",
                    "location": {"name": "San Francisco, CA"},
                    "content": "<p>Build production RAG pipelines.</p>",
                    "absolute_url": "https://boards.greenhouse.io/anthropic/jobs/101",
                }
            ]
        }
        mock_get.return_value = mock_response

        jobs = await fetch_greenhouse_jobs("anthropic")
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "101")
        self.assertEqual(jobs[0]["title"], "AI Systems Engineer")
        self.assertEqual(jobs[0]["company"], "Anthropic")
        self.assertEqual(jobs[0]["location"], "San Francisco, CA")
        self.assertEqual(jobs[0]["raw_content"], "Build production RAG pipelines.")

    @patch("httpx.AsyncClient.get")
    async def test_fetch_greenhouse_jobs_not_found_404(self, mock_get):
        mock_response = unittest.mock.MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError) as ctx:
            await fetch_greenhouse_jobs("non_existent_company_xyz123")
        self.assertIn("not found on Greenhouse", str(ctx.exception))

    @patch("httpx.AsyncClient.get", side_effect=httpx.ConnectTimeout("Connection timed out"))
    async def test_fetch_greenhouse_jobs_network_timeout(self, mock_get):
        with self.assertRaises(ConnectionError):
            await fetch_greenhouse_jobs("anthropic")

    @patch("boards.generate_batch_applications", new_callable=AsyncMock)
    @patch("boards.save_job")
    @patch("boards.async_extract_job", new_callable=AsyncMock)
    @patch("boards.get_existing_job", return_value=None)
    @patch("boards.get_candidate_profile")
    @patch("boards.load_resume_text", return_value="Resume text...")
    @patch("boards.fetch_greenhouse_jobs")
    async def test_ingest_live_board_and_rank_success(
        self, mock_fetch, mock_load_resume, mock_get_profile, mock_get_existing, mock_extract_job, mock_save_job, mock_generate_apps
    ):
        from boards import ingest_live_board_and_rank
        from extract import JobPosting

        mock_fetch.return_value = [
            {"id": "1", "title": "AI Systems Engineer", "company": "Cloudflare", "raw_content": "Python, RAG", "url": "url1"},
            {"id": "2", "title": "Executive Assistant", "company": "Cloudflare", "raw_content": "Calendar", "url": "url2"},
        ]
        mock_get_profile.return_value = {
            "name": "Aarya Pradhan",
            "experience_years": 2,
            "field": "AI Engineering",
            "skills": ["Python", "RAG"],
        }
        mock_extract_job.return_value = JobPosting(
            title="AI Systems Engineer", company="Cloudflare", skills=["Python", "RAG"]
        )

        results = await ingest_live_board_and_rank(
            company_slug="cloudflare",
            limit=5,
            auto_generate_approved=True,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].job.title, "AI Systems Engineer")
        self.assertEqual(results[0].decision, "APPROVED")
        self.assertEqual(results[0].match.match_score, 100.0)

    @patch("builtins.input", return_value="3")
    @patch("boards.async_extract_job", new_callable=AsyncMock)
    @patch("boards.get_existing_job")
    @patch("boards.get_candidate_profile")
    @patch("boards.load_resume_text", return_value="Resume text...")
    @patch("boards.fetch_greenhouse_jobs")
    async def test_ingest_live_board_deduplication_skips_llm(
        self, mock_fetch, mock_load_resume, mock_get_profile, mock_get_existing, mock_extract_job, mock_input
    ):
        from boards import ingest_live_board_and_rank

        mock_fetch.return_value = [
            {"id": "1", "title": "AI Systems Engineer", "company": "Cloudflare", "raw_content": "Python, RAG", "url": "url1"},
        ]
        mock_get_profile.return_value = {
            "name": "Aarya Pradhan",
            "experience_years": 2,
            "field": "AI Engineering",
            "skills": ["Python", "RAG"],
        }
        # Simulate SQLite cache hit for this job
        mock_get_existing.return_value = {
            "id": 1,
            "title": "AI Systems Engineer",
            "company": "Cloudflare",
            "skills": ["Python", "RAG"],
        }

        results = await ingest_live_board_and_rank(
            company_slug="cloudflare",
            limit=1,
            auto_generate_approved=False,
        )

        self.assertEqual(len(results), 1)
        # CRITICAL ASSERTION: LLM extraction was bypassed because job was in SQLite!
        mock_extract_job.assert_not_called()


if __name__ == "__main__":
    unittest.main()

