from datetime import datetime, timedelta
from typing import Any, Union, Optional
import hashlib
import hmac
try:
    from jose import jwt
except ImportError:
    import jwt
from app.core.config import settings

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with secret key salt for zero-dependency reliability."""
    return hmac.new(settings.SECRET_KEY.encode(), password.encode(), hashlib.sha256).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password hash."""
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

def create_access_token(subject: Union[str, Any], tenant_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": str(role)
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
