"""
Service definitions for all backend components
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from pydantic import BaseModel
import structlog

logger = structlog.get_logger()
class EmbeddingModel(BaseModel):
    id: str
    model_name: str
    provider: str
    max_tokens: int
    embedding_dim: int
    description: str
class LLMModel(BaseModel):
    id: str
    model_name: str
    provider: str
    max_tokens: int
    context_length: int
    is_available: bool
    parameters: Optional[Dict[str, Any]] = None
class RetrievaGenerator(Base, ABC):
    """Abstract base class for retrieval-augmented generation"""
    
    @abstractmethod
    def retrieve(self, query: str, filters: Optional[Dict] = None, top_k: int = 5) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def generate(self, prompt: str, context: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str:
        pass
class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self, mistral_api_key: str):
        self.api_key = mistral_api_key
        self.model = EmbeddingModel(
            id="mistral-embed",
            model_name="mistral-embed",
            provider="mistral",
            max_tokens=8192,
            embedding_dim=1024,
            description="Mistral embedding model for medical text"
        )
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            from mistralai import MistralClient
            client = MistralClient(api_key=self.api_key)
            response = await client.embeddings.create(
                model=self.model.model_name,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        try:
            from mistralai import MistralClient
            client = MistralClient(api_key=self.api_key)
            response = await client.embeddings.create(
                model=self.model.model_name,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("Batch embedding generation failed", error=str(e))
            raise

    async def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        import numpy as np
        
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
class LLMService:
    """Service for interacting with LLM models"""
    
    def __init__(self, mistral_api_key: str):
        self.api_key = mistral_api_key
        self.model = LLMModel(
            id="mistral-large-latest",
            model_name="mistral-large-latest",
            provider="mistral",
            max_tokens=1024,
            context_length=32768,
            is_available=True,
            parameters={
                "temperature": 0.3,
                "top_p": 0.9,
                "max_tokens": 1024,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.0
            }
        )
    
    async def generate_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate completion from LLM"""
        try:
            from mistralai import MistralClient
            client = MistralClient(api_key=self.api_key)
            
            response = await client.chat.complete(
                model=self.model.model_name,
                messages=messages,
                **kwargs
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise Exception("No completion generated")
        except Exception as e:
            logger.error("LLM completion failed", error=str(e))
            raise
    
    async def generate_medical_response(self, query: str, context: List[Dict[str, Any]] = None) -> str:
        """Generate medical response with safety guidelines"""
        system_prompt = """You are an AI healthcare assistant providing medical information for informational purposes only. 
        
        GUIDELINES:
        1. Always include a medical disclaimer at the end of your response
        2. Never provide specific medical diagnoses
        3. Encourage consulting healthcare professionals for medical advice
        4. Cite sources when providing information
        5. Be honest about limitations of AI knowledge
        6. Prioritize user safety and well-being
        
        Remember: I am an AI assistant for informational support only. Not a substitute for professional medical advice."""
        
        user_prompt = f"User query: {query}\n\n"
        
        if context:
            user_prompt += "Relevant information:\n"
            for i, source in enumerate(context, 1):
                user_prompt += f"{i}. Title: {source.get('title', 'N/A')}\n"
                user_prompt += f"   Content: {source.get('content', 'N/A')}\n\n"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        default_params = self.model.parameters.copy()
        default_params.update(kwargs)
        
        response = await self.generate_completion(messages, **default_params)
        
        # Ensure disclaimer is included
        if self.model.parameters.get("medical_disclaimer", True):
            disclaimer = "\n\n**Medical Disclaimer**: " + self.model.parameters.get("medical_disclaimer_text", 
                "I am an AI assistant for informational support only. Not a substitute for professional medical advice.")
            response += disclaimer
        
        return response
class RetrievalService:
    """Service for retrieving relevant information from knowledge base"""
    
    def __init__(self, qdrant_client: QdrantClient, embedding_service: EmbeddingService):
        self.client = qdrant_client
        self.embedding_service = embedding_service
        self.collection_name = "medical_knowledge"
        self.min_score = 0.7
    
    async def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=self.min_score,
                with_payload=True,
                with_vector=False,
            )
            
            results = []
            for point in search_result:
                results.append({
                    "id": point.id,
                    "title": point.payload.get("title", "Untitled"),
                    "content": point.payload.get("content", ""),
                    "score": point.score,
                    "metadata": point.payload.get("metadata", {}),
                    "source": point.payload.get("source", "unknown"),
                    "timestamp": point.payload.get("timestamp", ""),
                })
            
            return results
        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            raise
    
    async def filter_by_criteria(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter search results by criteria"""
        filtered_results = []
        
        for result in results:
            match = True
            
            for key, value in filters.items():
                if key in result:
                    if isinstance(value, list) and result[key] not in value:
                        match = False
                        break
                    elif result[key] != value:
                        match = False
                        break
            
            if match:
                filtered_results.append(result)
        
        return filtered_results

    async def get_fallback_sources(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get fallback sources from different knowledge bases"""
        results = []
        
        # Try different sources in order of preference
        sources = ["web_search", "medical_knowledge", "internal_docs"]
        
        for source in sources:
            try:
                if source == "web_search" and self.is_web_search_enabled:
                    # This would be implemented separately with web scraping
                    pass
                
                elif source == "medical_knowledge":
                    source_results = await self.search_similar(query, limit)
                    results.extend(source_results)
                
                elif source == "internal_docs":
                    # Internal documents (if any)
                    pass
                
                if results:
                    break
            except Exception as e:
                logger.warning(f"Source {source} failed", error=str(e))
                continue
        
        return results
class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self, redis_client: redis.Redis, db_session):
        self.redis = redis_client
        self.db = db_session
        self.max_history_length = 10
    
    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new conversation"""
        conversation_id = f"conv_{user_id}_{int(time.time())}"
        
        # Save to database
        db_conversation = Conversation(
            id=conversation_id,
            user_id=user_id,
            title=title or "New Conversation",
            context={},
            message_count=0,
            tags=[]
        )
        
        self.db.add(db_conversation)
        self.db.commit()
        
        # Also save in Redis for real-time updates
        conv_key = f"conv:{conversation_id}"
        self.redis.hset(conv_key, "user_id", user_id)
        self.redis.hset(conv_key, "title", title or "New Conversation")
        self.redis.expire(conv_key, 3600 * 24 * 30)  # 30 days
        
        logger.info("Conversation created", conversation_id=conversation_id, user_id=user_id)
        
        return conversation_id
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Dict[str, Any]:
        """Get conversation by ID"""
        # Try Redis first for speed
        conv_key = f"conv:{conversation_id}"
        conv_data = self.redis.hgetall(conv_key)
        
        if conv_data:
            return {
                "id": conversation_id,
                "user_id": conv_data.get("user_id"),
                "title": conv_data.get("title"),
                "source": "redis"
            }
        
        # Fall back to database
        db_conv = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not db_conv:
            return None
        
        return {
            "id": db_conv.id,
            "user_id": db_conv.user_id,
            "title": db_conv.title,
            "source": "database"
        }
    
    async def get_user_conversations(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all conversations for a user"""
        # Try Redis first
        pattern = f"conv:*"
        keys = self.redis.keys(pattern)
        conversations = []
        
        for key in keys:
            conv_data = self.redis.hgetall(key)
            if conv_data.get("user_id") == user_id:
                conversations.append({
                    "id": key.decode().split(":")[1],
                    "user_id": conv_data.get("user_id"),
                    "title": conv_data.get("title"),
                    "source": "redis"
                })
        
        # Sort by creation time (newest first)
        conversations.sort(key=lambda x: x["id"], reverse=True)
        
        return conversations[:limit]
    
    async def update_conversation(self, conversation_id: str, updates: Dict[str, Any]) -> bool:
        """Update conversation"""
        # Update in Redis
        conv_key = f"conv:{conversation_id}"
        for key, value in updates.items():
            self.redis.hset(conv_key, key, value)
        
        # Update in database
        db_conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if db_conv:
            for key, value in updates.items():
                setattr(db_conv, key, value)
            self.db.commit()
        
        return True
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete conversation"""
        # Delete from Redis
        conv_key = f"conv:{conversation_id}"
        self.redis.delete(conv_key)
        
        # Delete from database
        result = self.db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).delete()
        
        if result:
            self.db.commit()
            logger.info("Conversation deleted", conversation_id=conversation_id)
            return True
        
        return False
