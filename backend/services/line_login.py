"""LINE Login v2.1 OAuth フロー。

ID Token をデコードして user_id, display_name を取り出す。
署名検証は本番では実装すべきだが、当面は LINE token endpoint 経由で取得した
id_token を信頼する（中間者攻撃のリスクは TLS で軽減）。
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
    """JWT (header.payload.signature) のpayload部をデコード。署名検証は行わない。"""
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
    """id_token をデコードして user_id, display_name を抽出。"""
    try:
        payload = _decode_jwt_payload(id_token)
    except Exception as e:
        logger.error(f"Failed to decode id_token: {e}")
        return None

    user_id = payload.get("sub")
    if not user_id:
        logger.error("id_token has no 'sub' claim")
        return None

    return {
        "user_id": user_id,
        "display_name": payload.get("name", ""),
        "picture": payload.get("picture"),
        "email": payload.get("email"),  # email scope 申請時のみ
    }
