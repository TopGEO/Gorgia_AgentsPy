import asyncio
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .txt_document_embedder import read_txt_files_add_filename_metadata_and_return_chunks
from .embedder import EmbeddingCreator, PointInserter
from .collection import create_hybrid_collection
import uuid
import google.generativeai as genai
from loguru import logger


async def embed_text_documents_from_path(
    base_path: str,
    collection_name: str,
    model: str = 'gemini-embedding-001',
    vector_size: int = 3072,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    max_batch_size: int = 100,
    batch_insert_size: int = 100
):
    embedder = EmbeddingCreator(model=model, vector_size=vector_size)
    point_inserter = PointInserter(collection_name=collection_name, max_retries=2)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n\n\n", "\n\n\n", "\n\n", "\n", ". ", " ", ""],
    )

    logger.info(f"Reading text documents from {base_path}")
    chunks = read_txt_files_add_filename_metadata_and_return_chunks(
        base_path=base_path,
        text_splitter=text_splitter
    )

    if not chunks:
        logger.warning("No chunks found to embed")
        return 0

    for chunk in chunks:
        chunk["metadata"]["id"] = str(uuid.uuid4())

    texts = [chunk["content"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    logger.info(f"Creating dense embeddings for {len(texts)} chunks")
    dense_embeddings = await embedder.create_dense_embeddings_batch(
        texts=texts,
        max_batch_size=max_batch_size
    )

    logger.info(f"Creating sparse embeddings for {len(texts)} chunks")
    sparse_embeddings = await embedder.create_sparse_embeddings_batch(texts=texts)

    logger.info("Creating Qdrant points")
    points = point_inserter.create_qdrant_points_with_sparse_and_dense_vectors(
        metadatas=metadatas,
        dense_embeddings=dense_embeddings,
        sparse_embeddings=sparse_embeddings
    )

    logger.info(f"Inserting {len(points)} points into Qdrant")
    total_inserted = await point_inserter.insert_points_with_adaptive_batch_size(
        points=points,
        batch_size=batch_insert_size
    )

    logger.info(f"Successfully inserted {total_inserted} document chunks")
    return total_inserted


async def run_doc_setter_pipeline(
    collection_name: str = 'zoommer_docs_hybrid',
    docs_path: str = './docs',
    api_key: str = None,
    model: str = 'gemini-embedding-001',
    vector_size: int = 3072,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    max_batch_size: int = 100,
    batch_insert_size: int = 100,
    recreate_collection: bool = False
):
    if api_key:
        genai.configure(api_key=api_key)
    
    logger.info(f"Starting document setter pipeline with collection: {collection_name}")
    
    await create_hybrid_collection(collection_name, vector_size)
    
    total_inserted = await embed_text_documents_from_path(
        base_path=docs_path,
        collection_name=collection_name,
        model=model,
        vector_size=vector_size,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        max_batch_size=max_batch_size,
        batch_insert_size=batch_insert_size
    )
    
    logger.info(f"Document setter pipeline completed. Total inserted: {total_inserted}")
    return total_inserted

