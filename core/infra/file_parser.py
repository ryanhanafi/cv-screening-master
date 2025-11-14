from PyPDF2 import PdfReader
from core.application.interfaces import IFileParser

class PdfParser(IFileParser):
    def parse(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            pdf = PdfReader(f)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        return text
