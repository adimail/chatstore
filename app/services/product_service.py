from app.models import Product
from app.extensions import db


def find_product_by_name(name: str):
    return Product.query.filter(
        Product.name.ilike(f"{name}")
    ).first()  # Exact match, case insensitive


def get_product_by_id(product_id: int):
    return Product.query.get(product_id)


def list_all_products(limit: int = 20):
    return Product.query.limit(limit).all()


def create_product(name, description, price, quantity_in_stock, rating=0.0):
    if Product.query.filter(Product.name.ilike(name)).first():
        raise ValueError(f"Product with name '{name}' already exists.")
    product = Product(
        name=name,
        description=description,
        price=price,
        quantity_in_stock=quantity_in_stock,
        rating=rating,
    )
    db.session.add(product)
    try:
        db.session.commit()
        return product
    except Exception:
        db.session.rollback()
        raise
