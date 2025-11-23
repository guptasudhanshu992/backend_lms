from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List
from app.db.database import get_db
from app.core.dependencies import get_current_user, require_admin
from app.services.payment_service import payment_service
from app.schemas.payment import (
    OrderCreate, OrderResponse, OrderWithDetails,
    PaymentIntentResponse, PaymentConfirmRequest, PaymentResponse,
    TransactionResponse, CouponCreate, CouponUpdate, CouponResponse,
    CouponValidateRequest, CouponValidateResponse, RefundRequest,
    RevenueStats, DashboardStats
)
from app.orm_models.payment import Order, Payment, Transaction, Coupon, OrderStatus, PaymentStatus

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new order for a course"""
    # Check if course exists
    course = db.query(Course).filter(Course.id == order_data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Check if user already purchased this course
    existing_order = db.query(Order).filter(
        Order.user_id == current_user["id"],
        Order.course_id == order_data.course_id,
        Order.status == OrderStatus.CONFIRMED
    ).first()
    
    if existing_order:
        raise HTTPException(status_code=400, detail="You already own this course")
    
    # Check if course is free
    if course.price == 0:
        # Create completed order for free course
        order = await payment_service.create_order(
            db=db,
            user_id=current_user["id"],
            course_id=course.id,
            amount=0.0,
            coupon_code=None
        )
        order.status = OrderStatus.CONFIRMED
        order.completed_at = func.now()
        db.commit()
        db.refresh(order)
        return order
    
    # Create order
    order = await payment_service.create_order(
        db=db,
        user_id=current_user["id"],
        course_id=course.id,
        amount=course.price,
        coupon_code=order_data.coupon_code
    )
    
    return order


@router.post("/orders/{order_id}/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a Stripe Payment Intent for an order"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["id"]
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not pending")
    
    try:
        payment_intent = await payment_service.create_payment_intent(
            db=db,
            order=order,
            user_email=current_user["email"]
        )
        return payment_intent
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm", response_model=OrderResponse)
async def confirm_payment(
    confirm_data: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Confirm a payment after successful Stripe payment"""
    order = await payment_service.confirm_payment(
        db=db,
        payment_intent_id=confirm_data.payment_intent_id
    )
    
    if not order:
        raise HTTPException(status_code=404, detail="Payment not found or failed")
    
    return order


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    result = await payment_service.process_webhook(
        db=db,
        payload=payload,
        signature=signature
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result


@router.get("/orders", response_model=List[OrderResponse])
async def get_my_orders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's orders"""
    orders = db.query(Order).filter(
        Order.user_id == current_user["id"]
    ).order_by(desc(Order.created_at)).all()
    
    return orders


@router.get("/orders/{order_id}", response_model=OrderWithDetails)
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get order details"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user["id"]
    ).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get course and user details
    course = db.query(Course).filter(Course.id == order.course_id).first()
    
    order_dict = OrderWithDetails.model_validate(order).model_dump()
    order_dict["course_title"] = course.title if course else None
    order_dict["user_email"] = current_user["email"]
    
    return order_dict


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_my_transactions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's transactions"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user["id"]
    ).order_by(desc(Transaction.created_at)).all()
    
    return transactions


@router.post("/coupons/validate", response_model=CouponValidateResponse)
async def validate_coupon(
    validate_data: CouponValidateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate a coupon code"""
    coupon = payment_service.validate_coupon(
        db=db,
        code=validate_data.code,
        user_id=current_user["id"],
        course_id=validate_data.course_id
    )
    
    if not coupon:
        return CouponValidateResponse(
            valid=False,
            message="Invalid or expired coupon code"
        )
    
    return CouponValidateResponse(
        valid=True,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        max_discount=coupon.max_discount,
        message="Coupon is valid"
    )


# Admin endpoints
@router.get("/admin/orders", response_model=List[OrderWithDetails])
async def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all orders (admin only)"""
    orders = db.query(Order).order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    
    # Enrich with course and user details
    result = []
    for order in orders:
        course = db.query(Course).filter(Course.id == order.course_id).first()
        user = db.query(User).filter(User.id == order.user_id).first()
        
        order_dict = OrderWithDetails.model_validate(order).model_dump()
        order_dict["course_title"] = course.title if course else None
        order_dict["user_email"] = user.email if user else None
        result.append(order_dict)
    
    return result


@router.get("/admin/stats", response_model=DashboardStats)
async def get_payment_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get payment statistics (admin only)"""
    # Revenue stats
    total_orders = db.query(Order).count()
    successful_orders = db.query(Order).filter(Order.status == OrderStatus.CONFIRMED).count()
    failed_orders = db.query(Order).filter(Order.status == OrderStatus.FAILED).count()
    refunded_orders = db.query(Order).filter(Order.status == OrderStatus.REFUNDED).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    
    total_revenue = db.query(func.sum(Order.total_amount)).filter(
        Order.status == OrderStatus.CONFIRMED
    ).scalar() or 0.0
    
    average_order_value = total_revenue / successful_orders if successful_orders > 0 else 0.0
    
    revenue_stats = RevenueStats(
        total_revenue=total_revenue,
        total_orders=total_orders,
        successful_orders=successful_orders,
        failed_orders=failed_orders,
        refunded_orders=refunded_orders,
        pending_orders=pending_orders,
        average_order_value=average_order_value
    )
    
    # Recent orders
    recent_orders_query = db.query(Order).order_by(desc(Order.created_at)).limit(10).all()
    recent_orders = []
    for order in recent_orders_query:
        course = db.query(Course).filter(Course.id == order.course_id).first()
        user = db.query(User).filter(User.id == order.user_id).first()
        
        order_dict = OrderWithDetails.model_validate(order).model_dump()
        order_dict["course_title"] = course.title if course else None
        order_dict["user_email"] = user.email if user else None
        recent_orders.append(order_dict)
    
    # Top courses by revenue
    top_courses_query = db.query(
        Course.id,
        Course.title,
        func.count(Order.id).label("sales_count"),
        func.sum(Order.total_amount).label("revenue")
    ).join(Order).filter(
        Order.status == OrderStatus.CONFIRMED
    ).group_by(Course.id, Course.title).order_by(desc("revenue")).limit(5).all()
    
    top_courses = [
        {
            "course_id": row[0],
            "course_title": row[1],
            "sales_count": row[2],
            "revenue": row[3]
        }
        for row in top_courses_query
    ]
    
    return DashboardStats(
        revenue=revenue_stats,
        recent_orders=recent_orders,
        top_courses=top_courses
    )


@router.post("/admin/refund", response_model=dict)
async def process_refund(
    refund_data: RefundRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Process a refund for an order (admin only)"""
    success = await payment_service.create_refund(
        db=db,
        order_id=refund_data.order_id,
        reason=refund_data.reason
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Refund failed")
    
    return {"message": "Refund processed successfully"}


@router.post("/admin/coupons", response_model=CouponResponse)
async def create_coupon(
    coupon_data: CouponCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Create a new coupon (admin only)"""
    # Check if code already exists
    existing = db.query(Coupon).filter(Coupon.code == coupon_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")
    
    coupon = Coupon(**coupon_data.model_dump())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    
    return coupon


@router.get("/admin/coupons", response_model=List[CouponResponse])
async def get_all_coupons(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Get all coupons (admin only)"""
    coupons = db.query(Coupon).order_by(desc(Coupon.created_at)).all()
    return coupons


@router.put("/admin/coupons/{coupon_id}", response_model=CouponResponse)
async def update_coupon(
    coupon_id: int,
    coupon_data: CouponUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Update a coupon (admin only)"""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    for key, value in coupon_data.model_dump(exclude_unset=True).items():
        setattr(coupon, key, value)
    
    db.commit()
    db.refresh(coupon)
    
    return coupon


@router.delete("/admin/coupons/{coupon_id}")
async def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_admin)
):
    """Delete a coupon (admin only)"""
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    db.delete(coupon)
    db.commit()
    
    return {"message": "Coupon deleted successfully"}
