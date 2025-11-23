import stripe
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.orm_models.payment import Order, Payment, Transaction, Coupon, OrderStatus, PaymentStatus
from app.services.audit_service import audit_service
import secrets
import string

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class PaymentService:
    """Service for handling payment processing with Stripe"""
    
    def generate_order_number(self) -> str:
        """Generate a unique order number"""
        timestamp = datetime.now().strftime('%Y%m%d')
        random_str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        return f"ORD-{timestamp}-{random_str}"
    
    async def create_order(
        self,
        db: Session,
        user_id: int,
        course_id: int,
        amount: float,
        coupon_code: Optional[str] = None
    ) -> Order:
        """Create a new order"""
        # Calculate discount if coupon provided
        discount_amount = 0.0
        if coupon_code:
            coupon = db.query(Coupon).filter(
                Coupon.code == coupon_code,
                Coupon.is_active == True
            ).first()
            
            if coupon:
                if coupon.discount_type == "percentage":
                    discount_amount = amount * (coupon.discount_value / 100)
                    if coupon.max_discount:
                        discount_amount = min(discount_amount, coupon.max_discount)
                elif coupon.discount_type == "fixed":
                    discount_amount = min(coupon.discount_value, amount)
                
                # Update coupon usage
                coupon.used_count += 1
                db.commit()
        
        total_amount = amount - discount_amount
        
        # Create order
        order = Order(
            user_id=user_id,
            course_id=course_id,
            order_number=self.generate_order_number(),
            status=OrderStatus.PENDING,
            amount=amount,
            currency="USD",
            discount_amount=discount_amount,
            tax_amount=0.0,
            total_amount=total_amount,
            coupon_code=coupon_code
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        await audit_service.log(
            db=db,
            user_id=user_id,
            action="order_created",
            resource_type="order",
            resource_id=str(order.id),
            details=f"Order {order.order_number} created for course ID {course_id}"
        )
        
        return order
    
    async def create_payment_intent(
        self,
        db: Session,
        order: Order,
        user_email: str
    ) -> Dict[str, Any]:
        """Create a Stripe Payment Intent"""
        try:
            # Create or retrieve Stripe customer
            customer = stripe.Customer.create(
                email=user_email,
                metadata={
                    "user_id": order.user_id,
                    "order_id": order.id
                }
            )
            
            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),  # Convert to cents
                currency=order.currency.lower(),
                customer=customer.id,
                metadata={
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "user_id": order.user_id,
                    "course_id": order.course_id
                },
                description=f"Course purchase - Order {order.order_number}"
            )
            
            # Create payment record
            payment = Payment(
                order_id=order.id,
                payment_method="card",
                status=PaymentStatus.PENDING,
                stripe_payment_intent_id=intent.id,
                stripe_customer_id=customer.id,
                amount=order.total_amount,
                currency=order.currency
            )
            
            db.add(payment)
            db.commit()
            
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "publishable_key": settings.STRIPE_PUBLISHABLE_KEY
            }
            
        except stripe.error.StripeError as e:
            await audit_service.log(
                db=db,
                user_id=order.user_id,
                action="payment_intent_failed",
                resource_type="payment",
                resource_id=str(order.id),
                details=f"Stripe error: {str(e)}"
            )
            raise Exception(f"Payment processing error: {str(e)}")
    
    async def confirm_payment(
        self,
        db: Session,
        payment_intent_id: str
    ) -> Optional[Order]:
        """Confirm payment and update order status"""
        # Get payment record
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()
        
        if not payment:
            return None
        
        # Retrieve payment intent from Stripe
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if intent.status == "succeeded":
                # Update payment
                payment.status = PaymentStatus.COMPLETED
                payment.stripe_charge_id = intent.latest_charge
                payment.completed_at = datetime.utcnow()
                
                # Update order
                order = db.query(Order).filter(Order.id == payment.order_id).first()
                if order:
                    order.status = OrderStatus.CONFIRMED
                    order.completed_at = datetime.utcnow()
                    
                    # Create transaction record
                    transaction = Transaction(
                        user_id=order.user_id,
                        order_id=order.id,
                        transaction_type="purchase",
                        amount=order.total_amount,
                        currency=order.currency,
                        status="completed",
                        description=f"Course purchase - Order {order.order_number}",
                        stripe_transaction_id=intent.id
                    )
                    db.add(transaction)
                    
                    await audit_service.log(
                        db=db,
                        user_id=order.user_id,
                        action="payment_completed",
                        resource_type="order",
                        resource_id=str(order.id),
                        details=f"Payment completed for order {order.order_number}"
                    )
                
                db.commit()
                db.refresh(order)
                return order
            else:
                payment.status = PaymentStatus.FAILED
                payment.failure_reason = f"Payment status: {intent.status}"
                db.commit()
                return None
                
        except stripe.error.StripeError as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            db.commit()
            return None
    
    async def process_webhook(
        self,
        db: Session,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle different event types
            if event.type == "payment_intent.succeeded":
                payment_intent = event.data.object
                await self.confirm_payment(db, payment_intent.id)
                
            elif event.type == "payment_intent.payment_failed":
                payment_intent = event.data.object
                payment = db.query(Payment).filter(
                    Payment.stripe_payment_intent_id == payment_intent.id
                ).first()
                
                if payment:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = payment_intent.last_payment_error.message if payment_intent.last_payment_error else "Unknown error"
                    
                    order = db.query(Order).filter(Order.id == payment.order_id).first()
                    if order:
                        order.status = OrderStatus.FAILED
                    
                    db.commit()
            
            elif event.type == "charge.refunded":
                charge = event.data.object
                payment = db.query(Payment).filter(
                    Payment.stripe_charge_id == charge.id
                ).first()
                
                if payment:
                    payment.status = PaymentStatus.REFUNDED
                    order = db.query(Order).filter(Order.id == payment.order_id).first()
                    
                    if order:
                        order.status = OrderStatus.REFUNDED
                        
                        # Create refund transaction
                        transaction = Transaction(
                            user_id=order.user_id,
                            order_id=order.id,
                            transaction_type="refund",
                            amount=order.total_amount,
                            currency=order.currency,
                            status="completed",
                            description=f"Refund for order {order.order_number}",
                            stripe_transaction_id=charge.id
                        )
                        db.add(transaction)
                    
                    db.commit()
            
            return {"status": "success", "event_type": event.type}
            
        except ValueError as e:
            return {"status": "error", "message": f"Invalid payload: {str(e)}"}
        except stripe.error.SignatureVerificationError as e:
            return {"status": "error", "message": f"Invalid signature: {str(e)}"}
    
    async def create_refund(
        self,
        db: Session,
        order_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """Process a refund for an order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != OrderStatus.CONFIRMED:
            return False
        
        payment = db.query(Payment).filter(
            Payment.order_id == order_id,
            Payment.status == PaymentStatus.COMPLETED
        ).first()
        
        if not payment or not payment.stripe_charge_id:
            return False
        
        try:
            # Create refund in Stripe
            refund = stripe.Refund.create(
                charge=payment.stripe_charge_id,
                reason=reason or "requested_by_customer"
            )
            
            # Update payment and order
            payment.status = PaymentStatus.REFUNDED
            order.status = OrderStatus.REFUNDED
            
            # Create refund transaction
            transaction = Transaction(
                user_id=order.user_id,
                order_id=order.id,
                transaction_type="refund",
                amount=order.total_amount,
                currency=order.currency,
                status="completed",
                description=f"Refund for order {order.order_number}",
                stripe_transaction_id=refund.id
            )
            db.add(transaction)
            
            await audit_service.log(
                db=db,
                user_id=order.user_id,
                action="refund_processed",
                resource_type="order",
                resource_id=str(order.id),
                details=f"Refund processed for order {order.order_number}"
            )
            
            db.commit()
            return True
            
        except stripe.error.StripeError as e:
            await audit_service.log(
                db=db,
                user_id=order.user_id,
                action="refund_failed",
                resource_type="order",
                resource_id=str(order.id),
                details=f"Refund failed: {str(e)}"
            )
            return False
    
    def validate_coupon(
        self,
        db: Session,
        code: str,
        user_id: int,
        course_id: Optional[int] = None
    ) -> Optional[Coupon]:
        """Validate a coupon code"""
        coupon = db.query(Coupon).filter(
            Coupon.code == code,
            Coupon.is_active == True
        ).first()
        
        if not coupon:
            return None
        
        # Check validity dates
        now = datetime.utcnow()
        if coupon.valid_from and coupon.valid_from > now:
            return None
        if coupon.valid_until and coupon.valid_until < now:
            return None
        
        # Check max uses
        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            return None
        
        # Check course-specific
        if coupon.course_id and coupon.course_id != course_id:
            return None
        
        # Check per-user limit
        if coupon.max_uses_per_user:
            user_usage = db.query(Order).filter(
                Order.user_id == user_id,
                Order.coupon_code == code
            ).count()
            
            if user_usage >= coupon.max_uses_per_user:
                return None
        
        return coupon


payment_service = PaymentService()
