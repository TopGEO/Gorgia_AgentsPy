"""Main API module for Sandro - Gorgia expert chatbot"""
import logging
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..db import vector_store
from ..graph import process_graph_iterations, sanitize_messages_for_gemini, create_graph
from ..db import chat
from ..models import ChatRequest, ChatResponse, Product
from .middleware import token_validation_middleware
from .chat_helpers import (
    build_message_with_images,
    find_last_ai_message,
)
from ..utils.translator import translate_if_needed

app = FastAPI(title="Sandro - Gorgia expert")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(token_validation_middleware)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on server startup"""
    await chat.initialize_chat_table()


@app.get("/")
async def home():
    """Health check endpoint"""
    return {"message": "Visitor, you must not be here! Be carefull! You may get tracked as well as 🈂ucked! You have been warned!"}


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    print(f"📨 Received chat request: 📍{request.message}📍")
    try:
        session_id = request.session_id or str(uuid.uuid4())

        history = await chat.get_message_history(session_id, request.browser_id)

        # Sanitize messages from database to comply with Gemini's conversation rules
        existing_messages = await history.aget_messages()
        messages = sanitize_messages_for_gemini(list(existing_messages)) if existing_messages else []

        user_message = build_message_with_images(request.message, request.image_urls)
        messages.append(user_message)

        # Save user message to history before processing
        await history.aadd_messages([user_message])

        graph = await create_graph()
        result = await process_graph_iterations(
            graph,
            {"messages": messages},
            history
        )

        final_messages = result["messages"]
        tool_call = result.get("tool_call")
        
        if tool_call == "transfer_to_operator":
            ai_message = find_last_ai_message(final_messages)
            ai_message = await translate_if_needed(ai_message)
            return ChatResponse(
                response=ai_message,
                session_id=session_id,
                payload=None,
                tool_call=tool_call
            )
        
        ai_message = find_last_ai_message(final_messages)
        product_ids = result.get("product_ids_to_show")
        print(f"💡 Product IDs to show: {product_ids}")

        payload = None
        if product_ids:
            product_ids_int = [int(pid) for pid in product_ids]
            products = await vector_store.search_by_id(product_ids_int)
            
            def safe_validate(p):
                try:
                    return Product.model_validate(p.payload).to_frontend_dict()
                except Exception as e:
                    print(f"Failed to parse product: {e}")
                    return None
            
            products_list = [p for p in (safe_validate(product) for product in products) if p is not None]
            payload = {"products": products_list}
        
        ai_message = await translate_if_needed(ai_message)
        
        return ChatResponse(
            response=ai_message,
            session_id=session_id,
            payload=payload,
            tool_call=tool_call
        )

    except Exception as e:
        logging.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))