import os
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

from agent import AgentState
from cli import get_job_input, main, prompt_multiline_job_text, read_job_text_from_file
from extract import JobPosting
from matcher import MatchResult
from resume import Resume


class TestCLI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_file = os.path.join(self.temp_dir, "sample_job.txt")
        with open(self.sample_file, "w", encoding="utf-8") as f:
            f.write("Seeking Python and RAG engineer.")

    def tearDown(self):
        if os.path.exists(self.sample_file):
            os.remove(self.sample_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_read_job_text_from_file_success(self):
        text = read_job_text_from_file(self.sample_file)
        self.assertEqual(text, "Seeking Python and RAG engineer.")

    def test_read_job_text_from_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            read_job_text_from_file("non_existent_file_path_xyz.txt")

    @patch("builtins.input", side_effect=["Line 1", "Line 2", "END"])
    def test_prompt_multiline_job_text(self, mock_input):
        result = prompt_multiline_job_text()
        self.assertEqual(result, "Line 1\nLine 2")

    @patch("cli.read_job_text_from_file", return_value="Job content")
    def test_get_job_input_with_arg_path(self, mock_read):
        result = get_job_input("custom_path.txt")
        self.assertEqual(result, "Job content")
        mock_read.assert_called_once_with("custom_path.txt")

    @patch("builtins.input", return_value="1")
    @patch("cli.prompt_multiline_job_text", return_value="Pasted content")
    def test_get_job_input_interactive_paste(self, mock_prompt, mock_input):
        result = get_job_input(None)
        self.assertEqual(result, "Pasted content")
        mock_prompt.assert_called_once()

    @patch("builtins.input", side_effect=["2", "path/to/job.txt"])
    @patch("cli.read_job_text_from_file", return_value="File content")
    def test_get_job_input_interactive_file(self, mock_read, mock_input):
        result = get_job_input(None)
        self.assertEqual(result, "File content")
        mock_read.assert_called_once_with("path/to/job.txt")

    @patch("cli.run_job_agent", new_callable=AsyncMock)
    @patch("cli.get_job_input", return_value="Python RAG posting")
    @patch("sys.argv", ["cli.py", "--non-interactive"])
    async def test_main_cli_approved(self, mock_get_input, mock_run_agent):
        mock_state = AgentState(posting_text="Python RAG posting")
        mock_state.decision = "APPROVED"
        mock_state.output_path = "applications/sample.md"
        mock_state.cover_letter = "Dear Team, here is my cover letter..."
        mock_run_agent.return_value = mock_state

        await main()
        mock_run_agent.assert_called_once_with(
            posting_text="Python RAG posting",
            resume_path="resume.md",
            interactive=False,
        )

    @patch("cli.run_job_agent", new_callable=AsyncMock)
    @patch("cli.get_job_input", return_value="Python RAG posting")
    @patch("sys.argv", ["cli.py"])
    async def test_main_cli_aborted(self, mock_get_input, mock_run_agent):
        mock_state = AgentState(posting_text="Python RAG posting")
        mock_state.decision = "ABORTED"
        mock_run_agent.return_value = mock_state

        await main()
        mock_run_agent.assert_called_once_with(
            posting_text="Python RAG posting",
            resume_path="resume.md",
            interactive=True,
        )


if __name__ == "__main__":
    unittest.main()
