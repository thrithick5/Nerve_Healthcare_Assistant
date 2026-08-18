from functools import lru_cache
from app.core.config import Settings
from app.services.embedding_service import EmbeddingService
from app.services.retrieval_service import RetrievalService
from app.services.conversation_service import ConversationService
from app.services.llm_service import LLMService
from app.services.ingestion_service import IngestionService
from app.services.scraper import MedicalScraper
from app.services.file_processor import FileProcessor
from app.services.facility_finder_service import FacilityFinderService


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(settings)


@lru_cache
def get_retrieval_service() -> RetrievalService:
    settings = get_settings()
    embedding_service = get_embedding_service()
    return RetrievalService(settings, embedding_service)


@lru_cache
def get_conversation_service() -> ConversationService:
    settings = get_settings()
    return ConversationService(settings)


@lru_cache
def get_llm_service() -> LLMService:
    settings = get_settings()
    retrieval_service = get_retrieval_service()
    conversation_service = get_conversation_service()
    return LLMService(settings, retrieval_service, conversation_service)


@lru_cache
def get_ingestion_service() -> IngestionService:
    settings = get_settings()
    retrieval_service = get_retrieval_service()
    return IngestionService(settings, retrieval_service)


@lru_cache
def get_scraper() -> MedicalScraper:
    return MedicalScraper()


@lru_cache
def get_file_processor() -> FileProcessor:
    settings = get_settings()
    ingestion_service = get_ingestion_service()
    return FileProcessor(settings, ingestion_service)


@lru_cache
def get_facility_finder() -> FacilityFinderService:
    return FacilityFinderService()
