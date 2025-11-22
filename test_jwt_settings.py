import sys
sys.path.insert(0, 'app')

from config.settings import settings
from jose import jwt as jose_jwt
from datetime import datetime, timedelta

print("=== Testing with actual settings ===\n")
print(f"SECRET_KEY: {settings.SECRET_KEY[:20]}...")
print(f"ALGORITHM: HS256")

# Create a test payload
exp = datetime.utcnow() + timedelta(minutes=15)
payload = {
    "sub": "1",
    "exp": int(exp.timestamp()),
    "type": "access",
    "jti": "test-jti"
}

print(f"\nPayload: {payload}")

# Encode
token = jose_jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
print(f"\nEncoded token: {token[:60]}...")

# Decode
try:
    decoded = jose_jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    print(f"\n✓ Decoded successfully!")
    print(f"Decoded payload: {decoded}")
except Exception as e:
    print(f"\n❌ Decode failed: {e}")
