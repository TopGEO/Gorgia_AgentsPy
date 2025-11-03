from .clients import async_qdrant_client
from qdrant_client.http import models
from loguru import logger


async def delete_collection(collection_name: str):
    if not await async_qdrant_client.collection_exists(collection_name):
        logger.info(f"Cannot delete collection {collection_name} because it does not exist")
        return
    await async_qdrant_client.delete_collection(collection_name=collection_name)
    logger.info(f"Collection {collection_name} deleted")


async def create_hybrid_collection(collection_name: str, vector_size: int):
    logger.info(f"Creating hybrid collection {collection_name} with vector size {vector_size}")
    if not await async_qdrant_client.collection_exists(collection_name):
        logger.info(f"Creating hybrid collection {collection_name} with vector size {vector_size}")
        await async_qdrant_client.create_collection(
            collection_name, 
            vectors_config={
                "dense": models.VectorParams(size=vector_size, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
              "bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)
            }
        )

