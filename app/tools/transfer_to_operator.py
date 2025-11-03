from langchain_core.tools import tool
from pydantic import BaseModel, Field

class TransferToOperatorInput(BaseModel):
    reason: str = Field(description="The reason why the conversation is being transferred to a human operator")

@tool(args_schema=TransferToOperatorInput)
def transfer_to_operator(reason: str) -> str:
    """
    Transfer the conversation to a human operator. This STOPS the AI loop immediately.
    
    Use this when:
    - The user explicitly requests to speak with a human/agent/operator
    - The issue is too complex or outside your capabilities
    - The user is frustrated or needs human assistance
    
    Arguments:
    - reason: A clear explanation of why the transfer is needed
    """
    return f"User has finished speaking with human operator. Now you can continue the conversation."