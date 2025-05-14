from app.services import product_service


def get_product_info_executor(product_name: str) -> str:
    """
    Retrieves and formats information about a specific product.
    This tool does not require a user_id as product information is generic.

    Args:
        product_name: The name of the product to get information about.

    Returns:
        A string with product details or a message if not found.
    """
    try:
        product = product_service.find_product_by_name(product_name)
        if not product:
            return f"Sorry, I couldn't find information for a product named '{product_name}'."

        response = [f"Here's the information for {product.name}:"]
        if product.description:
            response.append(f"- Description: {product.description}")
        response.append(f"- Price: ₹{product.price:.2f}")
        response.append(f"- Current Rating: {product.rating:.1f}/5.0")
        stock_status = "In Stock" if product.quantity_in_stock > 0 else "Out of Stock"
        response.append(
            f"- Availability: {stock_status} ({product.quantity_in_stock} available)"
        )

        return "\n".join(response)
    except Exception:
        return "An error occurred while retrieving product information."
