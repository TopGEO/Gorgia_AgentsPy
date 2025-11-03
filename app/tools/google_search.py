from langchain_core.tools import tool
from duckduckgo_search import DDGS

@tool
def google_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for information not available in the product catalog.
    Use for general queries, comparisons, reviews, or external information.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
    """
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        
        if not results:
            return "No search results found."
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "title": result.get("title"),
                "snippet": result.get("body"),
                "link": result.get("href")
            })
        
        return str(formatted_results)
    except Exception as e:
        return f"Search failed: {str(e)}"