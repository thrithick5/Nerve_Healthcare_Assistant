from typing import List, Dict, Any
from fastapi import Depends
import structlog

logger = structlog.get_logger()

# RAG service registry for dependency injection
class RAGServices:
    """Container for all RAG services"""
    
    def __init__(self):
        self.embedding_service = None
        self.llm_service = None
        self.retrieval_service = None
        self.conversation_service = None
    
    def initialize(self, services: Dict[str, Any]):
        """Initialize all services"""
        for service_name, service_instance in services.items():
            setattr(self, service_name, service_instance)
        
        logger.info("RAG services initialized", service_names=list(services.keys()))

# Global service registry
_services = RAGServices()

def get_embedding_service():
    """Get embedding service"""
    if not _services.embedding_service:
        raise RuntimeError("Embedding service not initialized")
    return _services.embedding_service

def get_llm_service():
    """Get LLM service"""
    if not _services.llm_service:
        raise RuntimeError("LLM service not initialized")
    return _services.llm_service

def get_retrieval_service():
    """Get retrieval service"""
    if not _services.retrieval_service:
        raise RuntimeError("Retrieval service not initialized")
    return _services.retrieval_service

def get_conversation_service():
    """Get conversation service"""
    if not _services.conversation_service:
        raise RuntimeError("Conversation service not initialized")
    return _services.conversation_service

# Initialize services function
async def initialize_services(mistral_api_key: str, qdrant_client, redis_client, db_session):
    """Initialize all services"""
    from app.core.services import (
        EmbeddingService, LLMService, RetrievalService, ConversationService
    )
    
    embedding_service = EmbeddingService(mistral_api_key)
    llm_service = LLMService(mistral_api_key)
    retrieval_service = RetrievalService(qdrant_client, embedding_service)
    conversation_service = ConversationService(redis_client, db_session)
    
    services = {
        "embedding_service": embedding_service,
        "llm_service": llm_service,
        "retrieval_service": retrieval_service,
        "conversation_service": conversation_service,
    }
    
    _services.initialize(services)
    
    logger.info("All RAG services initialized successfully")
