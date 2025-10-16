"""Authentication configuration using NextAuth JWT validation."""
import os
from dotenv import load_dotenv
from fastapi_nextauth_jwt import NextAuthJWT

# Load environment variables from .env file
load_dotenv()

# Initialize NextAuth JWT validator
# This will automatically read AUTH_SECRET from environment variables
auth_secret = os.getenv("AUTH_SECRET")
if not auth_secret:
    raise ValueError("AUTH_SECRET environment variable is not set")

print(f"[Auth] Using AUTH_SECRET FULL: {auth_secret}")  # Full secret for debugging
print(f"[Auth] AUTH_SECRET byte length: {len(auth_secret.encode('utf-8'))}")

JWT = NextAuthJWT(
    secret=auth_secret,  # Must match your Next.js NEXTAUTH_SECRET
    cookie_name="next-auth.session-token",  # Must match Next.js cookie name
)

