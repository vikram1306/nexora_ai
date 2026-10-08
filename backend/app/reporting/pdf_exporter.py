from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app.schemas.agents import ExecutiveQueryResponse


class ExecutiveReportPDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42) # Obsidian Dark Banner
        self.rect(0, 0, 210, 32, "F")

        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "NEXORA AI - EXECUTIVE INTELLIGENCE REPORT", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

        self.set_font("Helvetica", "", 9)
        self.set_text_color(148, 163, 184)
        self.cell(0, 6, "Zero-Hallucination Verified | Autonomous Enterprise OS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}} - Nexora AI Confidential Executive Output", align="C")


def sanitize_pdf_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("•", "-").replace("### ", "").replace("**", "")
    return text.encode("latin-1", "replace").decode("latin-1")


def generate_executive_pdf_bytes(query_res: ExecutiveQueryResponse) -> bytes:
    pdf = ExecutiveReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_text_color(15, 23, 42)

    # Metadata Section
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Query Prompt:")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, sanitize_pdf_text(query_res.prompt))

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Intent:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, sanitize_pdf_text(query_res.intent), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Confidence:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"{int(query_res.confidence_score * 100)}% Zero-Hallucination Verification Score", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Executive Summary
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 8, "EXECUTIVE SUMMARY", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(226, 232, 240)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(51, 65, 85)
    clean_summary = sanitize_pdf_text(query_res.executive_summary or "")
    pdf.multi_cell(0, 5, clean_summary)
    pdf.ln(6)

    # Strategic Recommendations
    if query_res.strategic_recommendations:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 8, "STRATEGIC RECOMMENDATIONS", new_x="LMARGIN", new_y="NEXT")
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

        for i, r in enumerate(query_res.strategic_recommendations, 1):
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, sanitize_pdf_text(f"{i}. [{r.target_department}] {r.title}"), new_x="LMARGIN", new_y="NEXT")

            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(51, 65, 85)
            pdf.multi_cell(0, 5, sanitize_pdf_text(f"Action Item: {r.action_item}"))

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(16, 185, 129) # Emerald Impact
            pdf.cell(0, 6, sanitize_pdf_text(f"Expected Impact: {r.expected_impact}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(3)

    return bytes(pdf.output())
