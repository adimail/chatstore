from flask import render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from . import web_bp
from app.services import cart_service, order_service, browse_service
from app.models import Product, CartItem
from app.extensions import db


@web_bp.route("/")
def index():
    featured_products = (
        Product.query.filter(Product.quantity_in_stock > 0)
        .order_by(Product.name)
        .limit(8)
        .all()
    )

    cart_items = []
    total_price = 0.0

    if current_user.is_authenticated:
        cart_items = cart_service.get_cart_contents(current_user.id)
        if cart_items:
            for item in cart_items:
                if item.product:
                    item.total_item_price = item.quantity * item.product.price
                    total_price += item.total_item_price
                else:
                    item.total_item_price = 0

    return render_template(
        "index.html.jinja2",
        title="Welcome",
        products=featured_products,
        cart_items=cart_items,
        total_price=total_price,
    )


@web_bp.route("/profile")
@login_required
def profile():
    cart_items = cart_service.get_cart_contents(current_user.id)
    total_price = 0.0
    for item in cart_items:
        if item.product:
            item.total_item_price = item.quantity * item.product.price
            total_price += item.total_item_price
        else:
            item.total_item_price = 0

    user_orders = order_service.get_user_orders(current_user.id)
    robohash_url = (
        f"https://robohash.org/{current_user.id}.png?size=150x150&gravatar=hashed"
    )

    return render_template(
        "profile.html.jinja2",
        title="Your Profile",
        user=current_user,
        cart_items=cart_items,
        total_price=total_price,
        orders=user_orders,
        robohash_url=robohash_url,
    )


@web_bp.route("/browse")
@login_required
def browse_products():
    """Displays products available in the warehouse with filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = 20

    search_term = request.args.get("search", None)
    selected_categories = request.args.getlist("category")
    min_price = request.args.get("min_price", None)
    max_price = request.args.get("max_price", None)
    in_stock_only = request.args.get("in_stock") == "on"
    min_rating = request.args.get("min_rating", None)

    products_pagination = browse_service.get_filtered_products(
        search_term=search_term,
        categories=selected_categories,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        min_rating=min_rating,
        page=page,
        per_page=per_page,
    )

    products = products_pagination.items
    all_categories = browse_service.get_all_categories()

    current_filters = {
        "search": search_term or "",
        "categories": selected_categories,
        "min_price": min_price or "",
        "max_price": max_price or "",
        "in_stock": in_stock_only,
        "min_rating": min_rating or "",
    }

    return render_template(
        "browse_products.html.jinja2",
        title="Browse Products",
        products=products,
        pagination=products_pagination,
        all_categories=all_categories,
        current_filters=current_filters,
    )


@web_bp.route("/add_manual", methods=["POST"])
@login_required
def add_to_cart_manual():
    """Handles adding an item to the cart from the browse page."""
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", 1, type=int)

    if not product_id:
        flash("Invalid product specified.", "danger")
        return redirect(url_for("web.browse_products"))

    if quantity <= 0:
        flash("Quantity must be at least 1.", "warning")
        return redirect(request.referrer or url_for("web.browse_products"))

    try:
        message = cart_service.add_to_cart(current_user.id, product_id, quantity)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred while adding the item.", "danger")

    # Redirect back to the browse page, preserving filters if possible
    # This requires passing filters back or storing them in session,
    # for simplicity, just redirecting to the base browse URL for now.
    # A better approach might involve JS or passing args in redirect.
    return redirect(request.referrer or url_for("web.browse_products"))


@web_bp.route("/cart")
@login_required
def view_cart():
    """Displays the user's current shopping cart."""
    cart_items = cart_service.get_cart_contents(current_user.id)
    total_price = 0.0
    for item in cart_items:
        # Ensure product exists before calculating price
        if item.product:
            item.total_item_price = item.quantity * item.product.price
            total_price += item.total_item_price
        else:
            # Handle case where product might be missing (though unlikely with FK constraints)
            item.total_item_price = 0
            # Optionally log this situation or remove the cart item

    return render_template(
        "cart.html.jinja2",
        title="Your Shopping Cart",
        cart_items=cart_items,
        total_price=total_price,
    )


@web_bp.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_from_cart_web(item_id):
    """Removes an item from the cart based on CartItem ID."""
    cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()

    if not cart_item:
        flash("Item not found in your cart.", "warning")
        return redirect(url_for("web.view_cart"))

    try:
        message = cart_service.remove_from_cart(current_user.id, cart_item.product_id)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        # Log the exception e
        db.session.rollback()
        flash("An unexpected error occurred while removing the item.", "danger")

    return redirect(url_for("web.view_cart"))


@web_bp.route("/checkout", methods=["POST"])
@login_required
def proceed_to_checkout_web():
    """Initiates the checkout process from the cart page."""
    try:
        message = order_service.proceed_to_checkout(current_user.id)
        if "Checkout successful" in message:
            flash(message, "success")
            return redirect(
                url_for("web.orders")
            )  # Redirect to orders page instead of profile
        else:
            flash(message, "danger")
            return redirect(url_for("web.view_cart"))
    except ValueError as e:
        flash(f"Checkout failed: {str(e)}", "danger")
        return redirect(url_for("web.view_cart"))
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred during checkout.", "danger")
        return redirect(url_for("web.view_cart"))


@web_bp.route("/orders")
@login_required
def orders():
    """Displays the user's order history."""
    user_orders = order_service.get_user_orders(current_user.id)

    # Load order items for each order
    for order in user_orders:
        items = order_service.get_order_items(order.id)
        # Eagerly load items to avoid lazy loading issues in template
        order.items = items

    return render_template(
        "orders.html.jinja2", title="Your Orders", orders=user_orders
    )


@web_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id):
    """Cancels a user's order."""
    try:
        message = order_service.cancel_user_order(current_user.id, order_id)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred while canceling the order.", "danger")

    return redirect(url_for("web.orders"))


@web_bp.route("/orders/<int:order_id>/return", methods=["POST"])
@login_required
def request_return(order_id):
    """Requests a return for a delivered order."""
    try:
        message = order_service.request_order_return(current_user.id, order_id)
        flash(message, "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception as e:
        db.session.rollback()
        flash("An unexpected error occurred while requesting the return.", "danger")

    return redirect(url_for("web.orders"))
