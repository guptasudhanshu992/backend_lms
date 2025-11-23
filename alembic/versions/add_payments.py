"""Add payment tables

Revision ID: add_payments
Create Date: 2025-11-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_payments'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('discount_amount', sa.Float(), nullable=True),
        sa.Column('tax_amount', sa.Float(), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('coupon_code', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        # Note: No FK constraints - users and courses tables use SQLAlchemy Core
    )
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_charge_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], )
    )
    op.create_index(op.f('ix_payments_stripe_payment_intent_id'), 'payments', ['stripe_payment_intent_id'], unique=True)

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),  # Renamed from metadata to avoid SQLAlchemy conflict
        sa.Column('stripe_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], )
        # Note: No FK to users table - it uses SQLAlchemy Core
    )
    op.create_index(op.f('ix_transactions_stripe_transaction_id'), 'transactions', ['stripe_transaction_id'], unique=False)

    # Create coupons table
    op.create_table(
        'coupons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discount_type', sa.String(length=20), nullable=False),
        sa.Column('discount_value', sa.Float(), nullable=False),
        sa.Column('max_discount', sa.Float(), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('used_count', sa.Integer(), nullable=True),
        sa.Column('max_uses_per_user', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], )
    )
    op.create_index(op.f('ix_coupons_code'), 'coupons', ['code'], unique=True)


def downgrade():
    op.drop_index(op.f('ix_coupons_code'), table_name='coupons')
    op.drop_table('coupons')
    op.drop_index(op.f('ix_transactions_stripe_transaction_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_payments_stripe_payment_intent_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_orders_order_number'), table_name='orders')
    op.drop_table('orders')
