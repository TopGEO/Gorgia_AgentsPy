from typing import Any
from .clients import async_qdrant_client
from qdrant_client.http.models.models import Prefetch, FusionQuery, Fusion
from qdrant_client.models import SparseVector
from fastembed import SparseTextEmbedding
import google.generativeai as genai

bm25_embedding_model = SparseTextEmbedding("Qdrant/bm25")


async def dense_search(query: str, limit: int, collection_name: str) -> list[dict[str, Any]]:
    embedding_response = await genai.embed_content_async(
        model="gemini-embedding-001",
        content=query,
        output_dimensionality=3072
    )

    results = await async_qdrant_client.query_points(
        collection_name=collection_name,
        query=embedding_response['embedding'],
        using="dense",
        limit=limit
    )
    metadata = [result.payload['metadata'] for result in results.points]
    return metadata


async def lexical_search(query: str, limit: int, collection_name: str) -> list[dict[str, Any]]:
    embedding_response = list(bm25_embedding_model.embed(query))
    embeddings = list(embedding_response)
    embedding = embeddings[0]
    
    sparse_vector = SparseVector(
        indices=embedding.indices.tolist(),
        values=embedding.values.tolist()
    )
    
    results = await async_qdrant_client.query_points(
        collection_name=collection_name,
        query=sparse_vector,
        using="bm25",
        limit=limit
    )
    
    metadata = [result.payload['metadata'] for result in results.points]
    return metadata


async def hybrid_search(query: str, limit: int, collection_name: str) -> list[dict[str, Any]]:
    embedding_response = await genai.embed_content_async(
        model="gemini-embedding-001",
        content=query,
        output_dimensionality=3072
    )
    query_vector = embedding_response['embedding']
    sparse_vector = list(bm25_embedding_model.embed([query]))[0]
    
    results = await async_qdrant_client.query_points(
        collection_name=collection_name,
        prefetch=[
            Prefetch(
                query=query_vector,
                using="dense",
                limit=limit*10
            ),
            Prefetch(
                query=SparseVector(
                    indices=sparse_vector.indices.tolist(),
                    values=sparse_vector.values.tolist()
                ),
                using="bm25",
                limit=limit*10
            )
        ],
        query=FusionQuery(
            fusion=Fusion.DBSF
        ),
        limit=limit
    )

    points = results.points
    metadata = [point.payload['metadata'] for point in points]
    return metadata