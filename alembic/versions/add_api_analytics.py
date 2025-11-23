"""add api analytics

Revision ID: add_api_analytics
Revises: add_payments
Create Date: 2025-11-23 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_api_analytics'
down_revision = 'add_payments'
branch_labels = None
depends_on = None


def upgrade():
    # Create api_analytics table
    op.create_table(
        'api_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        
        # Request Information
        sa.Column('endpoint', sa.String(length=500), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('query_params', sa.Text(), nullable=True),
        
        # Response Information
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time', sa.Float(), nullable=False),
        
        # User Information
        sa.Column('user_id', sa.Integer(), nullable=True),
        
        # IP and Geolocation
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('country_code', sa.String(length=2), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        
        # Request/Response Data
        sa.Column('request_headers', sa.Text(), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        
        # Additional metadata
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('referer', sa.String(length=500), nullable=True),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Note: No foreign key to users table since it uses SQLAlchemy Core
    )
    
    # Create indexes for better query performance
    op.create_index('idx_api_analytics_id', 'api_analytics', ['id'])
    op.create_index('idx_api_analytics_endpoint', 'api_analytics', ['endpoint'])
    op.create_index('idx_api_analytics_method', 'api_analytics', ['method'])
    op.create_index('idx_api_analytics_status_code', 'api_analytics', ['status_code'])
    op.create_index('idx_api_analytics_user_id', 'api_analytics', ['user_id'])
    op.create_index('idx_api_analytics_ip_address', 'api_analytics', ['ip_address'])
    op.create_index('idx_api_analytics_city', 'api_analytics', ['city'])
    op.create_index('idx_api_analytics_country', 'api_analytics', ['country'])
    op.create_index('idx_api_analytics_created_at', 'api_analytics', ['created_at'])
    
    # Composite indexes for common query patterns
    op.create_index('idx_endpoint_method', 'api_analytics', ['endpoint', 'method'])
    op.create_index('idx_endpoint_created', 'api_analytics', ['endpoint', 'created_at'])
    op.create_index('idx_status_created', 'api_analytics', ['status_code', 'created_at'])
    op.create_index('idx_user_created', 'api_analytics', ['user_id', 'created_at'])
    op.create_index('idx_city_country', 'api_analytics', ['city', 'country'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_city_country', table_name='api_analytics')
    op.drop_index('idx_user_created', table_name='api_analytics')
    op.drop_index('idx_status_created', table_name='api_analytics')
    op.drop_index('idx_endpoint_created', table_name='api_analytics')
    op.drop_index('idx_endpoint_method', table_name='api_analytics')
    op.drop_index('idx_api_analytics_created_at', table_name='api_analytics')
    op.drop_index('idx_api_analytics_country', table_name='api_analytics')
    op.drop_index('idx_api_analytics_city', table_name='api_analytics')
    op.drop_index('idx_api_analytics_ip_address', table_name='api_analytics')
    op.drop_index('idx_api_analytics_user_id', table_name='api_analytics')
    op.drop_index('idx_api_analytics_status_code', table_name='api_analytics')
    op.drop_index('idx_api_analytics_method', table_name='api_analytics')
    op.drop_index('idx_api_analytics_endpoint', table_name='api_analytics')
    op.drop_index('idx_api_analytics_id', table_name='api_analytics')
    
    # Drop table
    op.drop_table('api_analytics')
