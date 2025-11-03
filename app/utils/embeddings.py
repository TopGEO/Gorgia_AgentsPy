from google import genai
from google.genai import types
from ..config import settings
import asyncio

class GeminiEmbeddings:
    def __init__(self, model: str, dimensions: int):
        self.model = model
        self.dimensions = dimensions
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def embed_query(self, text: str) -> list[float]:
        """Async wrapper for embedding a single query."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.models.embed_content(
                model=self.model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
            )
        )
        return result.embeddings[0].values

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Async wrapper for embedding multiple documents."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.models.embed_content(
                model=self.model,
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
            )
        )
        return [embedding.values for embedding in result.embeddings]

def get_embeddings():
    embeddings = GeminiEmbeddings(
        model=settings.embedding_model,
        dimensions=settings.vector_dimension
    )
    return embeddings