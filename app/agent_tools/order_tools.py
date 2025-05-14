from app.services import order_service


def view_orders_executor(user_id: int) -> str:
    """
    Retrieves the user's order history and formats it.

    Args:
        user_id: The ID of the current user.

    Returns:
        A string listing orders or a message if no orders exist.
    """
    try:
        orders = order_service.get_user_orders(user_id)
        if not orders:
            return "You haven't placed any orders yet."

        response = ["Here are your orders:"]
        for order in orders:
            response.append(f"\n--- Order #{order.id} ---")
            response.append(f"Status: {order.status.value}")
            response.append(f"Placed on: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
            response.append(f"Total: ₹{order.total_amount:.2f}")
            response.append("Items:")
            items = order_service.get_order_items(order.id)
            if items:
                for item in items:
                    response.append(
                        f"  - {item.quantity} x {item.product.name} (@ ₹{item.price_per_unit:.2f} each)"
                    )
            else:
                response.append("  (No item details available)")
        return "\n".join(response)
    except Exception:
        return "An error occurred while retrieving your order history."


def cancel_order_executor(user_id: int, order_id: int) -> str:
    """
    Attempts to cancel an order.

    Args:
        user_id: The ID of the current user.
        order_id: The specific ID of the order to cancel.

    Returns:
        A string confirming cancellation or an error/status message.
    """
    try:
        message = order_service.cancel_user_order(user_id, order_id)
        return message
    except ValueError as e:
        return str(e)
    except Exception:
        return "An unexpected error occurred while trying to cancel the order."


def request_return_executor(user_id: int, order_id: int) -> str:
    """
    Initiates a return request for a delivered order.

    Args:
        user_id: The ID of the current user.
        order_id: The ID of the delivered order.

    Returns:
        A string confirming the return request or an error/status message.
    """
    try:
        message = order_service.request_order_return(user_id, order_id)
        return message
    except ValueError as e:
        return str(e)
    except Exception:
        return "An unexpected error occurred while trying to request the return."


def proceed_to_checkout_executor(user_id: int) -> str:
    """
    Initiates the checkout process by creating an order from the cart.

    Args:
        user_id: The ID of the current user.

    Returns:
        A string confirming checkout and order creation or an error message.
    """
    try:
        return order_service.proceed_to_checkout(user_id)
    except ValueError as e:
        return f"Checkout failed: {str(e)}"
    except Exception:
        return "An unexpected error occurred during checkout. Please try again."
