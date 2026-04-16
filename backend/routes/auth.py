from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from database import get_db
import models, schemas, auth
import httpx
import os
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

@router.post("/auth/register", response_model=schemas.Token)
@limiter.limit("3/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    ユーザー新規登録 API
    
    - **username**: 一意のユーザー名
    - **password**: パスワード
    - **email**: (オプション) メールアドレス
    """
    # Check username uniqueness
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check email uniqueness (if provided)
    if user.email:
        db_email = db.query(models.User).filter(models.User.email == user.email).first()
        if db_email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        plan="free",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": new_user.username, "user_id": new_user.id},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/auth/login", response_model=schemas.Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    ログイン API (OAuth2 パスワードフロー)
    
    - **username**: ユーザー名
    - **password**: パスワード
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.post("/auth/google", response_model=schemas.Token)
@limiter.limit("10/minute")
async def google_auth(request: Request, body: schemas.GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth2 authentication: exchange code for token, get user info, create/link user."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    # Exchange authorization code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": body.code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": body.redirect_uri,
                "grant_type": "authorization_code",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to exchange Google authorization code")

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="No access token received from Google")

    # Get user info from Google
    async with httpx.AsyncClient() as client:
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if userinfo_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get Google user info")

    google_user = userinfo_response.json()
    google_email = google_user.get("email")
    google_name = google_user.get("name", "")

    if not google_email:
        raise HTTPException(status_code=400, detail="Google account has no email")

    # Find existing user by email or create new one
    user = db.query(models.User).filter(models.User.email == google_email).first()

    if not user:
        # Generate a unique username from Google name
        base_username = google_name.replace(" ", "_").lower()[:20] or google_email.split("@")[0]
        username = base_username
        counter = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        # Create user with a random password hash (Google users don't use password login)
        random_password = secrets.token_urlsafe(32)
        user = models.User(
            username=username,
            email=google_email,
            hashed_password=auth.get_password_hash(random_password),
            plan="free",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Issue JWT token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


async def _resolve_line_profile(code: str, redirect_uri: str):
    """LINE 認可コードを交換し id_token から (line_user_id, display_name) を返す。失敗時 HTTPException。"""
    from services.line_login import exchange_code, get_user_profile_from_id_token

    tokens = await exchange_code(code, redirect_uri)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange LINE authorization code")

    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(status_code=400, detail="LINE response missing id_token (is openid scope set?)")

    profile = await get_user_profile_from_id_token(id_token)
    if not profile:
        raise HTTPException(status_code=400, detail="Failed to decode LINE id_token")

    return profile["user_id"], profile.get("display_name") or ""


@router.post("/auth/line", response_model=schemas.Token)
@limiter.limit("10/minute")
async def line_auth(request: Request, body: schemas.LineAuthRequest, db: Session = Depends(get_db)):
    """LINE Login: 認可コードで既存ユーザー検索 or 新規作成して JWT を返す。

    既存ユーザーへの連携は `POST /auth/line/link` を使用（JWT 必須）。
    """
    line_user_id, display_name = await _resolve_line_profile(body.code, body.redirect_uri)

    user = db.query(models.User).filter(models.User.line_user_id == line_user_id).first()
    if not user:
        base_username = "line_" + line_user_id[-8:].lower()
        username = base_username
        counter = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        random_password = secrets.token_urlsafe(32)
        user = models.User(
            username=username,
            email=None,
            hashed_password=auth.get_password_hash(random_password),
            plan="free",
            line_user_id=line_user_id,
            line_display_name=display_name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = auth.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires,
    )
    return {"access_token": jwt_token, "token_type": "bearer"}


@router.post("/auth/line/link", response_model=schemas.LineLinkStatus)
@limiter.limit("10/minute")
async def line_link(
    request: Request,
    body: schemas.LineAuthRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """認証済みユーザーに LINE アカウントを連携する（JWT 必須、current_user の ID を使用）。

    別ユーザーが同じ LINE ID を既に使用している場合はエラー。
    """
    from services import line_messaging

    line_user_id, display_name = await _resolve_line_profile(body.code, body.redirect_uri)

    existing = db.query(models.User).filter(
        models.User.line_user_id == line_user_id,
        models.User.id != current_user.id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="このLINEアカウントは既に他のユーザーと連携されています",
        )

    current_user.line_user_id = line_user_id
    current_user.line_display_name = display_name
    db.commit()
    db.refresh(current_user)

    return schemas.LineLinkStatus(
        linked=True,
        line_user_id=current_user.line_user_id,
        line_display_name=current_user.line_display_name,
        bot_basic_id=line_messaging.get_bot_basic_id(),
    )
