from fpdf import FPDF
from docx import Document

def txt_to_pdf(txt_path):
    pdf_path = txt_path.replace(".txt", ".pdf")
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            safe = line.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(0, 8, safe.strip())

    pdf.output(pdf_path)
    print("PDF saved:", pdf_path)
    return pdf_path

def txt_to_docx(txt_path):
    docx_path = txt_path.replace(".txt", ".docx")
    doc = Document()

    with open(txt_path, "r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:
                doc.add_paragraph(text)
            else:
                doc.add_paragraph("")

    doc.save(docx_path)
    print("DOCX saved:", docx_path)
    return docx_path
