"""
MegaCommerce Data Transfer Objects (DTOs) & Pydantic Validation Schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from shared.enums import (
    UserRole, UserStatus, ProductStatus, OrderStatus, PaymentStatus,
    PaymentMethod, ShipmentStatus, CouponType, ReturnReason, ReturnStatus,
    FraudRiskCategory, WarehouseZone
)


# Base DTO Config
class BaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


# Auth DTOs
class UserRegisterRequest(BaseDTO):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    phone_number: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    company_name: Optional[str] = None  # Mandatory if SELLER


class UserLoginRequest(BaseDTO):
    email: EmailStr
    password: str


class AuthTokenResponse(BaseDTO):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    expires_in_seconds: int


class UserResponse(BaseDTO):
    id: str
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: str
    status: str
    created_at: datetime
    updated_at: datetime


# Address DTOs
class AddressCreateRequest(BaseDTO):
    title: str = Field(..., example="Home")
    street_address: str
    apartment_unit: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str = "United States"
    is_default: bool = False


class AddressResponse(BaseDTO):
    id: str
    user_id: str
    title: str
    street_address: str
    apartment_unit: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str
    is_default: bool
    created_at: datetime


# Catalog DTOs
class CategoryCreateRequest(BaseDTO):
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon_url: Optional[str] = None


class CategoryResponse(BaseDTO):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool
    created_at: datetime


class BrandCreateRequest(BaseDTO):
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None


class BrandResponse(BaseDTO):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    created_at: datetime


class ProductVariantDTO(BaseDTO):
    sku: str
    variant_name: str
    price: float
    discount_price: Optional[float] = None
    stock_quantity: int = 0
    attributes: Dict[str, str] = Field(default_factory=dict)
    image_url: Optional[str] = None


class ProductCreateRequest(BaseDTO):
    title: str
    slug: str
    description: str
    category_id: str
    brand_id: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    cost_price: float
    stock_quantity: int
    attributes: Dict[str, Any] = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    variants: List[ProductVariantDTO] = Field(default_factory=list)


class ProductResponse(BaseDTO):
    id: str
    seller_id: str
    title: str
    slug: str
    description: str
    category_id: str
    brand_id: Optional[str] = None
    price: float
    discount_price: Optional[float] = None
    stock_quantity: int
    status: str
    rating_average: float
    review_count: int
    attributes: Dict[str, Any]
    images: List[str]
    created_at: datetime
    updated_at: datetime


# Cart & Wishlist DTOs
class CartItemAddRequest(BaseDTO):
    product_id: str
    variant_sku: Optional[str] = None
    quantity: int = Field(..., gt=0)


class CartItemResponse(BaseDTO):
    id: str
    product_id: str
    product_title: str
    variant_sku: Optional[str] = None
    price: float
    quantity: int
    subtotal: float
    image_url: Optional[str] = None


class CartResponse(BaseDTO):
    items: List[CartItemResponse]
    subtotal: float
    discount_total: float
    tax_total: float
    shipping_total: float
    grand_total: float
    applied_coupon_code: Optional[str] = None


# Order DTOs
class CheckoutRequest(BaseDTO):
    shipping_address_id: str
    billing_address_id: str
    payment_method: PaymentMethod
    coupon_code: Optional[str] = None
    order_notes: Optional[str] = None


class OrderItemResponse(BaseDTO):
    id: str
    product_id: str
    product_title: str
    sku: str
    unit_price: float
    quantity: int
    total_price: float


class OrderResponse(BaseDTO):
    id: str
    order_number: str
    customer_id: str
    order_status: str
    payment_status: str
    payment_method: str
    subtotal: float
    discount_amount: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    shipping_address_id: str
    tracking_number: Optional[str] = None
    items: List[OrderItemResponse]
    created_at: datetime
    updated_at: datetime


# Payment Simulator DTOs
class PaymentSimulateRequest(BaseDTO):
    order_id: str
    payment_method: PaymentMethod
    amount: float
    simulate_failure: bool = False
    card_number_last4: Optional[str] = "4242"
    upi_id: Optional[str] = "demo@megacommerce"


class PaymentSimulateResponse(BaseDTO):
    transaction_id: str
    order_id: str
    status: str
    payment_method: str
    amount: float
    timestamp: datetime
    message: str
    gateway_audit_log: Dict[str, Any]


# Delivery Simulator DTOs
class ShipmentUpdateRequest(BaseDTO):
    shipment_id: str
    status: ShipmentStatus
    location_update: Optional[str] = None
    notes: Optional[str] = None


# ML & Analytics DTOs
class SearchRequest(BaseDTO):
    query: str
    category_id: Optional[str] = None
    brand_id: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    sort_by: str = "relevance"
    page: int = 1
    page_size: int = 20


class RecommendationRequest(BaseDTO):
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    category_id: Optional[str] = None
    limit: int = 10


class FraudAssessmentResponse(BaseDTO):
    order_id: str
    risk_score: float
    risk_category: str
    flagged: bool
    risk_reasons: List[str]
    evaluation_timestamp: datetime
