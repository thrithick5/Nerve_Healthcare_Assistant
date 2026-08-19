import os
os.environ["ANONYMOUS_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = ""

try:
    import chromadb.telemetry.product.posthog as _chroma_posthog
    _chroma_posthog.Posthog.capture = lambda self, event: None
except Exception:
    pass

import chromadb
from typing import Optional
from chromadb.config import Settings as ChromaSettings
from app.core.config import Settings
from app.services.embedding_service import EmbeddingService


class RetrievalService:
    def __init__(self, settings: Settings, embedding_service: EmbeddingService):
        self.settings = settings
        self.embedding_service = embedding_service
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, ids: list[str], documents: list[str], metadatas: list[dict]):
        embeddings = self.embedding_service.embed_batch(documents)
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def query(self, query_text: str, top_k: Optional[int] = None, min_score: float = 0.5) -> list[dict]:
        k = top_k or self.settings.TOP_K_RETRIEVAL
        query_embedding = self.embedding_service.embed(query_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2
        )
        sources = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                dist = results["distances"][0][i] if results["distances"] else 0
                rel_score = 1.0 - dist
                if rel_score >= min_score:
                    source = results["metadatas"][0][i].get("source", "")
                    sources.append({
                        "title": results["metadatas"][0][i].get("title", "Unknown"),
                        "content": doc,
                        "relevance_score": rel_score,
                        "source": source
                    })
        return sources

    def query_by_source(self, source: str, top_k: Optional[int] = None) -> list[dict]:
        results = self.collection.get(
            where={"source": source},
            limit=top_k or 20
        )
        chunks = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                chunks.append({
                    "title": results["metadatas"][i].get("title", "Unknown"),
                    "content": doc,
                    "source": results["metadatas"][i].get("source", ""),
                })
        return chunks

    def get_context(self, query_text: str) -> str:
        sources = self.query(query_text)
        if not sources:
            return ""
        context_parts = []
        for src in sources:
            context_parts.append(f"Source: {src['title']}\n{src['content']}")
        return "\n\n".join(context_parts)
