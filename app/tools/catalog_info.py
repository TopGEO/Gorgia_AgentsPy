from langchain_core.tools import tool
from ..db import vector_store
from pydantic import Field
from .products.rerank import rerank_docs

@tool
async def get_catalog_info(query: str = Field(description="A clear, specific search query describing the products to find. Only English query is accepted.")) -> str:
    """Get full catalog information based on a search query."""
    print(f'Catalog - searching catalog for query: 🔸{query}🔸')
    try:
        results = await vector_store.dense_search(query=query, k=2, collection="zoommer_catalog_hybrid")
        # print(f"Catalog Results Count (before reranking): {len(results)}")
        
        # reranked_results = rerank_docs(results, query)
        # print(f"Catalog Results Count (after reranking): {len(reranked_results)}")
        # print(f"Reranked Results: {reranked_results}")
        
        return str(results)
    except Exception as e:
        print(f"Error in get_catalog_info: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return f"Error searching catalog: {str(e)}"