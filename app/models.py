import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func

metadata = sqlalchemy.MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, unique=True, nullable=False),
    Column("hashed_password", String, nullable=True),
    Column("full_name", String, nullable=True),
    Column("is_active", Boolean, default=False),
    Column("is_verified", Boolean, default=False),
    Column("role", String, default="student"),
    Column("consent", Boolean, default=False),
    Column("two_factor_enabled", Boolean, default=False),
    Column("two_factor_secret", String, nullable=True),
    Column("profile_picture", String, nullable=True),
    Column("oauth_provider", String, nullable=True),
    Column("oauth_provider_id", String, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("updated_at", DateTime, server_default=func.now(), onupdate=func.now()),
    Column("last_login", DateTime, nullable=True),
)

roles = Table(
    "roles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True, nullable=False),
    Column("description", String, nullable=True),
    Column("permissions", Text, default="[]"),
    Column("created_at", DateTime, server_default=func.now()),
)

groups = Table(
    "groups",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True, nullable=False),
    Column("description", String, nullable=True),
    Column("permissions", Text, default="[]"),
    Column("created_at", DateTime, server_default=func.now()),
)

user_groups = Table(
    "user_groups",
    metadata,
    Column("user_id", Integer, nullable=False),
    Column("group_id", Integer, nullable=False),
)

user_permissions = Table(
    "user_permissions",
    metadata,
    Column("user_id", Integer, nullable=False),
    Column("permission", String, nullable=False),
)

sessions = Table(
    "sessions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("refresh_token", String, unique=True, nullable=True),
    Column("user_agent", String, nullable=True),
    Column("ip", String, nullable=True),
    Column("device_info", String, nullable=True),
    Column("created_at", DateTime, server_default=func.now()),
    Column("last_active_at", DateTime, server_default=func.now(), onupdate=func.now()),
    Column("expires_at", DateTime, nullable=True),
    Column("revoked", Boolean, default=False),
)

audit_logs = Table(
    "audit_logs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=True),
    Column("action", String, nullable=False),
    Column("resource", String, nullable=True),
    Column("ip", String, nullable=True),
    Column("user_agent", String, nullable=True),
    Column("status", String, default="success"),
    Column("meta", Text, default="{}"),
    Column("created_at", DateTime, server_default=func.now()),
)

password_reset_tokens = Table(
    "password_reset_tokens",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("token", String, unique=True, nullable=False),
    Column("expires_at", DateTime, nullable=False),
    Column("used", Boolean, default=False),
    Column("created_at", DateTime, server_default=func.now()),
)

email_verification_tokens = Table(
    "email_verification_tokens",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, nullable=False),
    Column("token", String, unique=True, nullable=False),
    Column("expires_at", DateTime, nullable=False),
    Column("verified", Boolean, default=False),
    Column("created_at", DateTime, server_default=func.now()),
)
