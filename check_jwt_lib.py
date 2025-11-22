import sys
sys.path.insert(0, 'app')

print("=== Checking JWT Library ===\n")

try:
    from jose import jwt as jose_jwt
    print("✓ python-jose is available")
except:
    print("❌ python-jose is NOT available")

try:
    import jwt as pyjwt
    print("✓ PyJWT is available")
except:
    print("❌ PyJWT is NOT available")

print("\n=== Testing token creation with each library ===\n")

SECRET = "test-secret-key"
ALGORITHM = "HS256"
payload = {"sub": "1", "type": "access", "exp": 9999999999}

# Test python-jose
try:
    from jose import jwt as jose_jwt
    token_jose = jose_jwt.encode(payload, SECRET, algorithm=ALGORITHM)
    decoded_jose = jose_jwt.decode(token_jose, SECRET, algorithms=[ALGORITHM])
    print(f"✓ python-jose works!")
    print(f"  Token: {token_jose[:40]}...")
    print(f"  Decoded: {decoded_jose}")
except Exception as e:
    print(f"❌ python-jose failed: {e}")

# Test PyJWT
try:
    import jwt as pyjwt
    token_pyjwt = pyjwt.encode(payload, SECRET, algorithm=ALGORITHM)
    decoded_pyjwt = pyjwt.decode(token_pyjwt, SECRET, algorithms=[ALGORITHM])
    print(f"\n✓ PyJWT works!")
    print(f"  Token: {token_pyjwt[:40]}...")
    print(f"  Decoded: {decoded_pyjwt}")
except Exception as e:
    print(f"\n❌ PyJWT failed: {e}")
