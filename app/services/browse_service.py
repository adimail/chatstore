from app.models import Product
from app.extensions import db

DEFAULT_PER_PAGE = 20


def get_filtered_products(
    search_term=None,
    categories=None,
    min_price=None,
    max_price=None,
    in_stock_only=False,
    min_rating=None,
    page=1,
    per_page=DEFAULT_PER_PAGE,
):
    """
    Fetches products based on various filter criteria and handles pagination.

    Args:
        search_term (str, optional): Term to search in product names.
        categories (list, optional): List of category names to filter by.
        min_price (float, optional): Minimum product price.
        max_price (float, optional): Maximum product price.
        in_stock_only (bool, optional): If True, only return products with quantity > 0.
        min_rating (float, optional): Minimum product rating.
        page (int, optional): Current page number for pagination.
        per_page (int, optional): Number of items per page.

    Returns:
        Pagination: A Flask-SQLAlchemy Pagination object containing the filtered products.
    """
    query = Product.query

    # Apply search term filter (case-insensitive)
    if search_term:
        query = query.filter(Product.name.ilike(f"%{search_term}%"))

    # Apply category filter
    if categories:
        # Ensure categories is a list, even if only one is passed
        if not isinstance(categories, list):
            categories = [categories]
        # Filter if product category is in the list of selected categories
        query = query.filter(Product.category.in_(categories))

    # Apply price range filters
    if min_price is not None:
        try:
            query = query.filter(Product.price >= float(min_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid min_price
    if max_price is not None:
        try:
            query = query.filter(Product.price <= float(max_price))
        except (ValueError, TypeError):
            pass  # Ignore invalid max_price

    # Apply stock filter
    if in_stock_only:
        query = query.filter(Product.quantity_in_stock > 0)
    else:
        # Default behavior from original route was to only show items with stock > 0
        # Keep this unless explicitly overridden or changed requirement
        query = query.filter(Product.quantity_in_stock > 0)

    # Apply rating filter
    if min_rating is not None:
        try:
            query = query.filter(Product.rating >= float(min_rating))
        except (ValueError, TypeError):
            pass  # Ignore invalid rating

    # Order results (e.g., by name)
    query = query.order_by(Product.name)

    # Apply pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return pagination


def get_all_categories():
    """
    Fetches a list of unique product categories from the database.

    Returns:
        list: A list of unique category names, sorted alphabetically.
    """
    categories = (
        db.session.query(Product.category).distinct().order_by(Product.category).all()
    )
    # Extract the category name from the tuple result
    return [category[0] for category in categories if category[0]]
