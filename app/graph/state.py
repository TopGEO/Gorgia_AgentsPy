from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    product_ids_to_show: Optional[List[int]]
    tool_call: Optional[str]
    order_status_transfer: Optional[Dict[str, Any]]