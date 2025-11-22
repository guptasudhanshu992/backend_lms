import sys
sys.path.insert(0, '.')

from app.core.security import hash_password, verify_password
import sqlite3

# Test password
password = "SecureAdminPassword123!"
print(f"Testing password: {password}")

# Hash it
hashed = hash_password(password)
print(f"New hash: {hashed[:50]}...")

# Verify it works
verified = verify_password(password, hashed)
print(f"Verification test: {verified}")

# Update admin user in database
conn = sqlite3.connect('dev.db')
cursor = conn.cursor()

cursor.execute("UPDATE users SET hashed_password = ? WHERE email = 'admin@example.com'", (hashed,))
conn.commit()

print(f"\nAdmin password updated successfully!")

# Verify the update
cursor.execute("SELECT hashed_password FROM users WHERE email = 'admin@example.com'")
stored_hash = cursor.fetchone()[0]
can_login = verify_password(password, stored_hash)
print(f"Can login with new password: {can_login}")

conn.close()
