from langchain_core.tools import tool

@tool
def manage_cart(action: str, product_id: str = None, quantity: int = 1) -> str:
    """
    Manage shopping cart operations.
    
    Args:
        action: Action to perform ("add", "remove", "view", "clear", "update_quantity")
        product_id: Product ID for add/remove/update actions
        quantity: Quantity for add/update actions
    """
    
    return f"Cart action '{action}' executed for product {product_id} with quantity {quantity}. Note: Cart state is managed in graph state."