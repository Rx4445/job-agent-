import os
import shutil
import tempfile
import unittest

from pdf_generator import clean_markdown_inline, markdown_to_pdf_resume
from pypdf import PdfReader


class TestPdfGenerator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.sample_markdown = """# Aarya Pradhan
**Contact:** +91-8217044923 | arya@example.com | GitHub: github.com/Rx4445
**Education:** B.Tech in IT (2026)

---

## Technical Skills
- **Languages:** Python, SQL, JavaScript
- **Frameworks:** FastAPI, Docker, ReportLab

---

## Professional Experience

### HighRadius | Business Analyst
*Bengaluru, India | Feb 2026 – Present*
- Supported 150+ enterprise client solution walkthroughs.
- Authored 180+ custom SQL scripts with 99.8% fidelity.
"""

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_markdown_inline(self):
        self.assertEqual(clean_markdown_inline("**Python** & **SQL**"), "<b>Python</b> &amp; <b>SQL</b>")
        self.assertEqual(clean_markdown_inline("*Italic Text*"), "<i>Italic Text</i>")
        self.assertIn("<b>Repo</b>", clean_markdown_inline("[Repo](https://github.com)"))

    def test_markdown_to_pdf_creates_valid_pdf(self):
        out_pdf = os.path.join(self.test_dir, "test_resume.pdf")
        result_path = markdown_to_pdf_resume(self.sample_markdown, out_pdf)

        self.assertTrue(os.path.exists(result_path))
        self.assertGreater(os.path.getsize(result_path), 1000)

        # Verify PDF magic bytes
        with open(result_path, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_pdf_contains_expected_text_stream(self):
        out_pdf = os.path.join(self.test_dir, "test_resume.pdf")
        markdown_to_pdf_resume(self.sample_markdown, out_pdf)

        reader = PdfReader(out_pdf)
        self.assertGreaterEqual(len(reader.pages), 1)

        extracted_text = "".join(page.extract_text() for page in reader.pages)
        self.assertIn("Aarya Pradhan", extracted_text)
        self.assertIn("TECHNICAL SKILLS", extracted_text)
        self.assertIn("HighRadius", extracted_text)
        self.assertIn("150+ enterprise client solution walkthroughs", extracted_text)

    def test_real_resume_md_compiles_without_errors(self):
        real_resume = "resume.md"
        if os.path.exists(real_resume):
            out_pdf = os.path.join(self.test_dir, "Aarya_Pradhan_Resume.pdf")
            result_path = markdown_to_pdf_resume(real_resume, out_pdf)
            self.assertTrue(os.path.exists(result_path))
            self.assertGreater(os.path.getsize(result_path), 5000)


if __name__ == "__main__":
    unittest.main()
