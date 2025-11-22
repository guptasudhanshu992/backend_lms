import os
import hmac
import hashlib
import base64

try:
    from passlib.context import CryptContext

    # Use argon2 instead of bcrypt for better security
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

except Exception:
    # Fallback implementation using PBKDF2-HMAC-SHA256 (pure Python)
    # Format: pbkdf2_sha256$<iterations>$<salt_b64>$<hash_b64>
    DEFAULT_PBKDF2_ITERATIONS = 260000

    def _pbkdf2_hash(password: str, salt: bytes, iterations: int = DEFAULT_PBKDF2_ITERATIONS) -> bytes:
        return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)

    def hash_password(password: str) -> str:
        salt = os.urandom(16)
        iterations = DEFAULT_PBKDF2_ITERATIONS
        dk = _pbkdf2_hash(password, salt, iterations)
        return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

    def verify_password(plain: str, hashed: str) -> bool:
        try:
            parts = hashed.split('$')
            if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
                # unsupported format
                return False
            iterations = int(parts[1])
            salt = base64.b64decode(parts[2])
            dk = base64.b64decode(parts[3])
            computed = _pbkdf2_hash(plain, salt, iterations)
            return hmac.compare_digest(computed, dk)
        except Exception:
            return False
