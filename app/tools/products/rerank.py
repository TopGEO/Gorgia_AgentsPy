from typing import List
import json
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from ...config import settings
from .extractors import extract_product_payload


class RerankOutput(BaseModel):
    selected_ids: List[str] = Field(description="List of IDs that best match the query.")


def build_products_text_and_id_map(rag_results, is_lexical: bool):
    products_texts = ""
    id_to_item = {}
    for item in rag_results:
        metadata = item.payload.get("metadata", {})
        product = metadata.get("product", {})
        product_id = product.get("id")
        if product_id:
            id_to_item[str(product_id)] = item

        p = extract_product_payload(item, is_lexical=is_lexical)

        price_line = f"Price: {p.get('price', 'N/A')} GEL" + (f" (was {p['previousPrice']} GEL)" if p.get('previousPrice') is not None else "")
        products_texts += (
            f"ID: {p.get('id')}\n"
            f"Name: {p.get('name')}\n"
            f"{price_line}\n"
            f"In Stock: {'Yes' if p.get('isInStock') else 'No'}\n"
        )
        if is_lexical:
            products_texts += f"Bar Code: {p.get('barCode')}\n\n"
    return products_texts, id_to_item


def rerank_products(rag_results, query, is_lexical: bool):
    products_texts, id_to_item = build_products_text_and_id_map(rag_results, is_lexical)

    prompt = (
        "Query: '{query}'\n\n"
        "From the list below, select matching products."
        "Respond with ids of matching products only.\n\n"
        "Products:\n{products_texts}"
    )

    prompt = PromptTemplate.from_template(prompt)

    llm = ChatOpenAI(
        model="gpt-4o-mini", temperature=0, api_key=settings.openai_api_key
    ).with_structured_output(RerankOutput)

    chain = prompt | llm

    try:
        response = chain.invoke({"query": query, "products_texts": str(products_texts)})

        print(f"🤖 LLM selected IDs: {response.selected_ids}")
        print(f"Selected {len(response.selected_ids)}/{len(rag_results)} items after reranking.")

        reranked_results = [
            id_to_item[i] for i in response.selected_ids
            if i in id_to_item
        ]

        if len(reranked_results) == 0:
            print("⚠️ Reranking returned 0 results, returning original search results")
            return rag_results

        return reranked_results
    except Exception as e:
        print(f"Reranking failed, returning original results: {str(e)}")
        return rag_results

def rerank_docs(rag_results, query):
    id_to_item = {}
    for item in rag_results:
        item_id = item.payload.get("id") if hasattr(item, "payload") else None
        if item_id is not None:
            id_to_item[str(item_id)] = item

    items_json = json.dumps([getattr(item, "payload", {}) for item in rag_results], ensure_ascii=False)

    prompt = (
        "Query: '{query}'\n\n"
        "Your task: Select ONLY the catalog items that are truly relevant and match the query.\n"
        "Be very strict - if an item doesn't directly match or relate to the query, DO NOT include it.\n"
        "Only return IDs of items (use the 'id' field) that are clearly relevant to what the user is looking for.\n"
        "If nothing matches well, return an empty list.\n\n"
        "Catalog items (JSON array):\n{items_json}"
    )

    prompt = PromptTemplate.from_template(prompt)

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=settings.gemini_api_key,
        thinking_budget=0
    ).with_structured_output(RerankOutput)

    chain = prompt | llm

    try:
        response = chain.invoke({"query": query, "items_json": items_json})

        print(f"🤖 Gemini Flash selected IDs: {response.selected_ids}")
        print(f"Selected {len(response.selected_ids)}/{len(rag_results)} catalog items after reranking.")

        reranked_results = [
            id_to_item[i] for i in response.selected_ids
            if i in id_to_item
        ]

        if len(reranked_results) == 0:
            print("⚠️ Reranking returned 0 results, returning original search results")
            return rag_results

        return reranked_results
    except Exception as e:
        print(f"Catalog reranking failed, returning original results: {str(e)}")
        return rag_results
