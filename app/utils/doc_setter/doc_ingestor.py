import asyncio
import os
from doc_setter.pipeline import run_doc_setter_pipeline
from loguru import logger

if __name__ == "__main__":
    docs_path = os.path.join(os.path.dirname(__file__), 'doc_setter', 'docs')
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(run_doc_setter_pipeline(
        collection_name="zoommer_docs_hybrid",
        docs_path=docs_path,
        api_key=api_key,
        model='gemini-embedding-001',
        vector_size=3072,
        chunk_size=500,
        chunk_overlap=200,
        max_batch_size=100,
        batch_insert_size=100,
        recreate_collection=True
    ))

