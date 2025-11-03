def extract_product_payload(item, is_lexical: bool) -> dict:
    metadata = item.payload.get("metadata", {})
    product = metadata.get("product", {})

    route = product.get("route")
    product_url = f"https://zoommer.ge/{route}" if route else None

    payload = {
        "id": product.get("id"),
        "name": product.get("name"),
        "price": product.get("price"),
        "isInStock": product.get("isInStock"),
        "url": product_url,
    }
    if product.get("previousPrice") is not None:
        payload["previousPrice"] = product.get("previousPrice")
    if is_lexical:
        payload["barCode"] = product.get("barCode")

    return payload