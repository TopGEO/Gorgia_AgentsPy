from .utils import sanitize_messages_for_gemini, should_continue_processing


async def process_graph_iterations(graph, initial_state, history, max_iterations: int = 10):
    """
    Process graph iterations with Gemini as the single agent.
    The loop continues until respond_to_user is called or max_iterations is reached.
    """
    initial_messages = initial_state.get("messages", [])
    current_state = {"messages": initial_messages}

    for _ in range(max_iterations):
        result = await graph.ainvoke(current_state)
        new_messages = result["messages"]
        old_count = len(current_state["messages"])

        # Add new messages to history
        for msg in new_messages[old_count:]:
            if msg.type == "human":
                history.add_message(msg)
            elif msg.type == "ai":
                # Check if this is the final response (no tool_calls) or has tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Don't add AI messages with respond_to_user tool calls to history
                    # But DO add transfer_to_operator so AI knows user talked to operator
                    has_respond = False
                    has_transfer = False
                    for tc in msg.tool_calls:
                        tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', None)
                        if tool_name == "respond_to_user":
                            has_respond = True
                        elif tool_name == "transfer_to_operator":
                            has_transfer = True
                    
                    if has_transfer or (not has_respond):
                        history.add_message(msg)
                else:
                    # Final AI response without tool calls - this is the user-facing message
                    # Don't save empty AI messages (e.g., from transfer_to_operator final response)
                    if msg.content and msg.content.strip():
                        history.add_message(msg)
            elif msg.type == "tool":
                # Don't add respond_to_user tool results to history
                # But DO add transfer_to_operator tool results
                if hasattr(msg, 'name') and msg.name != "respond_to_user":
                    history.add_message(msg)

        current_state = result

        # Check if we should stop processing
        if not should_continue_processing(new_messages):
            break

    return result