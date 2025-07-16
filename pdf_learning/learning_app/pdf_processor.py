import PyPDF2
import re
from typing import List, Tuple
from django.core.files.uploadedfile import UploadedFile

class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
    
    def extract_text_from_pdf(self, pdf_file: UploadedFile) -> Tuple[str, int]:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            return text, total_pages
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
    
    def extract_text_from_pages(self, pdf_file: UploadedFile, page_range: str) -> str:
        """Extract text from specific pages"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)
            
            # Parse page range (e.g., "1-5", "3,7,9", "1-3,7-10")
            pages_to_extract = self.parse_page_range(page_range, total_pages)
            
            text = ""
            for page_num in pages_to_extract:
                if 0 <= page_num < total_pages:
                    page_text = pdf_reader.pages[page_num].extract_text()
                    text += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
            
            return text
        except Exception as e:
            raise Exception(f"Error extracting pages: {str(e)}")
    
    def parse_page_range(self, page_range: str, total_pages: int) -> List[int]:
        """Parse page range string into list of page numbers (0-indexed)"""
        pages = []
        
        if not page_range.strip():
            return list(range(total_pages))
        
        parts = page_range.split(',')
        
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range like "1-5"
                start, end = part.split('-')
                start = max(1, int(start.strip()))
                end = min(total_pages, int(end.strip()))
                pages.extend(range(start - 1, end))  # Convert to 0-indexed
            else:
                # Single page like "3"
                page_num = int(part.strip())
                if 1 <= page_num <= total_pages:
                    pages.append(page_num - 1)  # Convert to 0-indexed
        
        return sorted(list(set(pages)))  # Remove duplicates and sort
    
    def chunk_text(self, text: str) -> Tuple[List[str], List[int]]:
        """Split text into chunks with page tracking"""
        chunks = []
        page_numbers = []
        
        # Split by page markers
        pages = re.split(r'--- Page (\d+) ---', text)
        
        current_page = 1
        for i in range(1, len(pages), 2):  # Skip empty first element, then take page_num, content pairs
            if i + 1 < len(pages):
                page_num = int(pages[i])
                page_content = pages[i + 1].strip()
                
                if page_content:
                    # Split page content into chunks
                    page_chunks = self.split_into_chunks(page_content)
                    chunks.extend(page_chunks)
                    page_numbers.extend([page_num] * len(page_chunks))
        
        return chunks, page_numbers
    
    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings near the chunk boundary
                for i in range(end, max(start + self.chunk_size - 100, start), -1):
                    if text[i] in '.!?':
                        end = i + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
            
            if start >= len(text):
                break
        
        return chunks
