from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os

# Security constants — SECRET_KEY from env var (critical for SaaS security).
# Any production marker (DATABASE_URL on Render, RENDER env, or explicit
# PRICERADAR_ENV=production) forces the env var to be set. The local-dev
# fallback is deliberately random per-process so it can never be mistaken
# for a stable key, and any tokens issued locally become invalid on restart.
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    _prod_markers = ("DATABASE_URL", "RENDER", "RENDER_SERVICE_ID")
    if any(os.environ.get(k) for k in _prod_markers) or os.environ.get("PRICERADAR_ENV") == "production":
        raise RuntimeError("JWT_SECRET_KEY environment variable is required in production")
    import secrets as _secrets
    SECRET_KEY = _secrets.token_urlsafe(64)
    import logging as _logging
    _logging.getLogger("priceradar.auth").warning(
        "JWT_SECRET_KEY not set — generated a per-process ephemeral key. "
        "Tokens will be invalidated on every restart. Set JWT_SECRET_KEY for a stable dev environment."
    )
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.id == user_id).first() if user_id else \
           db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
