import json
import hashlib
from .embedder import EmbeddingCreator, PointInserter
from .collection import create_hybrid_collection, delete_collection
from loguru import logger
import aiofiles

COLLECTION_NAME = "gorgia_catalog_hybrid"
VECTOR_SIZE = 3072

embedding_creator = EmbeddingCreator('gemini-embedding-001', VECTOR_SIZE)
point_inserter = PointInserter(collection_name=COLLECTION_NAME, max_retries=2)


async def _read_json_file(file_path: str) -> list[dict]:
    async with aiofiles.open(file_path, 'r') as file:
        data = json.loads(await file.read())
    return data


def _map_product_to_text(product_catalog_json: dict) -> str:
    category_name = product_catalog_json.get('category_name', '')
    parent_category_name = product_catalog_json.get('parent_category_name', '')
    summary = product_catalog_json.get('summary', '')
    return f"{category_name}, {parent_category_name}\n{summary}"


def _add_id_to_metadata(metadata: dict) -> dict:
    summary = metadata.get('summary', '')
    category_name = metadata.get('category_name', '')
    parent_category_name = metadata.get('parent_category_name', '')
    
    content_to_hash = f"{category_name}|{parent_category_name}|{summary}"
    hash_value = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()[:16]
    hash_int = int(hash_value, 16)
    metadata['id'] = hash_int
    return metadata


async def _process_catalog_data(product_catalog_json_list: list[dict], max_batch_size: int):
    product_catalog_json_list = [_add_id_to_metadata(item) for item in product_catalog_json_list]
    await delete_collection(collection_name=COLLECTION_NAME)
    await create_hybrid_collection(collection_name=COLLECTION_NAME, vector_size=VECTOR_SIZE)
    
    texts = [_map_product_to_text(item) for item in product_catalog_json_list]
    logger.info(f"Created {len(texts)} texts for embedding")
    logger.info(f"Sample text: {texts[0]}")
    
    dense_embeddings = await embedding_creator.create_dense_embeddings_batch(texts, max_batch_size)
    sparse_embeddings = await embedding_creator.create_sparse_embeddings_batch(texts)
    logger.info(f"Created {len(dense_embeddings)} dense embeddings and {len(sparse_embeddings)} sparse embeddings")
    
    points = point_inserter.create_qdrant_points_with_sparse_and_dense_vectors(
        metadatas=product_catalog_json_list,
        dense_embeddings=dense_embeddings,
        sparse_embeddings=sparse_embeddings
    )
    logger.info(f"Created {len(points)} points to insert")
    
    total_inserted = await point_inserter.insert_points_with_adaptive_batch_size(points, batch_size=10)
    logger.info(f"Total points inserted: {total_inserted}")
    return total_inserted


async def run_catalog_pipeline(file_path: str = 'products.json', max_batch_size: int = 20):
    product_catalog_json_list = await _read_json_file(file_path)
    await _process_catalog_data(product_catalog_json_list, max_batch_size)

