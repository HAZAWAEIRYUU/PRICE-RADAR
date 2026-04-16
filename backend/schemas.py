from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from datetime import datetime
from decimal import Decimal

class CompetitorUrlBase(BaseModel):
    competitor_name: str
    url: str

class CompetitorUrlCreate(CompetitorUrlBase):
    pass

class CompetitorUrl(CompetitorUrlBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    product_name: str
    own_price: float
    category: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    competitor_urls: Optional[List[CompetitorUrlCreate]] = []

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    own_price: Optional[float] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class Product(ProductBase):
    id: int
    user_id: int
    own_price: str
    created_at: datetime
    updated_at: datetime
    competitor_urls: List[CompetitorUrl] = []

    @field_validator("own_price", mode="before")
    def convert_own_price(cls, v):
        return str(v) if v is not None else v

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_active: bool
    plan: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class PriceHistoryRecord(BaseModel):
    id: int
    competitor_url_id: int
    price: str
    stock_status: str
    scraped_at: datetime
    created_at: datetime

    @field_validator("price", mode="before")
    def convert_price(cls, v):
        return str(v) if v is not None else v

    class Config:
        from_attributes = True

class PriceAlertItem(BaseModel):
    product_id: int
    product_name: str
    own_price: str
    competitor_name: str
    competitor_price: str
    price_diff: str
    stock_status: str

class ProductCount(BaseModel):
    count: int

class PlanUsage(BaseModel):
    current_products: int
    max_products: Optional[int]  # None = unlimited
    max_competitors_per_product: Optional[int]
    history_retention_days: Optional[int]

class PlanInfo(BaseModel):
    plan: str
    label: str
    price: Optional[int]
    usage: PlanUsage

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str

class LineAuthRequest(BaseModel):
    code: str
    redirect_uri: str

class NotificationSettings(BaseModel):
    notification_enabled: bool
    notify_price_loss: bool
    notify_price_recovery: bool
    notify_stock_change: bool
    notify_subscription: bool

    class Config:
        from_attributes = True

class NotificationSettingsUpdate(BaseModel):
    notification_enabled: Optional[bool] = None
    notify_price_loss: Optional[bool] = None
    notify_price_recovery: Optional[bool] = None
    notify_stock_change: Optional[bool] = None
    notify_subscription: Optional[bool] = None

class LineLinkStatus(BaseModel):
    linked: bool
    line_user_id: Optional[str] = None
    line_display_name: Optional[str] = None
    bot_basic_id: Optional[str] = None  # 友達追加用

