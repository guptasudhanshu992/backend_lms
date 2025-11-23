from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# Order schemas
class OrderCreate(BaseModel):
    course_id: int
    coupon_code: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    order_number: str
    status: OrderStatusEnum
    amount: float
    currency: str
    discount_amount: float
    tax_amount: float
    total_amount: float
    coupon_code: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class OrderWithDetails(OrderResponse):
    course_title: Optional[str] = None
    user_email: Optional[str] = None


# Payment schemas
class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    publishable_key: str


class PaymentConfirmRequest(BaseModel):
    payment_intent_id: str


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    payment_method: str
    status: PaymentStatusEnum
    amount: float
    currency: str
    stripe_payment_intent_id: Optional[str]
    stripe_charge_id: Optional[str]
    receipt_url: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Transaction schemas
class TransactionResponse(BaseModel):
    id: int
    user_id: int
    order_id: Optional[int]
    transaction_type: str
    amount: float
    currency: str
    status: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# Coupon schemas
class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = None
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: float = Field(..., gt=0)
    max_discount: Optional[float] = None
    max_uses: Optional[int] = None
    max_uses_per_user: int = 1
    is_active: bool = True
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    course_id: Optional[int] = None


class CouponUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
    max_uses: Optional[int] = None
    valid_until: Optional[datetime] = None


class CouponResponse(BaseModel):
    id: int
    code: str
    description: Optional[str]
    discount_type: str
    discount_value: float
    max_discount: Optional[float]
    max_uses: Optional[int]
    used_count: int
    max_uses_per_user: int
    is_active: bool
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    course_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CouponValidateRequest(BaseModel):
    code: str
    course_id: Optional[int] = None


class CouponValidateResponse(BaseModel):
    valid: bool
    discount_type: Optional[str] = None
    discount_value: Optional[float] = None
    max_discount: Optional[float] = None
    message: Optional[str] = None


# Refund schema
class RefundRequest(BaseModel):
    order_id: int
    reason: Optional[str] = None


# Revenue statistics
class RevenueStats(BaseModel):
    total_revenue: float
    total_orders: int
    successful_orders: int
    failed_orders: int
    refunded_orders: int
    pending_orders: int
    average_order_value: float


class DashboardStats(BaseModel):
    revenue: RevenueStats
    recent_orders: List[OrderWithDetails]
    top_courses: List[dict]
