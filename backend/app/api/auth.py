from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from ..database import get_db
from ..models.user import User, UserRole
from ..schemas.user import UserCreate, UserResponse, Token, GoogleLoginRequest, UserProfileUpdate
from ..security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_google_oauth_token,
    decode_token
)
from .deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/config")
def get_auth_config():
    from ..config import settings
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if client_id:
        client_id = client_id.strip().strip('"').strip("'")
    return {"google_client_id": client_id}

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This username is already taken"
        )
    
    # Generate robot avatar url
    avatar_url = f"https://api.dicebear.com/7.x/bottts/svg?seed={user_in.username}"
    
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        avatar_url=avatar_url,
        role=UserRole.USER
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Authenticate user by email or username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email/username or password"
        )
        
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
        
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/google", response_model=Token)
def google_login(login_req: GoogleLoginRequest, db: Session = Depends(get_db)):
    import re
    # Verify Google token (supports mock_ for testing and real Google tokens)
    google_profile = verify_google_oauth_token(login_req.id_token)
    if not google_profile or not google_profile.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google OAuth token or email could not be verified"
        )
        
    email = google_profile["email"]
    google_id = google_profile["google_id"]
    name = google_profile.get("name") or email.split("@")[0]
    picture = google_profile.get("picture")
    
    # Check if user already exists
    user = db.query(User).filter((User.email == email) | (User.google_id == google_id)).first()
    
    if not user:
        # Create a clean alphanumeric username
        clean_base = re.sub(r'[^a-zA-Z0-9_]', '', name.replace(" ", "_").lower())
        if not clean_base:
            clean_base = email.split("@")[0]
            
        username = clean_base
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{clean_base}_{counter}"
            counter += 1
            
        user = User(
            email=email,
            username=username,
            google_id=google_id,
            avatar_url=picture,
            role=UserRole.USER
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Link google_id or avatar if not yet present
        if not user.google_id:
            user.google_id = google_id
        if picture and not user.avatar_url:
            user.avatar_url = picture
        db.commit()
        db.refresh(user)
        
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if profile_in.username:
        if profile_in.username != current_user.username:
            if db.query(User).filter(User.username == profile_in.username).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken"
                )
            current_user.username = profile_in.username

    if profile_in.email:
        if profile_in.email != current_user.email:
            if db.query(User).filter(User.email == profile_in.email).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A user with this email already exists"
                )
            current_user.email = profile_in.email

    if profile_in.avatar_url is not None:
        current_user.avatar_url = profile_in.avatar_url

    if profile_in.password:
        current_user.hashed_password = hash_password(profile_in.password)

    db.commit()
    db.refresh(current_user)
    return current_user

