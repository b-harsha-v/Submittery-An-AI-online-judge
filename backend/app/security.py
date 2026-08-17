import os
from datetime import datetime, timedelta
from typing import Union, Any, Dict
from jose import jwt, JWTError
from passlib.context import CryptContext
from .config import settings
import bcrypt
if not hasattr(bcrypt, "__about__"):
    class _BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "4.1.2")
    bcrypt.__about__ = _BcryptAbout()

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
    Supports mock_ tokens for instant local developer testing,
    and validates real Google OAuth tokens via Google's tokeninfo API.
    """
    if id_token.startswith("mock_"):
        raw = id_token[5:]
        if "::" in raw:
            parts = raw.split("::")
            email = parts[0]
            username = parts[1] if len(parts) > 1 else email.split("@")[0]
            avatar_url = parts[2] if len(parts) > 2 else f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"
        elif "@" in raw:
            email = raw
            username = email.split("@")[0]
            avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"
        else:
            email = f"dev_{raw}@submittery.com"
            username = f"dev_{raw}"
            avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={username}"
            
        return {
            "email": email,
            "name": username,
            "google_id": f"google_{username}",
            "picture": avatar_url
        }
    
    # Real Google OAuth verification
    try:
        import httpx
        from .config import settings
        response = httpx.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
            if client_id:
                client_id = client_id.strip().strip('"').strip("'")
            
            # Check audience if configured
            token_aud = data.get("aud")
            if client_id and token_aud and token_aud != client_id:
                print(f"[!] Google OAuth Aud Mismatch: token aud='{token_aud}' vs configured GOOGLE_CLIENT_ID='{client_id}'")
            
            return {
                "email": data.get("email"),
                "name": data.get("name") or data.get("email", "").split("@")[0],
                "google_id": data.get("sub"),
                "picture": data.get("picture")
            }
        else:
            print(f"[!] Google OAuth token validation HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[!] Error validating Google token: {e}")
    return None
