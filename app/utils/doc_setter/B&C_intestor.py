import asyncio
from catalog import run_catalog_pipeline, run_brands_pipeline
from loguru import logger

COLLECTION_NAME = "gorgia_catalog_hybrid"

async def run_all_pipelines():
    logger.info("Starting both pipelines concurrently...")

    catalog_task = asyncio.create_task(run_catalog_pipeline())
    brands_task = asyncio.create_task(run_brands_pipeline(collection_name=COLLECTION_NAME))

    await asyncio.gather(catalog_task, brands_task)

    logger.info("All pipelines completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_all_pipelines())