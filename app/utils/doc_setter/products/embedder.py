from abc import ABC
from .clients import async_qdrant_client
from qdrant_client.models import PointStruct
import asyncio
from loguru import logger
from fastembed import SparseTextEmbedding
import google.generativeai as genai

bm25_embedding_model = SparseTextEmbedding("Qdrant/bm25")


class EmbeddingCreator(ABC):
    def __init__(self, model: str, vector_size: int):
        self.model = model
        self.vector_size = vector_size

    async def _gemini_create_dense_embeddings_batch(self, texts: list[str]):
        result = await genai.embed_content_async(
            model=self.model,
            content=texts,
            output_dimensionality=self.vector_size
        )
        return result['embedding']
    
    async def create_dense_embeddings_batch(self, texts: list[str], max_batch_size: int):
        if not texts:
            return []
        all_embeddings = []
        batch_size_options = [max_batch_size, max_batch_size * 8 // 10, max_batch_size * 4 // 10, max_batch_size * 2 // 10, 5, 2, 1]
        current_batch_size_index = 0
        
        created_up_to = 0
        
        while created_up_to < len(texts):
            current_batch_size = batch_size_options[current_batch_size_index]
            batch_end = min(created_up_to + current_batch_size, len(texts))
            current_batch = texts[created_up_to:batch_end]
            
            try:
                batch_embeddings = await self._gemini_create_dense_embeddings_batch(current_batch)
                all_embeddings.extend(batch_embeddings)
                created_up_to = batch_end
                logger.info(f"Created dense embeddings for {len(all_embeddings)} texts out of {len(texts)}")
                
                if current_batch_size_index > 0:
                    current_batch_size_index -= 1
                                    
            except Exception as e:
                logger.error(f"Error embedding products {created_up_to} - {batch_end}: {str(e)[:100]}...")
                
                if current_batch_size_index >= len(batch_size_options) - 1:
                    logger.error(f"Failed even with batch size 1. inserting None embeddings:")
                    all_embeddings.extend([None] * len(current_batch))
                    created_up_to = batch_end
                    current_batch_size_index = 0
                else:
                    current_batch_size_index += 1
                    logger.info(f"Reducing batch size to {batch_size_options[current_batch_size_index]}")

                    await asyncio.sleep(2)
        
        return all_embeddings
    
    async def create_sparse_embeddings_batch(self, texts: list[str]):
        return list(bm25_embedding_model.embed(text.strip() for text in texts))


class PointInserter:
    def __init__(self, collection_name: str, max_retries: int = 2):
        self.max_retries = max_retries
        self.collection_name = collection_name
    
    async def insert_points_with_adaptive_batch_size(self, points: list[PointStruct], batch_size: int):
        if not points:
            return
        
        total_inserted = 0
        batch_size_options = [batch_size, batch_size * 8 // 10, batch_size * 4 // 10, batch_size * 2 // 10, 5, 2, 1]
        current_batch_size_index = 0
        created_up_to = 0

        while created_up_to < len(points):
            current_batch_size = batch_size_options[current_batch_size_index]
            batch_end = min(created_up_to + current_batch_size, len(points))
            current_points = points[created_up_to:batch_end]

            if not current_points:
                logger.info("No valid points to upsert for this batch; skipping upsert.")
                created_up_to = batch_end
                if current_batch_size_index > 0:
                    current_batch_size_index -= 1
                await asyncio.sleep(0.05)
                continue

            try:
                await self._insert_points_in_qdrant(current_points)
                total_inserted += len(current_points)
                logger.info(f"Inserted {len(current_points)} points into Qdrant out of {len(points)}")
                created_up_to = batch_end
                if current_batch_size_index > 0:
                    current_batch_size_index -= 1
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(
                    f"Error inserting points for range {created_up_to}-{batch_end} with batch size {current_batch_size}: {e}"
                )
                if current_batch_size_index >= len(batch_size_options) - 1:
                    logger.error(
                        "Failed to insert even with smallest batch size; skipping these items and continuing."
                    )
                    created_up_to = batch_end
                    current_batch_size_index = 0
                    await asyncio.sleep(0.2)
                else:
                    current_batch_size_index += 1
                    logger.info(
                        f"Reducing insert batch size to {batch_size_options[current_batch_size_index]} and retrying."
                    )
                    await asyncio.sleep(0.2)
        return total_inserted
    
    
    async def _insert_points_in_qdrant(self, points: list[PointStruct]):
        if not points:
            logger.info("Received empty points list; skipping Qdrant upsert.")
            return
        for attempt in range(self.max_retries):
            try:
                await async_qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                    wait=True
                )
                return
            except Exception as e:
                logger.error(
                    f"Error inserting points on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                await asyncio.sleep(2 ** attempt)
        logger.error(f"Failed to insert points after {self.max_retries} attempts")
        raise Exception(f"Failed to insert points after {self.max_retries} attempts")


    def create_qdrant_points_with_sparse_and_dense_vectors(self, metadatas: list[dict], dense_embeddings: list[list[float] | None], sparse_embeddings: list[list[float] | None]) -> list[PointStruct]:
        return [self._create_qdrant_point_with_sparse_and_dense_vectors(product_metadata, dense_embedding, sparse_embedding) for product_metadata, dense_embedding, sparse_embedding in zip(metadatas, dense_embeddings, sparse_embeddings) if dense_embedding is not None and sparse_embedding is not None]

    def _create_qdrant_point_with_sparse_and_dense_vectors(self, metadata: dict, dense_embedding: list[float] | None, sparse_embedding: list[float] | None) -> PointStruct:
        if dense_embedding is None or sparse_embedding is None:
            return None
        
        point = PointStruct(
            id=metadata['id'],
            vector={
                'dense': dense_embedding,
                'bm25': sparse_embedding.as_object()
            },
            payload={'metadata': metadata}
        )
        return point

