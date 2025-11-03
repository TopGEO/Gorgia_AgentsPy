import asyncio
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import agent_node, tool_node, extract_final_response, should_continue

def should_continue_after_tools(state: AgentState) -> str:
    """Check if we should transfer to operator directly after tools"""
    if "order_status_transfer" in state and state["order_status_transfer"].get("should_transfer"):
        return "extract_response"
    return "agent"

async def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("extract_response", extract_final_response)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "extract_response": "extract_response"
        }
    )

    workflow.add_conditional_edges(
        "tools",
        should_continue_after_tools,
        {
            "agent": "agent",
            "extract_response": "extract_response"
        }
    )

    workflow.add_edge("extract_response", END)

    return workflow.compile()