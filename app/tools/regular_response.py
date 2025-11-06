from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

class RespondToUserInput(BaseModel):
    message: str = Field(description="Very concise final response message to send to the user")
    product_ids_to_show: Optional[list[str]] = Field(
        default=None,
        description="Optional list of product IDs to display to the user"
    )

@tool(args_schema=RespondToUserInput)
async def respond_to_user(message: str, product_ids_to_show: Optional[list[str]] = None) -> str:
    """
    **FINAL TOOL** - Call this to send your response to the user.

    Use this when:
    - User sends greetings, thanks, or casual chat
    - You have gathered enough information from other tools
    - You're ready to provide a final answer based on tool results
    - After completing all necessary tool calls

    Arguments:
    - message: Your complete response to the user (formatted, natural language)
    - product_ids_to_show: Optional list of product IDs referenced in your message

    This is the ONLY way to send a message to the user - you MUST call this tool to respond.
    """
    return message, product_ids_to_show