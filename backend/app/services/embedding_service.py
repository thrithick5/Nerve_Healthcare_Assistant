from openai import OpenAI
from app.core.config import Settings
from app.services.mistral_resilience import call_with_retry


class EmbeddingService:
    def __init__(self, settings: Settings):
        # OpenRouter embeddings use the OpenAI-compatible API.
        self.client = OpenAI(
            api_key=settings.MISTRAL_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = settings.MISTRAL_EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        # Transient 429s (rate limit / out of capacity) are retried inside;
        # persistent failures propagate to RetrievalService, which degrades
        # gracefully instead of failing the whole chat request.
        response = call_with_retry(
            lambda: self.client.embeddings.create(
                model=self.model,
                input=text,
            ),
            what="openrouter embeddings",
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = call_with_retry(
            lambda: self.client.embeddings.create(
                model=self.model,
                input=texts,
            ),
            what="openrouter embeddings (batch)",
        )
        return [item.embedding for item in response.data]
