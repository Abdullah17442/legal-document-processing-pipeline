import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str):
    """
    Extract text from every page of a PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        dict: {
            "text": Extracted text,
            "pages": Number of pages,
            "characters": Number of characters
        }
    """

    try:
        document = fitz.open(pdf_path)

        extracted_text = ""

        for page in document:
            extracted_text += page.get_text("text") + "\n"

        page_count = len(document)
        document.close()

        return {
            "text": extracted_text,
            "pages": page_count,
            "characters": len(extracted_text)
        }

    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")