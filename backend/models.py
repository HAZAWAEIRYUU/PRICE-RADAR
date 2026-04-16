import sqlalchemy as sa
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    plan = Column(String, default="free")  # free / pro / enterprise
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    # LINE integration
    line_user_id = Column(String, nullable=True, unique=True, index=True)
    line_display_name = Column(String, nullable=True)
    # Notification preferences
    notification_enabled = Column(Boolean, default=True, server_default=sa.text("true"), nullable=False)
    notify_price_loss = Column(Boolean, default=True, server_default=sa.text("true"), nullable=False)
    notify_price_recovery = Column(Boolean, default=True, server_default=sa.text("true"), nullable=False)
    notify_stock_change = Column(Boolean, default=True, server_default=sa.text("true"), nullable=False)
    notify_subscription = Column(Boolean, default=False, server_default=sa.text("false"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())

    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_name = Column(String, index=True)
    own_price = Column(Numeric(10, 2))
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now(), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="products")
    competitor_urls = relationship("CompetitorUrl", back_populates="product", cascade="all, delete-orphan")

class CompetitorUrl(Base):
    __tablename__ = "competitor_urls"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    competitor_name = Column(String)
    url = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())

    product = relationship("Product", back_populates="competitor_urls")
    price_histories = relationship("PriceHistory", back_populates="competitor_url", cascade="all, delete-orphan")

class PriceHistory(Base):
    __tablename__ = "price_histories"

    id = Column(Integer, primary_key=True, index=True)
    competitor_url_id = Column(Integer, ForeignKey("competitor_urls.id"))
    price = Column(Numeric(10, 2))
    stock_status = Column(String, default="在庫あり")
    scraped_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())

    competitor_url = relationship("CompetitorUrl", back_populates="price_histories")

class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # price_loss / price_recovery / stock_out / pro_subscribed
    entity_id = Column(Integer, nullable=True, index=True)  # competitor_url_id etc.
    previous_state = Column(String, nullable=True)
    current_state = Column(String, nullable=True)
    line_message_id = Column(String, nullable=True)
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now(), index=True)

    user = relationship("User", back_populates="notification_logs")

# Plan limits configuration
PLAN_LIMITS = {
    "free": {
        "max_products": 3,
        "max_competitors_per_product": 2,
        "history_retention_days": 7,
        "label": "Free",
        "price": 0,
    },
    "pro": {
        "max_products": 50,
        "max_competitors_per_product": 10,
        "history_retention_days": None,  # unlimited
        "label": "Pro",
        "price": 1980,
    },
    "enterprise": {
        "max_products": None,  # unlimited
        "max_competitors_per_product": None,
        "history_retention_days": None,
        "label": "Enterprise",
        "price": None,
    },
}
