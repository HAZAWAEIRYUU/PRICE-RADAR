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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), server_default=sa.func.now())

    products = relationship("Product", back_populates="owner", cascade="all, delete-orphan")

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
