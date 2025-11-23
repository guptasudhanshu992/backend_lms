from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # No FK - users table is SQLAlchemy Core
    course_id = Column(Integer, nullable=False, index=True)  # No FK - courses table is SQLAlchemy Core
    
    # Order details
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Pricing
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Coupon/Discount
    coupon_code = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    payments = relationship("Payment", back_populates="order")
    
    def __repr__(self):
        return f"<Order {self.order_number} - {self.status.value}>"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Stripe details
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False, index=True)
    stripe_charge_id = Column(String(255), nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(String(50), nullable=True)
    
    # Failure/Error info
    failure_code = Column(String(50), nullable=True)
    failure_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.stripe_payment_intent_id} - {self.status.value}>"


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # No FK - users table is SQLAlchemy Core
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # purchase, refund, withdrawal
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Status and metadata
    status = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON string for additional data (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Stripe reference
    stripe_transaction_id = Column(String(255), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Transaction {self.transaction_type} - {self.amount} {self.currency}>"


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    
    # Coupon details
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), nullable=False)  # 'percentage' or 'fixed'
    discount_value = Column(Float, nullable=False)
    max_discount = Column(Float, nullable=True)  # Max discount amount (for percentage)
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)  # null = unlimited
    used_count = Column(Integer, default=0, nullable=False)
    max_uses_per_user = Column(Integer, default=1, nullable=False)
    
    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Coupon {self.code} - {self.discount_value}{' %' if self.discount_type == 'percentage' else self.currency}>"
