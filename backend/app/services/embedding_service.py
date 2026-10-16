from mistralai import Mistral
from app.core.config import Settings
from app.services.mistral_resilience import call_with_retry


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        self.model = settings.MISTRAL_EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        # Transient 429s (rate limit / out of capacity) are retried inside;
        # persistent failures propagate to RetrievalService, which degrades
        # gracefully instead of failing the whole chat request.
        response = call_with_retry(
            lambda: self.client.embeddings.create(
                model=self.model,
                inputs=text
            ),
            what="mistral embeddings",
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = call_with_retry(
            lambda: self.client.embeddings.create(
                model=self.model,
                inputs=texts
            ),
            what="mistral embeddings (batch)",
        )
        return [item.embedding for item in response.data]
