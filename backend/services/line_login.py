"""LINE Login v2.1 OAuth フロー。

ID Token を LINE の OAuth2 verify エンドポイントで検証してから
user_id / display_name を取り出す。verify エンドポイントは署名・
aud (client_id)・有効期限を LINE 側で確認してくれるため、独自で
JWKs を持つ必要がない。
"""
import os
import json
import base64
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger("priceradar.line_login")

LINE_TOKEN_ENDPOINT = "https://api.line.me/oauth2/v2.1/token"
LINE_VERIFY_ENDPOINT = "https://api.line.me/oauth2/v2.1/verify"


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    """JWT (header.payload.signature) のpayload部をデコード。署名検証は行わない。

    LINE 側エンドポイントが利用できず、フォールバックとしてクレームだけ
    使いたい場合にのみ呼ぶ。通常は `_verify_id_token` を使うこと。
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT format")
    payload_b64 = parts[1]
    # base64url パディング修正
    padding = 4 - (len(payload_b64) % 4)
    if padding != 4:
        payload_b64 += "=" * padding
    decoded = base64.urlsafe_b64decode(payload_b64.encode())
    return json.loads(decoded)


async def _verify_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """LINE の verify エンドポイントで id_token を検証する。

    LINE 側で署名 / aud (channel_id) / exp を確認し、検証済みクレームを返す。
    失敗時は None。
    """
    client_id = os.environ.get("LINE_LOGIN_CHANNEL_ID")
    if not client_id:
        logger.error("LINE_LOGIN_CHANNEL_ID is not configured")
        return None

    data = {"id_token": id_token, "client_id": client_id}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                LINE_VERIFY_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
    except Exception as e:
        logger.error(f"LINE id_token verify exception: {e}")
        return None

    if resp.status_code != 200:
        logger.warning(
            f"LINE id_token verification failed: {resp.status_code} {resp.text[:200]}"
        )
        return None
    return resp.json()


async def exchange_code(code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    """LINE Login の認可コードを access_token と id_token に交換。"""
    client_id = os.environ.get("LINE_LOGIN_CHANNEL_ID")
    client_secret = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")

    if not client_id or not client_secret:
        logger.error("LINE_LOGIN_CHANNEL_ID/SECRET is not configured")
        return None

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                LINE_TOKEN_ENDPOINT,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            logger.warning(f"LINE token exchange failed: {resp.status_code} {resp.text[:200]}")
            return None
        return resp.json()
    except Exception as e:
        logger.error(f"LINE token exchange exception: {e}")
        return None


async def get_user_profile_from_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """id_token を LINE で検証してから user_id, display_name を抽出。"""
    payload = await _verify_id_token(id_token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if not user_id:
        logger.error("id_token has no 'sub' claim after verification")
        return None

    # aud は verify エンドポイントで検証済みだが、念のため再確認
    client_id = os.environ.get("LINE_LOGIN_CHANNEL_ID")
    aud = payload.get("aud")
    if client_id and aud and aud != client_id:
        logger.error(f"id_token aud mismatch: got={aud} expected={client_id}")
        return None

    return {
        "user_id": user_id,
        "display_name": payload.get("name", ""),
        "picture": payload.get("picture"),
        "email": payload.get("email"),  # email scope 申請時のみ
    }
