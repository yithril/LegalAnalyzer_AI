"""Script to create test users for development."""
import asyncio
from core.models.user import User, UserRole
from services.auth_service import AuthService
from infrastructure.database import db_provider


async def create_test_users():
    """Create test users with different roles."""
    
    # Initialize database
    await db_provider.init()
    
    test_users = [
        {
            "email": "admin@test.com",
            "password": "admin123",
            "full_name": "Admin User",
            "role": UserRole.ADMIN
        },
        {
            "email": "analyst@test.com",
            "password": "analyst123",
            "full_name": "Analyst User",
            "role": UserRole.ANALYST
        },
        {
            "email": "user@test.com",
            "password": "user123",
            "full_name": "Regular User",
            "role": UserRole.USER
        },
    ]
    
    for user_data in test_users:
        # Check if user already exists
        existing = await User.get_or_none(email=user_data["email"])
        
        if existing:
            print(f"[OK] User {user_data['email']} already exists")
            continue
        
        # Hash password
        password_hash = AuthService.hash_password(user_data["password"])
        
        # Create user
        user = await User.create(
            email=user_data["email"],
            password_hash=password_hash,
            full_name=user_data["full_name"],
            role=user_data["role"],
            is_active=True
        )
        
        print(f"[OK] Created user: {user.email} (role: {user.role.value})")
    
    print("\n Test users created successfully!")
    print("\nLogin credentials:")
    print("=" * 50)
    for user_data in test_users:
        print(f"Email: {user_data['email']}")
        print(f"Password: {user_data['password']}")
        print(f"Role: {user_data['role'].value}")
        print("-" * 50)
    
    # Close database
    await db_provider.close()


if __name__ == "__main__":
    asyncio.run(create_test_users())

