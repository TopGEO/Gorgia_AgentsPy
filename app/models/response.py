from pydantic import BaseModel, Field
from typing import List, Optional


class ResponseOutput(BaseModel):
    """Structured output for final response"""
    message: str = Field(description="The natural language response to the user")
    product_ids_to_show: Optional[List[int]] = Field(
        default=None,
        description="List of product IDs to highlight in the response. Only include IDs that are directly relevant to show the user."
    )


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    session_id: Optional[str] = None
    browser_id: Optional[str] = None
    image_urls: Optional[List[str]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    session_id: str
    payload: Optional[dict] = None
    tool_call: Optional[str] = None