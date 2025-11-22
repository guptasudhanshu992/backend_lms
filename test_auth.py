import requests
import json

API_BASE = "http://localhost:8000"

# Test login and blog creation
def test_auth_flow():
    print("=== Testing Auth Flow ===\n")
    
    # Step 1: Login
    print("1. Logging in as admin...")
    login_response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": "admin@example.com", "password": "SecureAdminPassword123!"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    user = login_data.get("user")
    
    print(f"✓ Login successful!")
    print(f"  User: {user.get('email')} (Role: {user.get('role')})")
    print(f"  Token: {token[:30]}...")
    
    # Step 2: Test fetching blogs
    print("\n2. Fetching blogs with token...")
    headers = {"Authorization": f"Bearer {token}"}
    
    blogs_response = requests.get(f"{API_BASE}/api/admin/blogs", headers=headers)
    
    if blogs_response.status_code != 200:
        print(f"❌ Fetch blogs failed: {blogs_response.status_code}")
        print(blogs_response.text)
        return
    
    blogs_data = blogs_response.json()
    print(f"✓ Fetch blogs successful!")
    print(f"  Total blogs: {len(blogs_data.get('blogs', []))}")
    
    # Step 3: Test creating a blog
    print("\n3. Creating a new blog...")
    new_blog = {
        "title": "Test Blog via API",
        "excerpt": "This is a test blog created via direct API call",
        "content": "Full content of the test blog post...",
        "author": "Test Author",
        "category": "Market Analysis",
        "image_url": "https://via.placeholder.com/600x400",
        "published": True
    }
    
    create_response = requests.post(
        f"{API_BASE}/api/admin/blogs",
        headers=headers,
        json=new_blog
    )
    
    if create_response.status_code not in [200, 201]:
        print(f"❌ Create blog failed: {create_response.status_code}")
        print(create_response.text)
        return
    
    print(f"✓ Create blog successful!")
    print(f"  Response: {create_response.json()}")
    
    print("\n=== All tests passed! ===")

if __name__ == "__main__":
    test_auth_flow()
