from mistralai import Mistral
from app.core.config import Settings


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        self.model = settings.MISTRAL_EMBEDDING_MODEL

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            inputs=text
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=self.model,
            inputs=texts
        )
        return [item.embedding for item in response.data]
