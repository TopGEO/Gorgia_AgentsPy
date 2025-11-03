import json
import hashlib
from .embedder import EmbeddingCreator, PointInserter
from loguru import logger

VECTOR_SIZE = 3072


def _read_json_file(file_path: str) -> list[dict]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data


def _map_brand_to_text(brand_json: dict) -> str:
    return brand_json.get('text', '')


def _add_id_to_metadata(metadata: dict) -> dict:
    category = metadata.get('category', '')
    subcategory = metadata.get('subcategory', '')
    brands = ','.join(metadata.get('brands', []))
    text = metadata.get('text', '')
    
    content_to_hash = f"{category}|{subcategory}|{brands}|{text}"
    hash_value = hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()[:16]
    hash_int = int(hash_value, 16)
    metadata['id'] = hash_int
    return metadata


async def _process_brands_data(brand_json_list: list[dict], max_batch_size: int, collection_name: str):
    embedding_creator = EmbeddingCreator('gemini-embedding-001', VECTOR_SIZE)
    point_inserter = PointInserter(collection_name=collection_name, max_retries=2)
    
    brand_json_list = [_add_id_to_metadata(item) for item in brand_json_list]
    
    texts = [_map_brand_to_text(item) for item in brand_json_list]
    logger.info(f"Created {len(texts)} brand texts for embedding")
    logger.info(f"Sample brand text: {texts[0]}")
    
    dense_embeddings = await embedding_creator.create_dense_embeddings_batch(texts, max_batch_size)
    sparse_embeddings = await embedding_creator.create_sparse_embeddings_batch(texts)
    logger.info(f"Created {len(dense_embeddings)} brand dense embeddings and {len(sparse_embeddings)} sparse embeddings")
    
    points = point_inserter.create_qdrant_points_with_sparse_and_dense_vectors(
        metadatas=brand_json_list,
        dense_embeddings=dense_embeddings,
        sparse_embeddings=sparse_embeddings
    )
    logger.info(f"Created {len(points)} brand points to insert")
    
    total_inserted = await point_inserter.insert_points_with_adaptive_batch_size(points, batch_size=10)
    logger.info(f"Total brand points inserted: {total_inserted}")
    return total_inserted


async def run_brands_pipeline(file_path: str = 'brand_summary.json', max_batch_size: int = 20, collection_name: str = 'zoommer_catalog_hybrid'):
    brand_json_list = _read_json_file(file_path)
    await _process_brands_data(brand_json_list, max_batch_size, collection_name)

