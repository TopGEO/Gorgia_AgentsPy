from google import genai
from google.genai import types
from ..config import settings

class GeminiEmbeddings:
    def __init__(self, model: str, dimensions: int):
        self.model = model
        self.dimensions = dimensions
        self.client = genai.Client(api_key=settings.gemini_api_key)
    
    def embed_query(self, text: str) -> list[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
        )
        return result.embeddings[0].values
    
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
        )
        return [embedding.values for embedding in result.embeddings]

def get_embeddings():
    embeddings = GeminiEmbeddings(
        model=settings.embedding_model,
        dimensions=settings.vector_dimension
    )
    return embeddings