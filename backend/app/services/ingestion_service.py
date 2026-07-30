import os
import uuid
from app.core.config import Settings
from app.services.retrieval_service import RetrievalService


class TextChunk:
    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = metadata


class IngestionService:
    def __init__(self, settings: Settings, retrieval_service: RetrievalService):
        self.settings = settings
        self.retrieval_service = retrieval_service

    def chunk_text(self, text: str, source: str) -> list[TextChunk]:
        words = text.split()
        chunks = []
        chunk_size = self.settings.CHUNK_SIZE
        overlap = self.settings.CHUNK_OVERLAP

        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            if len(chunk_words) < 50:
                continue
            chunk_text = " ".join(chunk_words)
            chunks.append(TextChunk(
                text=chunk_text,
                metadata={"source": source, "chunk_index": len(chunks)}
            ))
        return chunks

    def ingest_text(self, text: str, title: str, source: str = "manual") -> int:
        chunks = self.chunk_text(text, source)
        if not chunks:
            return 0

        ids = [str(uuid.uuid4()) for _ in chunks]
        documents = [c.text for c in chunks]
        metadatas = [{"title": title, "source": source, "chunk_index": c.metadata["chunk_index"]} for c in chunks]

        self.retrieval_service.add_documents(ids, documents, metadatas)
        return len(chunks)

    def ingest_directory(self, directory: str) -> int:
        total_chunks = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if not os.path.isfile(filepath):
                continue

            if filename.endswith(".pdf"):
                text = self._parse_pdf(filepath)
            elif filename.endswith(".txt"):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            elif filename.endswith(".md"):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
            else:
                continue

            if text.strip():
                title = os.path.splitext(filename)[0]
                chunks = self.ingest_text(text, title, source=filename)
                total_chunks += chunks

        return total_chunks

    def _parse_pdf(self, filepath: str) -> str:
        try:
            import fitz
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except ImportError:
            return ""

    def get_collection_stats(self) -> dict:
        try:
            count = self.retrieval_service.collection.count()
            return {"total_chunks": count}
        except Exception:
            return {"total_chunks": 0}
