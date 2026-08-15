import os
from datetime import datetime, timedelta
from typing import Union, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7) # Refresh token lasts 7 days
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    try:
        decoded_token = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return decoded_token
    except JWTError:
        return {}

def verify_google_oauth_token(id_token: str) -> Union[Dict[str, Any], None]:
    """
    Verifies a Google OAuth ID token.
    For local development/testing:
    If the token starts with "mock_", we return mock user details based on the string.
    Otherwise, we attempt to verify it using google-auth library if available,
    or fallback to manual HTTP verification.
    """
    if id_token.startswith("mock_"):
        # Format: mock_email_username_avatarurl (URL-safe separator)
        parts = id_token.split("_")
        email = parts[1] if len(parts) > 1 else "mockuser@gmail.com"
        username = parts[2] if len(parts) > 2 else email.split("@")[0]
        avatar_url = parts[3] if len(parts) > 3 else "https://lh3.googleusercontent.com/a/default-user"
        return {
            "email": email,
            "name": username,
            "google_id": f"google_{username}",
            "picture": avatar_url
        }
    
    # Real Google OAuth verification
    try:
        # Standard HTTP verification fallback if google-auth library is not installed
        import httpx
        response = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
        if response.status_code == 200:
            data = response.json()
            # Ensure the audience matches our client ID if configured
            if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
                return None
            return {
                "email": data.get("email"),
                "name": data.get("name", data.get("email", "").split("@")[0]),
                "google_id": data.get("sub"),
                "picture": data.get("picture")
            }
    except Exception as e:
        print(f"Error validating Google token: {e}")
    return None
