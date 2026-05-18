import io
import os

def extract_text_from_file(file_storage) -> str:
    """Extract text from uploaded PDF or DOCX resume."""
    filename = file_storage.filename.lower()
    try:
        if filename.endswith(".pdf"):
            import PyPDF2
            reader = PyPDF2.PdfReader(io.BytesIO(file_storage.read()))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text.strip()
        elif filename.endswith(".docx"):
            import docx
            doc = docx.Document(io.BytesIO(file_storage.read()))
            text = "\n".join(para.text for para in doc.paragraphs)
            return text.strip()
        elif filename.endswith(".txt"):
            return file_storage.read().decode("utf-8", errors="ignore").strip()
        else:
            return ""
    except Exception as e:
        return f"Error parsing file: {e}"
