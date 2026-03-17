import bcrypt
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), hash.encode())

def create_token(admin_id: str, expires_in_days: int = 7) -> str:
    """Create JWT token for admin"""
    payload = {
        "sub": admin_id,
        "exp": datetime.utcnow() + timedelta(days=expires_in_days)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode JWT token"""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])