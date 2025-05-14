from app.models import Product, CartItem
from app.extensions import db


def add_to_cart(user_id: int, product_id: int, quantity: int) -> str:
    if quantity <= 0:
        raise ValueError("Quantity must be positive.")

    product = Product.query.get(product_id)
    if not product:
        raise ValueError(f"Product with ID {product_id} not found.")

    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity
        if product.quantity_in_stock < (
            new_quantity - cart_item.quantity
        ):  # Check only additional quantity
            raise ValueError(
                f"Not enough stock for {product.name}. Only {product.quantity_in_stock} more available."
            )
        cart_item.quantity = new_quantity
        product.quantity_in_stock -= quantity
        message = (
            f"Updated {product.name} quantity to {cart_item.quantity} in your cart."
        )
    else:
        if product.quantity_in_stock < quantity:
            raise ValueError(
                f"Not enough stock for {product.name}. Only {product.quantity_in_stock} available."
            )
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        product.quantity_in_stock -= quantity
        db.session.add(cart_item)
        message = f"Added {quantity} x {product.name} to your cart."

    db.session.add(product)
    try:
        db.session.commit()
        return message
    except Exception:
        db.session.rollback()
        raise ValueError("Could not update cart due to a database error.")


def remove_from_cart(user_id: int, product_id: int) -> str:
    cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()

    if not cart_item:
        raise ValueError("Item not found in your cart.")

    product = Product.query.get(product_id)
    item_name = f"Product ID {product_id}"
    if product:
        product.quantity_in_stock += cart_item.quantity
        db.session.add(product)
        item_name = product.name

    db.session.delete(cart_item)
    try:
        db.session.commit()
        return f"Removed {item_name} from your cart."
    except Exception:
        db.session.rollback()
        raise ValueError("Could not update cart due to a database error.")


def get_cart_contents(user_id: int):
    return (
        CartItem.query.options(db.joinedload(CartItem.product))
        .filter_by(user_id=user_id)
        .order_by(CartItem.added_at)
        .all()
    )


def clear_cart(user_id: int):
    cart_items = CartItem.query.filter_by(user_id=user_id).all()
    if not cart_items:
        return

    product_ids_quantities = {item.product_id: item.quantity for item in cart_items}

    CartItem.query.filter_by(user_id=user_id).delete()

    products_to_update = Product.query.filter(
        Product.id.in_(product_ids_quantities.keys())
    ).all()
    for product in products_to_update:
        product.quantity_in_stock += product_ids_quantities.get(product.id, 0)
        db.session.add(product)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise ValueError("Could not clear cart due to a database error.")


def get_cart_total(user_id: int) -> float:
    items = get_cart_contents(user_id)
    total = sum(item.quantity * item.product.price for item in items)
    return total
