import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.config import Settings
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.ingestion_service import IngestionService


def main():
    settings = Settings()
    embedding_service = EmbeddingService(settings)
    retrieval_service = RetrievalService(settings, embedding_service)
    ingestion_service = IngestionService(settings, retrieval_service)

    directory = "../data/medical_knowledge"
    print(f"Starting document ingestion from: {directory}")

    total_chunks = ingestion_service.ingest_directory(directory)
    stats = ingestion_service.get_collection_stats()

    print(f"\nIngestion complete!")
    print(f"  Chunks ingested: {total_chunks}")
    print(f"  Total chunks in DB: {stats['total_chunks']}")


if __name__ == "__main__":
    main()
