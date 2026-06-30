from pypdf import PdfReader
from pathlib import Path
import re

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Returns a list of dicts: {page_number, text, source}
    Extracts per-page so chunk metadata can include page numbers.
    """
    reader = PdfReader(pdf_path)
    source = Path(pdf_path).stem
    pages = []
    
    for page_num, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        
        # Clean up common PDF extraction artifacts
        text = re.sub(r'\n{3,}', '\n\n', raw_text)      # collapse excess newlines
        text = re.sub(r'(?<=[a-z])-\n(?=[a-z])', '', text)  # rejoin hyphenated line-breaks
        text = re.sub(r'[ \t]+', ' ', text)               # normalize whitespace
        text = text.strip()
        
        if len(text) > 50:  # skip blank or near-blank pages
            pages.append({
                "page_number": page_num,
                "text": text,
                "source": source,
                "filepath": str(pdf_path)
            })
    
    return pages