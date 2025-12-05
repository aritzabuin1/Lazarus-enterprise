from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
from app.domain.models import Token, User, UserCreate, TokenData
from app.database import supabase
from app.logger import logger

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    # Fetch user from Supabase
    # Note: In a real app, use a proper Repo. Direct Supabase call for MVP.
    response = supabase.table("users").select("*").eq("email", token_data.email).execute()
    if not response.data:
        raise credentials_exception
    
    user_dict = response.data[0]
    return User(**user_dict)

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    # 1. Fetch user
    response = supabase.table("users").select("*").eq("email", form_data.username).execute()
    if not response.data:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    user_dict = response.data[0]
    user = User(**user_dict)
    
    # 2. Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    # 3. Create token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate):
    # Check if user exists
    existing = supabase.table("users").select("id").eq("email", user_in.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_in.password)
    
    user_data = {
        "email": user_in.email,
        "hashed_password": hashed_password,
        "full_name": user_in.full_name,
        "is_active": user_in.is_active,
        "is_superuser": user_in.is_superuser
    }
    
    res = supabase.table("users").insert(user_data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create user")
        
    return User(**res.data[0])

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
