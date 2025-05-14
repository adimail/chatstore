import enum
from datetime import datetime
from typing import List, Optional

from flask_login import UserMixin
from werkzeug.security import check_password_hash
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    Float,
    Integer,
    DateTime,
    Enum as SQLAlchemyEnum,
    UniqueConstraint,
)

from app.extensions import db


class MessageSender(enum.Enum):
    USER = "user"
    AGENT = "agent"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    RETURN_REQUESTED = "return_requested"
    RETURNED = "returned"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    orders: Mapped[List["Order"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    cart_items: Mapped[List["CartItem"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    chat_messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="ChatMessage.timestamp",
    )

    def __init__(
        self,
        email: str,
        name: str,
        password_hash: str,
        created_at: Optional[datetime] = None,
    ) -> None:
        self.email = email
        self.name = name
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now()

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.id}: {self.email}>"

    @property
    def is_active(self) -> bool:
        return True


class Product(db.Model):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    category: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True, default="Miscellaneous"
    )

    cart_items: Mapped[List["CartItem"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="dynamic"
    )
    order_items: Mapped[List["OrderItem"]] = relationship(
        back_populates="product", lazy="dynamic"
    )

    def __init__(
        self,
        name: str,
        description: Optional[str],
        price: float,
        quantity_in_stock: int = 0,
        rating: float = 0.0,
        category: str = "Miscellaneous",
    ) -> None:
        self.name = name
        self.description = description
        self.price = price
        self.quantity_in_stock = quantity_in_stock
        self.rating = rating
        # --- Assign New Column ---
        self.category = category

    def __repr__(self) -> str:
        return f"<Product {self.id}: {self.name} ({self.category})>"


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_cart"),
    )

    user: Mapped["User"] = relationship(back_populates="cart_items")
    product: Mapped["Product"] = relationship(back_populates="cart_items")

    def __init__(
        self,
        user_id: int,
        product_id: int,
        quantity: int = 1,
        added_at: Optional[datetime] = None,
    ) -> None:
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.added_at = added_at or datetime.now()

    def __repr__(self) -> str:
        return f"<CartItem UserID:{self.user_id} ProductID:{self.product_id} Qty:{self.quantity}>"


class Order(db.Model):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLAlchemyEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=db.func.now, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=db.func.now, onupdate=db.func.now
    )
    total_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    user: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(
        self,
        user_id: int,
        status: OrderStatus = OrderStatus.PENDING,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        total_amount: float = 0.0,
    ) -> None:
        self.user_id = user_id
        self.status = status
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.total_amount = total_amount

    def __repr__(self) -> str:
        return f"<Order {self.id} Status:{self.status.value}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    def __init__(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
        price_per_unit: float,
    ) -> None:
        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.price_per_unit = price_per_unit

    def __repr__(self) -> str:
        return f"<OrderItem OrderID:{self.order_id} ProductID:{self.product_id} Qty:{self.quantity}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, index=True
    )
    sender: Mapped[MessageSender] = mapped_column(
        SQLAlchemyEnum(MessageSender), nullable=False
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship(back_populates="chat_messages")

    def __init__(
        self,
        user_id: int,
        sender: MessageSender,
        message_text: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        self.user_id = user_id
        self.sender = sender
        self.message_text = message_text
        self.timestamp = timestamp or datetime.now()

    def __repr__(self) -> str:
        return (
            f"<ChatMessage ID:{self.id} User:{self.user_id} Sender:{self.sender.value}>"
        )
