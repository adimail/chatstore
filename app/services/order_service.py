from datetime import datetime
from app.models import User, Product, Order, OrderItem, OrderStatus
from app.extensions import db
from app.services import cart_service


def create_order_from_cart(user_id: int) -> Order:
    """Create a new order from user's cart items.

    Args:
        user_id: The ID of the user placing the order

    Returns:
        The newly created Order object

    Raises:
        ValueError: If user not found, cart is empty, or database error occurs
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found.")

    cart_items = cart_service.get_cart_contents(user_id)
    if not cart_items:
        raise ValueError("Cannot create order: Cart is empty.")

    try:
        # Validate products first
        for item in cart_items:
            product = Product.query.get(item.product_id)
            if not product or product.id != item.product.id:
                raise ValueError(
                    f"Product data inconsistency for product ID {item.product_id}."
                )
            if product.quantity_in_stock < 0:
                raise ValueError(
                    f"Inventory issue detected for {product.name}. Please contact support."
                )

        # Calculate total first to avoid creating an order if there's an issue
        total_amount = 0.0
        for item in cart_items:
            price_at_order = item.product.price
            item_total = item.quantity * price_at_order
            total_amount += item_total

        # Create the order with the correct total
        new_order = Order(
            user_id=user_id,
            status=OrderStatus.PENDING,
            total_amount=total_amount,
        )

        # Add order to session
        db.session.add(new_order)
        db.session.flush()  # Assign ID

        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_per_unit=item.product.price,
            )
            db.session.add(order_item)

        # Commit the order and items
        db.session.commit()

        # Clear the cart after successful order creation
        cart_service.clear_cart(user_id)

        return new_order

    except Exception as e:
        db.session.rollback()
        raise ValueError(f"Could not create order due to a database error: {str(e)}")


def get_user_orders(user_id: int):
    return (
        Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    )


def get_order_by_id(order_id: int, user_id):
    order = Order.query.get(order_id)
    if user_id and order and order.user_id != user_id:
        return None
    return order


def get_order_items(order_id: int):
    return (
        OrderItem.query.options(db.joinedload(OrderItem.product))
        .filter_by(order_id=order_id)
        .all()
    )


def cancel_user_order(user_id: int, order_id) -> str:
    order_to_cancel = None
    if order_id:
        order_to_cancel = get_order_by_id(order_id, user_id)
        if not order_to_cancel:
            raise ValueError(f"Order #{order_id} not found or does not belong to you.")
    else:
        cancellable_statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING]
        order_to_cancel = (
            Order.query.filter(
                Order.user_id == user_id, Order.status.in_(cancellable_statuses)
            )
            .order_by(Order.created_at.desc())
            .first()
        )
        if not order_to_cancel:
            raise ValueError("No recent orders found that can be cancelled.")

    if order_to_cancel.status not in [OrderStatus.PENDING, OrderStatus.PROCESSING]:
        return f"Order #{order_to_cancel.id} cannot be cancelled as its status is {order_to_cancel.status.value}."

    order_to_cancel.status = OrderStatus.CANCELLED
    order_to_cancel.updated_at = datetime.now()

    items = get_order_items(order_to_cancel.id)
    product_ids_quantities = {item.product_id: item.quantity for item in items}
    products_to_update = Product.query.filter(
        Product.id.in_(product_ids_quantities.keys())
    ).all()

    for product in products_to_update:
        if product.id in product_ids_quantities:
            product.quantity_in_stock += product_ids_quantities[product.id]
            db.session.add(product)

    db.session.add(order_to_cancel)
    try:
        db.session.commit()
        return f"Order #{order_to_cancel.id} has been cancelled successfully."
    except Exception:
        db.session.rollback()
        raise ValueError("Could not cancel the order due to a database error.")


def request_order_return(user_id: int, order_id: int) -> str:
    order = get_order_by_id(order_id, user_id)
    if not order:
        raise ValueError(f"Order #{order_id} not found or does not belong to you.")

    if order.status != OrderStatus.DELIVERED:
        return f"Cannot request return for Order #{order_id}. Its status is {order.status.value}. Only delivered orders can be returned."

    order.status = OrderStatus.RETURN_REQUESTED
    order.updated_at = datetime.now()
    db.session.add(order)

    try:
        db.session.commit()
        return f"Return request initiated for Order #{order_id}. You will be contacted with further instructions."
    except Exception:
        db.session.rollback()
        raise ValueError("Could not request return due to a database error.")


def proceed_to_checkout(user_id: int) -> str:
    """Process checkout for a user's cart.

    Args:
        user_id: The ID of the user checking out

    Returns:
        A message indicating success or failure

    Raises:
        ValueError: If checkout fails
    """
    try:
        order = create_order_from_cart(user_id)
        return f"Checkout successful! Your order #{order.id} has been created with status '{order.status.value}'. Total: ₹{order.total_amount:.2f}."
    except ValueError as e:
        return f"Checkout failed: {str(e)}"
    except Exception as e:
        db.session.rollback()
        return (
            f"Checkout failed: An unexpected error occurred during checkout: {str(e)}"
        )
