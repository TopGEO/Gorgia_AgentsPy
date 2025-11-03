from .embedder import EmbeddingCreator, PointInserter
from .mapper import ZoommerMapper
from .fetcher import ZoommerFetcher
from .collection import create_hybrid_collection, delete_collection
from loguru import logger


class ProductPipelineConfig:
    def __init__(
        self, 
        embedding_model: str, 
        vector_size: int, 
        collection_name: str, 
        fetcher_class,
        bulk_fetch_size: int, 
        batch_create_embeddings_size: int, 
        batch_insert_points_size: int,
        fetcher_kwargs: dict = None
    ):
        self.embedding_model = embedding_model
        self.vector_size = vector_size
        self.collection_name = collection_name
        self.fetcher_class = fetcher_class
        self.bulk_fetch_size = bulk_fetch_size
        self.batch_create_embeddings_size = batch_create_embeddings_size
        self.batch_insert_points_size = batch_insert_points_size
        self.fetcher_kwargs = fetcher_kwargs or {}


class ProductEmbedderPipeline:
    def __init__(self, config: ProductPipelineConfig):
        self.collection_name = config.collection_name
        self.fetcher_class = config.fetcher_class
        self.embedder = EmbeddingCreator(
            model=config.embedding_model,
            vector_size=config.vector_size
        )
        self.inserter = PointInserter(collection_name=config.collection_name)
        self.mapper = ZoommerMapper()
        self.config = config
        self.to_be_inserted = [0]

    async def _set_to_be_inserted(self, to_be_inserted: int):
        self.to_be_inserted[0] = to_be_inserted
        logger.info(f"Total products to be inserted: {to_be_inserted}")

    async def run_hybrid(self) -> bool:
        total_inserted = 0
        total_processed = 0

        async with self.fetcher_class(set_total_products_found_callback=self._set_to_be_inserted, **self.config.fetcher_kwargs) as fetcher:
            async for product_batch in fetcher.iterate_over_bulk_product_details(1, self.config.bulk_fetch_size):
                logger.info(f"Processing batch of {len(product_batch)} products")

                product_metadatas = self.mapper.map_fetched_details_to_product_metadatas(product_batch)

                dense_texts = self.mapper.map_metadatas_to_embedding_texts(product_metadatas)
                sparse_texts = self.mapper.map_metadatas_to_sparse_embedding_texts(product_metadatas)

                logger.info(f"Generating dense embeddings for {len(dense_texts)} product texts")
                dense_embeddings = await self.embedder.create_dense_embeddings_batch(
                    dense_texts,
                    self.config.batch_create_embeddings_size
                )

                logger.info(f"Generating sparse embeddings for {len(sparse_texts)} product texts")
                sparse_embeddings = await self.embedder.create_sparse_embeddings_batch(sparse_texts)

                logger.info(f"Generated {len(dense_embeddings)} dense embeddings")
                logger.info(f"Generated {len(sparse_embeddings)} sparse embeddings")

                logger.info(f"Inserting {len(product_metadatas)} product models into qdrant")
                points = self.inserter.create_qdrant_points_with_sparse_and_dense_vectors(
                    product_metadatas,
                    dense_embeddings,
                    sparse_embeddings
                )

                inserted = await self.inserter.insert_points_with_adaptive_batch_size(
                    points,
                    self.config.batch_insert_points_size
                )

                logger.info(f"Inserted {inserted} product models into qdrant")
                total_processed += len(product_batch)
                total_inserted += inserted
                logger.info(f"Total processed: {total_processed}, Total inserted: {total_inserted}")

        logger.info(f"Finished fetching. Total inserted: {total_inserted}/{self.to_be_inserted[0]}")
        if self.to_be_inserted[0] > 0 and total_inserted + 100 < self.to_be_inserted[0]:
            logger.warning(f"Total inserted is less than expected by 100+. Total inserted: {total_inserted}/{self.to_be_inserted[0]}")
            return False
        
        return True


async def run_products_pipeline(
    collection_name: str = "zoommer_products_hybrid",
    model: str = "gemini-embedding-001",
    vector_size: int = 3072,
    bulk_fetch_size: int = 100,
    batch_create_embeddings_size: int = 100,
    batch_insert_points_size: int = 100,
    recreate_collection: bool = False
):
    logger.info(f"Starting Zoommer products pipeline with collection: {collection_name}")
    
    if recreate_collection:
        await delete_collection(collection_name=collection_name)
    
    await create_hybrid_collection(collection_name=collection_name, vector_size=vector_size)
    
    config = ProductPipelineConfig(
        embedding_model=model,
        vector_size=vector_size,
        collection_name=collection_name,
        fetcher_class=ZoommerFetcher,
        bulk_fetch_size=bulk_fetch_size,
        batch_create_embeddings_size=batch_create_embeddings_size,
        batch_insert_points_size=batch_insert_points_size
    )
    
    pipeline = ProductEmbedderPipeline(config)
    success = await pipeline.run_hybrid()
    
    logger.info(f"Zoommer products pipeline completed. Success: {success}")
    return success

