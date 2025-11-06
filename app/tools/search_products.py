from langchain_core.tools import tool
from pydantic import BaseModel, Field
from ..db import vector_store
from .products.extractors import extract_product_payload
from .products.rerank import rerank_products
from ..models.product import Product
from typing import Optional

class PriceRange(BaseModel):
    min_price: Optional[float] = Field(None, description="Minimum price (inclusive)")
    max_price: Optional[float] = Field(None, description="Maximum price (inclusive)")
    
    def to_qdrant_range(self) -> dict:
        range_params = {}
        if self.min_price is not None:
            range_params["gte"] = self.min_price
        if self.max_price is not None:
            range_params["lte"] = self.max_price
        return range_params


class SearchFilters(BaseModel):
    price_range: Optional[PriceRange] = Field(None, description="Price range filter")
    
    def to_qdrant_filters(self) -> Optional[dict]:
        conditions = []
        
        if self.price_range:
            range_params = self.price_range.to_qdrant_range()
            if range_params:
                conditions.append({
                    "key": "metadata.price",
                    "range": range_params
                })
        
        if not conditions:
            return None
            
        return {"must": conditions}

class SearchProductsInput(BaseModel):
    query: str = Field(
        description="A clear, specific search query describing the items to find. Any language query is accepted, but for better results, use user language query."
    )
    filters: Optional[SearchFilters] = Field(
        None,
        description="Use price_range to filter by minimum and maximum price whenever the user query contains price range."
    )
    need_location: bool = Field(
        False,
        description="Set to True only when product availability in store locations is required. Otherwise, keep it False."
    )

@tool(args_schema=SearchProductsInput)
async def search_products(query: str, filters: Optional[SearchFilters] = None, need_location: bool = False) -> str:
    """
    Tool to get relevant products of the query.
    Use this tool when the user asks about products, wants to browse items.
    """
    print(f'[Products] - searching products for query: 🔸{query}🔸')
    if need_location:
        print("⚠️ Location information needed for this search")
    qdrant_filter = filters.to_qdrant_filters() if filters else None
    if qdrant_filter: print(f"Applying filters: {qdrant_filter}")
    try:
        results = await vector_store.hybrid_search(query, k=20, filter=qdrant_filter)
        print(f"Found {len(results)} hybrid search results")

        cleaned = []
        for i in results:
            try:
                product = Product.from_search_result(i)
                cleaned.append(product.to_search_result_dict(need_location=need_location))
            except Exception as e:
                print(f"Failed to parse product {i.payload.get('id','unknown')}: {e}")
                cleaned.append(i.payload)
        
        return str(cleaned)
    except Exception as e:
        return f"Search failed: {e}"