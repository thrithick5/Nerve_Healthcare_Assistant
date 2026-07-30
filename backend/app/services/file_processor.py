import io
from typing import Dict, Any, Optional
from PIL import Image
from app.core.config import Settings
from app.services.ingestion_service import IngestionService
import pytesseract
from pdf2image import convert_from_path
import os

class FileProcessor:
    def __init__(self, settings: Settings, ingestion_service: IngestionService):
        self.settings = settings
        self.ingestion_service = ingestion_service

    def process_file(self, file_path: str, title: str) -> Dict[str, Any]:
        """Process image, PDF, or document file and extract text."""
        try:
            if file_path.lower().endswith('.png') or file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg') or file_path.lower().endswith('.gif') or file_path.lower().endswith('.bmp'):
                return self.process_image(file_path, title)
            elif file_path.lower().endswith('.pdf'):
                return self.process_pdf(file_path, title)
            elif file_path.lower().endswith('.txt'):
                return self.process_text(file_path, title)
            else:
                return {"success": False, "message": "Unsupported file format", "chunks": 0}
        except Exception as e:
            return {"success": False, "message": f"Error processing file: {str(e)}", "chunks": 0}

    def process_image(self, image_path: str, title: str) -> Dict[str, Any]:
        """Process an image file using OCR."""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)
            return self.ingest_extracted_text(title, text, f"image:{os.path.basename(image_path)}")
        except Exception as e:
            return {"success": False, "message": f"Error processing image: {str(e)}", "chunks": 0}

    def process_pdf(self, pdf_path: str, title: str) -> Dict[str, Any]:
        """Process a PDF file and extract text from all pages."""
        try:
            images = convert_from_path(pdf_path, dpi=200, timeout=30)
            all_text = ""
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image)
                all_text += f"\n=== Page {i + 1} ===\n{page_text}\n"

            return self.ingest_extracted_text(title, all_text, f"pdf:{os.path.basename(pdf_path)}")
        except Exception as e:
            return {"success": False, "message": f"Error processing PDF: {str(e)}", "chunks": 0}

    def process_text(self, text_path: str, title: str) -> Dict[str, Any]:
        """Process a text file."""
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.ingest_extracted_text(title, text, f"text:{os.path.basename(text_path)}")
        except Exception as e:
            return {"success": False, "message": f"Error processing text file: {str(e)}", "chunks": 0}

    def ingest_extracted_text(self, title: str, text: str, source: str) -> Dict[str, Any]:
        """Ingest extracted text into the vector database."""
        try:
            chunks = self.ingestion_service.ingest_text(text, title, source)
            stats = self.ingestion_service.get_collection_stats()
            return {
                "success": True,
                "message": f"Processed and ingested {chunks} chunks from {source}",
                "chunks": chunks,
                "total_chunks": stats["total_chunks"],
                "extracted_text": text,
                "source": source
            }
        except Exception as e:
            return {"success": False, "message": f"Error ingesting text: {str(e)}", "chunks": 0}
