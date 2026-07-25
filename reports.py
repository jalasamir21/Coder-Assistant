import io
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


def _text_to_html(text: str) -> str:
    return escape(text or "").replace("\n", "<br/>")


def build_pdf_report(title: str, sections: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    code_style = ParagraphStyle(
        "Code",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        backColor="#F2F2F2",
        borderPadding=6,
    )

    story = [Paragraph(title, styles["Title"])]
    story.append(Paragraph(datetime.now().strftime("Generated %Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 16))

    for heading, content, is_code in sections:
        story.append(Paragraph(heading, styles["Heading2"]))
        story.append(Spacer(1, 6))
        style = code_style if is_code else styles["Normal"]
        story.append(Paragraph(_text_to_html(content), style))
        story.append(Spacer(1, 14))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def build_generation_report(task: str, code: str) -> bytes:
    sections = [("Task", task, False), ("Generated code", code, True)]
    return build_pdf_report("Code Generation Report", sections)


def build_analysis_report(file_name: str, idea: str, line_by_line: str) -> bytes:
    sections = [
        ("File", file_name, False),
        ("Idea", idea, False),
        ("Line by line", line_by_line, False),
    ]
    return build_pdf_report("Code Analysis Report", sections)


def build_debug_report(file_name: str, issue: str, report: str, sources: list = None) -> bytes:
    sections = [
        ("File", file_name, False),
        ("Issue description", issue.strip() if issue and issue.strip() else "Not provided", False),
        ("Debug report", report, False),
    ]
    if sources:
        sources_text = "\n".join(f"{s['title']} - {s['link']}" for s in sources)
        sections.append(("Retrieved from Stack Overflow", sources_text, False))
    return build_pdf_report("Debug Report", sections)