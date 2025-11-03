"""Helper functions for chat message processing"""
import re
from typing import List, Optional, Tuple
from langchain_core.messages import HumanMessage


def build_message_with_images(text: str, image_urls: Optional[List[str]]) -> HumanMessage:
    """
    Build a HumanMessage with optional image URLs

    Args:
        text: The text message
        image_urls: Optional list of image URLs to include

    Returns:
        HumanMessage with text and images if provided
    """
    if image_urls:
        content = [{"type": "text", "text": text}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        return HumanMessage(content=content)
    return HumanMessage(content=text)


def extract_product_ids(message: str) -> Tuple[str, Optional[List[int]]]:
    """
    Extract product IDs from AI message and clean the message

    Args:
        message: AI message that may contain product IDs marker

    Returns:
        Tuple of (cleaned_message, product_ids)
    """
    match = re.search(r'\[PRODUCT_IDS: ([\d,]+)\]', message)
    if match:
        product_ids = [int(pid) for pid in match.group(1).split(',')]
        cleaned_message = re.sub(r'\n\n\[PRODUCT_IDS: [\d,]+\]', '', message)
        return cleaned_message, product_ids
    return message, None


def find_last_ai_message(messages: List) -> str:
    """
    Find the last AI message in the conversation

    Args:
        messages: List of conversation messages

    Returns:
        The content of the last AI message, or default message if not found
    """
    for msg in reversed(messages):
        if msg.type == "ai":
            return msg.content
    return "რით შემიძლია დაგეხმაროთ? 😊"
