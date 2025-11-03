import asyncio
from products import run_products_pipeline

if __name__ == "__main__":
    asyncio.run(run_products_pipeline(
        collection_name="gorgia_products_hybrid",
        bulk_fetch_size=100,
        batch_create_embeddings_size=50,
        batch_insert_points_size=50,
        recreate_collection=True
    ))

