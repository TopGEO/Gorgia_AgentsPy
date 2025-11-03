from typing import List
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def sanitize_messages_for_gemini(messages: List) -> List:
    sanitized = []
    skip_next_tool_response = False

    for i, m in enumerate(messages):
        if m.type == "ai":
            if hasattr(m, "tool_calls") and m.tool_calls:
                # Check if this AI message contains respond_to_user or transfer_to_operator
                has_respond_to_user = False
                has_transfer_to_operator = False
                other_tool_calls = []
                respond_message = ""
                
                for tc in m.tool_calls:
                    tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                    if tool_name == "respond_to_user":
                        has_respond_to_user = True
                        # Extract the message content from respond_to_user args
                        args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                        respond_message = args.get('message', '')
                    elif tool_name == "transfer_to_operator":
                        has_transfer_to_operator = True
                        # Keep transfer_to_operator in tool calls for context
                        other_tool_calls.append(tc)
                    else:
                        other_tool_calls.append(tc)
                
                if has_respond_to_user and not other_tool_calls:
                    # Only respond_to_user was called - convert to regular AI message
                    # This preserves the final response in history
                    if respond_message:
                        sanitized.append(AIMessage(content=respond_message))
                    skip_next_tool_response = True
                elif other_tool_calls:
                    # There are other tool calls - keep them (including transfer_to_operator)
                    new_ai_msg = AIMessage(content=m.content or "", tool_calls=other_tool_calls)
                    sanitized.append(new_ai_msg)
                    # If respond_to_user was among them, we'll skip its tool response
                    if has_respond_to_user:
                        skip_next_tool_response = True
            else:
                # Regular AI message without tool calls
                sanitized.append(m)

        elif m.type == "tool":
            # Check if we should skip this tool response (from respond_to_user)
            # Keep transfer_to_operator tool results for context
            tool_name = getattr(m, 'name', None)
            if tool_name == "respond_to_user" or skip_next_tool_response:
                skip_next_tool_response = False
                continue
            sanitized.append(m)

        else:
            # Human messages and others
            sanitized.append(m)

    return sanitized


def should_continue_processing(messages: List) -> bool:
    """Check if we should continue processing based on last message"""
    if not messages:
        return False

    last_message = messages[-1]
    
    # Check if the last message is a tool result from transfer_to_operator
    if hasattr(last_message, 'type') and last_message.type == "tool":
        tool_name = getattr(last_message, 'name', None)
        if tool_name == "transfer_to_operator":
            return False

    # If last message is AI with tool_calls, check if respond_to_user was called
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tc in last_message.tool_calls:
            tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
            if tool_name == "respond_to_user":
                return False
        return True

    # If last message is just AI text without tool calls, we're done
    if isinstance(last_message, AIMessage):
        return False

    return True