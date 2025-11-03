from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import SparseVector, NamedSparseVector, Prefetch, SparseVector, Fusion, FusionQuery
from typing import List, Dict, Any, Optional
from ..config import settings
from ..utils import embeddings
from fastembed import SparseTextEmbedding
from dataclasses import dataclass
import asyncio

@dataclass
class SearchResult:
    """Unified search result structure for all search methods."""
    id: str
    score: float
    payload: Dict[str, Any]
    page_content: str

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key
        )
        self.async_client = AsyncQdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key
        )
        self.embeddings = embeddings.get_embeddings()
        self.bm25_model = SparseTextEmbedding("Qdrant/bm25")
        self.collection_name = settings.qdrant_collection
        self._collection_cache = {}  # Cache collection configurations

    def _has_named_vectors(self, collection: str) -> bool:
        """Check if collection has named vectors (dense/bm25) or unnamed vectors."""
        if collection not in self._collection_cache:
            try:
                info = self.client.get_collection(collection)
                has_named = isinstance(info.config.params.vectors, dict)
                self._collection_cache[collection] = has_named
            except Exception:
                self._collection_cache[collection] = False
        return self._collection_cache[collection]

    async def dense_search(
        self,
        query: str,
        k: int = 7,
        filter: dict = None,
        collection: str = None,
    ) -> List[SearchResult]:
        """
        Perform dense vector search using semantic embeddings.
        Best for semantic similarity and understanding context.

        Works with both:
        - Named vectors (new hybrid collections with "dense" vector)
        - Unnamed vectors (legacy collections)
        """
        loop = asyncio.get_event_loop()
        query_vector = await loop.run_in_executor(
            None,
            lambda: self.embeddings.embed_query(query)
        )

        collection = collection or self.collection_name
        if collection and self._has_named_vectors(collection):
            vector_param = ("dense", query_vector)
        else:
            vector_param = query_vector

        search_result = await self.async_client.search(
            collection_name=collection,
            query_vector=vector_param,
            limit=k,
            query_filter=filter,
        )
        
        results = []
        for point in search_result:
            m = point.payload.get("metadata", {})
            pc = self._build_page_content(m)
            results.append(SearchResult(
                id=str(point.id),
                score=float(point.score) if point.score else 0.0,
                payload=m,
                page_content=pc
            ))
        return results

    async def lexical_search(
        self,
        query: str,
        k: int = 7,
        filter: dict = None,
        collection: str = None,
    ) -> List[SearchResult]:
        loop = asyncio.get_event_loop()
        sparse_embedding = await loop.run_in_executor(
            None,
            lambda: list(self.bm25_model.embed([query.strip()]))[0]
        )

        sparse_vector = NamedSparseVector(
            name="bm25",
            vector=SparseVector(
                indices=sparse_embedding.indices.tolist(),
                values=sparse_embedding.values.tolist()
            )
        )

        collection = collection or self.collection_name
        search_result = await self.async_client.search(
            collection_name=collection,
            query_vector=sparse_vector,
            limit=k,
            query_filter=filter,
        )
        
        results = []
        for point in search_result:
            m = point.payload.get("metadata", {})
            pc = self._build_page_content(m)
            results.append(SearchResult(
                id=str(point.id),
                score=float(point.score) if point.score else 0.0,
                payload=m,
                page_content=pc
            ))
        return results

    async def _create_sparse_embedding(self, query: str):
        """Helper to create sparse embedding asynchronously."""
        loop = asyncio.get_event_loop()
        sparse_embedding = await loop.run_in_executor(
            None,
            lambda: list(self.bm25_model.embed([query.strip()]))[0]
        )
        return SparseVector(
            indices=sparse_embedding.indices.tolist(),
            values=sparse_embedding.values.tolist()
        )

    def _build_page_content(self, metadata: Dict[str, Any]) -> str:
        """Build page content from metadata."""
        return metadata.get("page_content", "") or metadata.get("title", "") or ""

    async def hybrid_search(
        self,
        query: str,
        k: int = 7,
        filter: Optional[Dict] = None,
        collection: str = None,
    ) -> List[SearchResult]:
        """
        Hybrid search combining dense (semantic) and sparse (BM25) search with RRF.
        Uses Qdrant's native RRF fusion for optimal performance.
        """
        try:
            print(f"Hybrid search for: {query}")

            loop = asyncio.get_event_loop()
            dense_vector = await loop.run_in_executor(
                None,
                lambda: self.embeddings.embed_query(query)
            )
            sparse_vector = await self._create_sparse_embedding(query)

            collection = collection or self.collection_name

            search_result = await self.async_client.query_points(
                collection_name=collection,
                prefetch=[
                    Prefetch(query=sparse_vector, using="bm25", limit=k*2),
                    Prefetch(query=dense_vector, using="dense", limit=k*2)
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=k,
                query_filter=filter
            )

            results = []
            for point in search_result.points:
                m = point.payload.get("metadata", {})
                pc = self._build_page_content(m)
                results.append(SearchResult(
                    id=str(point.id),
                    score=float(point.score) if point.score else 0.0,
                    payload=m,
                    page_content=pc
                ))

            print(f"Hybrid search found {len(results)} results")
            return results

        except Exception as e:
            print(f"Hybrid search failed: {e}")
            return await self.dense_search(query, k, filter, collection)
    
    async def search_by_id(self, ids: List[int], collection: str = None) -> List[SearchResult]:
        from qdrant_client.models import Filter, FieldCondition, MatchAny
        
        collection = collection or self.collection_name
        if not ids:
            return []

        results = []
        batch_size = 100

        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            try:
                filter_condition = Filter(
                    must=[
                        FieldCondition(
                            key="metadata.id",
                            match=MatchAny(any=batch_ids)
                        )
                    ]
                )

                scroll_result = await self.async_client.scroll(
                    collection_name=collection,
                    scroll_filter=filter_condition,
                    limit=len(batch_ids),
                    with_payload=True,
                    with_vectors=False,
                )
                
                points = scroll_result[0]
                print(f"Found {len(points)} products")

                for point in points:
                    m = point.payload.get("metadata", {})
                    if not m:
                        print(f"Point {point.id} has no metadata!")
                        continue
                    pc = self._build_page_content(m)
                    results.append(SearchResult(
                        id=str(point.id),
                        score=1.0,
                        payload=m,
                        page_content=pc
                    ))
                        
            except Exception as e:
                print(f"Error searching batch: {e}")
                import traceback
                traceback.print_exc()
                continue

        print(f"Total results: {len(results)} out of {len(ids)} requested")
        return results


vector_store = VectorStore()