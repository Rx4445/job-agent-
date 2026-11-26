# Resume PDF Generator Architecture

## Overview
While the agent stores and refines the candidate's ground truth experience in Markdown (`resume.md`), modern Applicant Tracking Systems (ATS) like Greenhouse, Lever, and Workday require binary PDF documents for job applications.

The **Resume PDF Generator** (`pdf_generator.py`) compiles unstructured or structured Markdown resumes into clean, professionally formatted, single/two-page ATS-optimized PDFs.

---

## Architectural Workflow

```mermaid
flowchart TD
    MD["Input: resume.md (Markdown)"] --> Parser[clean_markdown_inline: Regex Tag Parser]
    
    subgraph TagTranslation ["Markdown to ReportLab XML Mapping"]
        Parser --> T1["Bold: **text** -> &lt;b&gt;text&lt;/b&gt;"]
        Parser --> T2["Italic: *text* -> &lt;i&gt;text&lt;/i&gt;"]
        Parser --> T3["Ampersand: & -> &amp;amp;"]
        Parser --> T4["Code: `code` -> &lt;font face='Courier'&gt;code&lt;/font&gt;"]
        Parser --> T5["Links: [text](url) -> formatted string"]
    end

    TagTranslation --> FlowableEngine["ReportLab Flowable Construction"]
    
    subgraph FlowableStyles ["ATS-Optimized Flowables"]
        FlowableEngine --> F1["# Header -> TitleStyle (Helvetica-Bold 18pt)"]
        FlowableEngine --> F2["## Section -> H2Style + Horizontal Separator (HRFlowable)"]
        FlowableEngine --> F3["### Subtitle -> H3Style (Role & Company)"]
        FlowableEngine --> F4["- Bullets -> BulletStyle (Indented with &bull;)"]
        FlowableEngine --> F5["Subtext -> SubheadingStyle (Italicized Dates/Location)"]
    end

    FlowableStyles --> DocBuild["SimpleDocTemplate: Build PDF Document"]
    DocBuild --> PDF["Output: applications/Aarya_Pradhan_Resume.pdf"]
```

---

## Key ATS-Compliance Rules

1. **Strict Single-Column Flow:**
   * Many modern ATS parsers fail when reading multi-column sidebars, table grids, or floating text frames, resulting in scrambled chronological order.
   * `pdf_generator.py` uses a linear single-column flow that standard ATS text extractors read cleanly from top to bottom.

2. **Standard Vector Typography:**
   * Uses built-in `Helvetica` and `Helvetica-Bold` fonts. These do not require embedded custom fonts, ensuring universally parseable ASCII/Unicode text streams.

3. **High-Contrast, Distraction-Free Palette:**
   * Text colors: Deep Slate (`#0F172A`, `#1E293B`) on pure white (`#FFFFFF`).
   * Subtle dividers: `#CBD5E1` horizontal rules separating sections.

4. **Zero Compromise Security:**
   * Output `.pdf` files are protected by `.gitignore` rules (`*.pdf` and `applications/`) so personal contact details and phone numbers are never committed to public repositories.

---

## How to Test

Run the dedicated PDF generator unit test suite (4 tests):
```powershell
python -m unittest test_pdf_generator.py
```

Run the entire project test suite (96 tests passing in ~1.0s):
```powershell
python -m unittest discover
```

Generate a fresh resume PDF directly from terminal:
```powershell
python pdf_generator.py
```
