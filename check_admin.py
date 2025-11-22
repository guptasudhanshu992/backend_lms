import sqlite3
import sys

conn = sqlite3.connect('dev.db')
cursor = conn.cursor()

# Check if admin user exists
cursor.execute("SELECT id, email, role, is_active, is_verified, hashed_password FROM users WHERE email = 'admin@example.com'")
admin = cursor.fetchone()

if admin:
    print(f"Admin user found:")
    print(f"  ID: {admin[0]}")
    print(f"  Email: {admin[1]}")
    print(f"  Role: {admin[2]}")
    print(f"  Active: {admin[3]}")
    print(f"  Verified: {admin[4]}")
    print(f"  Has password: {bool(admin[5])}")
    print(f"  Password hash starts with: {admin[5][:20] if admin[5] else 'None'}")
else:
    print("Admin user NOT found in database!")
    print("\nAll users:")
    cursor.execute("SELECT id, email, role FROM users")
    for row in cursor.fetchall():
        print(f"  {row}")

conn.close()
