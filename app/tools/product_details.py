from typing import List
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from ..db import vector_store
from ..models.product import Product

class GetProductDetailsInput(BaseModel):
    product_id: List[str] = Field(description="List of product IDs to get detailed information about.")
    # need_location: bool = Field(default=False, description="Whether to include store location information.")

@tool(args_schema=GetProductDetailsInput)
async def get_product_details(product_id: List[str], ) -> str:
    """
    Get detailed information about one or more products.
    
    IMPORTANT: This tool supports batch lookups. Do NOT make separate calls for each product — it is inefficient and slow. When multiple products details are needed, collect all their IDs and pass them together in one call.
    
    Args:
        product_id: List of product IDs.
    
    Returns:
        Formatted product details.
    """
    try:
        product_id = [int(pid) for pid in product_id]
        print(f"Searching for IDs: {product_id}")
        results = await vector_store.search_by_id(ids=product_id, collection="gorgia_products_hybrid")
        cleaned_results = []
        for item in results:
            try:
                product = Product.model_validate(item.payload)
                cleaned_results.append(product.to_detailed_search_dict())
            except Exception as e:
                print(f"Failed to parse product {item.payload.get('id', 'unknown')}: {e}")
                cleaned_results.append(item.payload)

        return str(cleaned_results)
    
    except Exception as e:
        return f"Search failed: {str(e)}"