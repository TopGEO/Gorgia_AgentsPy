from langchain_core.tools import tool
from ..db import vector_store
from pydantic import BaseModel, Field

class StorePolicyInput(BaseModel):
    query: str = Field(description="Always return a clear, specific query about company information you need. Only English query is accepted.",)

@tool(args_schema=StorePolicyInput)
async def get_store_policy(query: str) -> str:
    """
    Tool to get any information about company profile profile, policies, services, item return, delivery or general company details.
    """
    print(f"[Docs] - searching company information for query: 🔸{query}🔸")
    try:
        results = await vector_store.hybrid_search(query=query, k=7, collection="zoommer_docs_hybrid")
        print(f"Found {len(results)} results from vector store")
        
        return str([result.payload for result in results])
    
    except Exception as e:
        return f"Search failed: {str(e)}"