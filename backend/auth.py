from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models
import os

# Cookie carrying the JWT. Set HttpOnly / Secure / SameSite=None in
# production so XSS can't read it and CSRF is mitigated by Origin
# checks + the browser's SameSite rules. Name is intentionally distinct
# from the old localStorage key so stale js-cookie values can't collide.
ACCESS_TOKEN_COOKIE = "pr_access_token"

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


def _is_production() -> bool:
    return bool(os.environ.get("DATABASE_URL")) or os.environ.get("PRICERADAR_ENV") == "production"


def set_auth_cookie(response: Response, token: str) -> None:
    """Attach the JWT to the response as an HttpOnly cookie.

    Production: SameSite=None + Secure (required for the static
    frontend on priceradar.space to authenticate against the API on
    onrender.com). Local dev: SameSite=Lax, Secure=False so http://
    localhost still works without HTTPS.
    """
    prod = _is_production()
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=prod,
        samesite="none" if prod else "lax",
        path="/",
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear the auth cookie on logout. Attributes must match set_auth_cookie
    or some browsers refuse to overwrite it."""
    prod = _is_production()
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE,
        path="/",
        secure=prod,
        samesite="none" if prod else "lax",
        httponly=True,
    )


def _extract_token(request: Request) -> Optional[str]:
    """Prefer cookie, fall back to Authorization header.

    The header path keeps backward compatibility during the cookie
    migration rollout and lets the Swagger docs "Authorize" button
    still work with a pasted bearer token.
    """
    cookie_token = request.cookies.get(ACCESS_TOKEN_COOKIE)
    if cookie_token:
        return cookie_token
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip() or None
    return None


def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token = _extract_token(request)
    if not token:
        raise credentials_exception

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
