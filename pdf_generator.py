import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


def clean_markdown_inline(text: str) -> str:
    """Converts Markdown inline formatting into ReportLab Paragraph-compatible XML tags."""
    if not text:
        return ""

    # 1. Escape lone ampersands not already part of an XML entity
    text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;)", "&amp;", text)

    # 2. Bold: **text** -> <b>text</b>
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # 3. Italic: *text* -> <i>text</i>
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)

    # 4. Inline Code: `code` -> font Courier
    text = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', text)

    # 5. Markdown Links: [label](url) -> label (url) or bold label
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<b>\1</b> (<font color="#2563EB">\2</font>)', text)

    return text.strip()


def markdown_to_pdf_resume(
    markdown_source: str,
    output_pdf_path: str = "Aarya_Pradhan_Resume.pdf",
) -> str:
    """Converts candidate Markdown resume into a clean, single/two-page ATS-friendly PDF."""
    if os.path.exists(markdown_source):
        with open(markdown_source, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        raw_text = markdown_source

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)

    # Page setup: Standard Letter, 0.5-inch margins (36 pt) for optimal ATS density
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # ATS-Optimized Typography Styles (Helvetica, High-Contrast Palette)
    title_style = ParagraphStyle(
        "ResumeTitle",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=1,  # Center
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=3,
    )

    contact_style = ParagraphStyle(
        "ResumeContact",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        alignment=1,  # Center
        textColor=colors.HexColor("#475569"),
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "ResumeH2",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=7,
        spaceAfter=2,
    )

    h3_style = ParagraphStyle(
        "ResumeH3",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=4,
        spaceAfter=1,
    )

    subheading_style = ParagraphStyle(
        "ResumeSubheading",
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#475569"),
        spaceBefore=0,
        spaceAfter=2,
    )

    bullet_style = ParagraphStyle(
        "ResumeBullet",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
        leftIndent=12,
        firstLineIndent=-7,
        spaceAfter=1.5,
    )

    body_style = ParagraphStyle(
        "ResumeBody",
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=2,
    )

    story = []
    lines = raw_text.splitlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 1. Main Header: # Name
        if stripped.startswith("# "):
            name_text = clean_markdown_inline(stripped[2:])
            story.append(Paragraph(name_text, title_style))

        # 2. Section Separator: ---
        elif stripped == "---":
            story.append(Spacer(1, 2))

        # 3. Section Titles: ## Title
        elif stripped.startswith("## "):
            sec_title = stripped[3:].strip().upper()
            story.append(Spacer(1, 3))
            story.append(Paragraph(sec_title, h2_style))
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.75,
                    color=colors.HexColor("#CBD5E1"),
                    spaceBefore=1,
                    spaceAfter=4,
                )
            )

        # 4. Job / Project Subtitles: ### Title
        elif stripped.startswith("### "):
            sub_title = clean_markdown_inline(stripped[4:])
            story.append(Paragraph(sub_title, h3_style))

        # 5. Italic Subheadings: *Location / Date*
        elif stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            sub_text = clean_markdown_inline(stripped.strip("*"))
            story.append(Paragraph(sub_text, subheading_style))

        # 6. Bullet Items: - Bullet
        elif stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = clean_markdown_inline(stripped[2:])
            formatted_bullet = f"•&nbsp;&nbsp;{bullet_text}"
            story.append(Paragraph(formatted_bullet, bullet_style))

        # 7. Contact Info / Standard Lines: **Contact:** ...
        else:
            clean_line = clean_markdown_inline(stripped)
            if "Contact:" in stripped or "Education:" in stripped or len(story) < 3:
                story.append(Paragraph(clean_line, contact_style))
            else:
                story.append(Paragraph(clean_line, body_style))

    doc.build(story)
    return output_pdf_path


if __name__ == "__main__":
    resume_file = "resume.md"
    output_file = "applications/Aarya_Pradhan_Resume.pdf"
    if os.path.exists(resume_file):
        out = markdown_to_pdf_resume(resume_file, output_file)
        print(f"Generated clean ATS resume PDF at: {out}")
    else:
        print(f"File not found: {resume_file}")
