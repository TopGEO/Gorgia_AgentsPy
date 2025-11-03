from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_xai import ChatXAI
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode

from ..config import settings, prompts
from ..utils.order_status_handler import OrderStatusHandler
from .utils import sanitize_messages_for_gemini
from ..tools import tools
from .state import AgentState


llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    temperature=settings.temperature,
    google_api_key=settings.gemini_api_key,
    # thinking_budget=24000
)


# llm = ChatXAI(
#     model="grok-4-fast-reasoning",
#     # temperature=settings.temperature,
#     xai_api_key=settings.xai_api_key
# )

llm_with_tools = llm.bind_tools(tools, tool_choice="any")


async def tool_node(state: AgentState) -> AgentState:
    """
    Enhanced tool node with special handling for check_order_status.
    
    When check_order_status returns a transfer code, this node:
    1. Processes the result through OrderStatusHandler
    2. Sets order_status_transfer flag if operator transfer is needed
    3. Bypasses AI for immediate transfer with predefined message
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {"messages": []}
    
    tool_messages = []
    order_transfer_info = None
    
    for tool_call in last_message.tool_calls:
        tool_name = (
            tool_call.get("name")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "name", None)
        )
        tool_call_id = (
            tool_call.get("id")
            if isinstance(tool_call, dict)
            else getattr(tool_call, "id", "")
        )
        
        if tool_name == "check_order_status":
            from ..tools.check_order_status import check_order_status
            
            args = (
                tool_call.get("args")
                if isinstance(tool_call, dict)
                else getattr(tool_call, "args", {})
            )
            order_id = args.get("order_id", "")
            
            result = await check_order_status.ainvoke({"order_id": order_id})
            transfer_msg, tool_msg, should_transfer = OrderStatusHandler.handle_order_status_result(
                result, tool_call_id
            )
            
            if should_transfer:
                order_transfer_info = {
                    "message": transfer_msg,
                    "should_transfer": True
                }
                tool_messages.append(ToolMessage(
                    content=f"Transferring to operator: {transfer_msg}",
                    tool_call_id=tool_call_id,
                    name="check_order_status"
                ))
            elif tool_msg:
                tool_messages.append(tool_msg)
        else:
            tool_result = await ToolNode(tools).ainvoke({"messages": [last_message]})
            if tool_result and "messages" in tool_result:
                tool_messages.extend(tool_result["messages"])
    
    new_state = {"messages": tool_messages}
    if order_transfer_info:
        new_state["order_status_transfer"] = order_transfer_info
    
    return new_state

async def agent_node(state: AgentState) -> AgentState:
    """Gemini decides which tools to call with tool_choice='any' (required)"""
    sanitized = sanitize_messages_for_gemini(state["messages"])
    messages = [SystemMessage(content=prompts.SYSTEM_PROMPT)] + sanitized
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def extract_final_response(state: AgentState) -> AgentState:
    """
    Extract final response from state.
    
    Priority handling:
    1. Order status transfer (immediate operator transfer with message)
    2. Manual transfer_to_operator tool call
    3. respond_to_user tool call with message/products
    4. Default fallback message
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if "order_status_transfer" in state and state["order_status_transfer"].get("should_transfer"):
        transfer_info = state["order_status_transfer"]
        ai_message = AIMessage(content=transfer_info["message"])
        return {
            "messages": [ai_message],
            "tool_call": "transfer_to_operator"
        }
    
    for msg in reversed(messages[-3:]):
        if hasattr(msg, 'type') and msg.type == "tool":
            tool_name = getattr(msg, 'name', None)
            if tool_name == "transfer_to_operator":
                ai_message = AIMessage(content="")
                return {
                    "messages": [ai_message],
                    "tool_call": "transfer_to_operator"
                }

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = (
                tool_call.get("name")
                if isinstance(tool_call, dict)
                else getattr(tool_call, "name", None)
            )

            if tool_name == "respond_to_user":
                args = (
                    tool_call.get("args")
                    if isinstance(tool_call, dict)
                    else getattr(tool_call, "args", {})
                )

                message = args.get("message", "")
                product_ids = args.get("product_ids_to_show")

                ai_message = AIMessage(content=message)
                new_state: AgentState = {"messages": [ai_message]}

                if product_ids:
                    new_state["product_ids_to_show"] = list(product_ids)

                return new_state

    return {"messages": [AIMessage(content="რით შემიძლია დაგეხმაროთ? ☺️")]}


def should_continue(state: AgentState) -> str:
    """Route to tools or extract response after agent node"""
    messages = state["messages"]
    last_message = messages[-1]

    if len(messages) >= 2:
        second_last = messages[-2]
        if hasattr(second_last, 'type') and second_last.type == "tool":
            tool_name = getattr(second_last, 'name', None)
            if tool_name == "transfer_to_operator":
                return "extract_response"
    
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = (
                tool_call.get("name")
                if isinstance(tool_call, dict)
                else getattr(tool_call, "name", None)
            )
            if tool_name == "respond_to_user":
                return "extract_response"
        return "tools"
    return "extract_response"