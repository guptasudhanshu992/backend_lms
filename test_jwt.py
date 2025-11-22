import sys
sys.path.insert(0, 'app')

from core.jwt import create_access_token, decode_token
from datetime import datetime

# Test token creation and decoding
print("=== JWT Debug Test ===\n")

# Create a token
user_id = "1"
print(f"Creating access token for user_id: {user_id}")
token = create_access_token(user_id)
print(f"Token created: {token[:50]}...")

# Decode the token
print(f"\nDecoding token...")
payload = decode_token(token)

if payload:
    print(f"✓ Token decoded successfully!")
    print(f"  Payload: {payload}")
    print(f"  Subject (user_id): {payload.get('sub')}")
    print(f"  Token type: {payload.get('type')}")
    print(f"  Expiry: {datetime.fromtimestamp(payload.get('exp'))}")
    print(f"  Current time: {datetime.utcnow()}")
    
    if payload.get('type') == 'access':
        print(f"✓ Token type is correct (access)")
    else:
        print(f"❌ Token type is wrong: {payload.get('type')}")
else:
    print(f"❌ Token decode failed!")
