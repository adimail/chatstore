from app.services import cart_service, product_service


def add_item_to_cart_executor(user_id: int, product_name: str, quantity: int) -> str:
    """
    Adds a specified quantity of a product to the user's shopping cart.
    Use this when the user explicitly asks to add something.

    Args:
        user_id: The ID of the current user.
        product_name: The name of the product to add (e.g., 'Apple', 'Banana'). Be specific.
        quantity: The number of units of the product to add.

    Returns:
        A string confirming the action or an error message.
    """
    if quantity <= 0:
        return "Please specify a positive quantity to add."

    product = product_service.find_product_by_name(product_name)
    if not product:
        return f"Sorry, I couldn't find a product named '{product_name}'."

    try:
        message = cart_service.add_to_cart(user_id, product.id, quantity)
        return message
    except ValueError as e:
        return str(e)
    except Exception:
        return "An unexpected error occurred while trying to add the item to your cart."


def view_cart_executor(user_id: int) -> str:
    """
    Retrieves the user's cart contents and formats it as a string.

    Args:
        user_id: The ID of the current user.

    Returns:
        A string listing cart items or a message if the cart is empty.
    """
    try:
        items = cart_service.get_cart_contents(user_id)
        if not items:
            return "Your shopping cart is currently empty."

        cart_details = ["Here's what's in your cart:"]
        total_price = 0.0
        for item in items:
            item_total = item.quantity * item.product.price
            cart_details.append(
                f"- {item.quantity} x {item.product.name} (@ ₹{item.product.price:.2f} each) = ₹{item_total:.2f}"
            )
            total_price += item_total

        cart_details.append(f"\nTotal: ₹{total_price:.2f}")
        return "\n".join(cart_details)
    except Exception:
        return "An unexpected error occurred while trying to view your cart."


def remove_item_from_cart_executor(user_id: int, product_name: str) -> str:
    """
    Removes an item entirely from the user's cart.

    Args:
        user_id: The ID of the current user.
        product_name: The name of the product to remove.

    Returns:
        A string confirming the action or an error message.
    """
    product = product_service.find_product_by_name(product_name)
    if not product:
        return f"Sorry, I couldn't find a product named '{product_name}' in the system to remove."

    try:
        message = cart_service.remove_from_cart(user_id, product.id)
        return message
    except ValueError as e:
        return str(e)
    except Exception:
        return "An unexpected error occurred while trying to remove the item from your cart."
