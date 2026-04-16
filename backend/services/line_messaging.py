"""LINE Messaging API client.

公式SDKを使わず httpx ベースで実装（既存依存と整合）。
"""
import os
import logging
from typing import Optional
import httpx

logger = logging.getLogger("priceradar.line")

LINE_PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"


def _get_access_token() -> Optional[str]:
    return os.environ.get("LINE_MESSAGING_CHANNEL_ACCESS_TOKEN")


def get_bot_basic_id() -> Optional[str]:
    """フロントエンドの友達追加リンク用 (@で始まる Basic ID)。"""
    return os.environ.get("LINE_BOT_BASIC_ID")


def get_friend_add_url() -> Optional[str]:
    """LINE Bot を友達追加するためのURL。Basic ID が必要。"""
    basic_id = get_bot_basic_id()
    if not basic_id:
        return None
    # @ を取り除く
    clean_id = basic_id.lstrip("@")
    return f"https://line.me/R/ti/p/@{clean_id}"


async def push_text(line_user_id: str, text: str) -> Optional[str]:
    """指定のLINEユーザーIDにテキストメッセージを送信。

    成功時は LINE API レスポンスの x-line-request-id を返す。
    失敗時は None を返してログを残す。
    """
    token = _get_access_token()
    if not token:
        logger.error("LINE_MESSAGING_CHANNEL_ACCESS_TOKEN is not configured")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": line_user_id,
        "messages": [{"type": "text", "text": text}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(LINE_PUSH_ENDPOINT, json=payload, headers=headers)
        if resp.status_code == 200:
            request_id = resp.headers.get("x-line-request-id")
            logger.info(f"LINE push sent to {line_user_id[:8]}... (req_id={request_id})")
            return request_id or "ok"
        else:
            logger.warning(
                f"LINE push failed: status={resp.status_code} body={resp.text[:200]} "
                f"to={line_user_id[:8]}..."
            )
            return None
    except Exception as e:
        logger.error(f"LINE push exception: {e}")
        return None


async def push_flex_price_alert(
    line_user_id: str,
    *,
    title: str,
    product_name: str,
    own_price: float,
    competitor_name: str,
    competitor_price: float,
    diff: float,
    product_id: int,
    frontend_url: str = "https://priceradar.space",
) -> Optional[str]:
    """価格関連の Flex Message を送信。"""
    token = _get_access_token()
    if not token:
        logger.error("LINE_MESSAGING_CHANNEL_ACCESS_TOKEN is not configured")
        return None

    sign = "+" if diff >= 0 else ""
    diff_text = f"{sign}¥{int(abs(diff)):,}" if diff != 0 else "¥0"
    diff_color = "#E5484D" if diff > 0 else "#30A46C"

    flex = {
        "type": "bubble",
        "size": "kilo",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": title, "weight": "bold", "color": "#FFFFFF", "size": "md"},
            ],
            "backgroundColor": "#10B981",
            "paddingAll": "12px",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {"type": "text", "text": product_name, "weight": "bold", "size": "lg", "wrap": True},
                {"type": "separator", "margin": "md"},
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {"type": "text", "text": "自社価格", "size": "sm", "color": "#888888"},
                        {"type": "text", "text": f"¥{int(own_price):,}", "size": "sm", "align": "end"},
                    ],
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": competitor_name, "size": "sm", "color": "#888888"},
                        {"type": "text", "text": f"¥{int(competitor_price):,}", "size": "sm", "align": "end"},
                    ],
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": "差額", "size": "sm", "color": "#888888"},
                        {"type": "text", "text": diff_text, "size": "sm", "align": "end", "color": diff_color, "weight": "bold"},
                    ],
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#10B981",
                    "action": {
                        "type": "uri",
                        "label": "ダッシュボードを開く",
                        "uri": f"{frontend_url}/prices/?id={product_id}",
                    },
                }
            ],
        },
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "to": line_user_id,
        "messages": [{"type": "flex", "altText": title, "contents": flex}],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(LINE_PUSH_ENDPOINT, json=payload, headers=headers)
        if resp.status_code == 200:
            request_id = resp.headers.get("x-line-request-id")
            logger.info(f"LINE flex sent to {line_user_id[:8]}... (req_id={request_id})")
            return request_id or "ok"
        else:
            logger.warning(
                f"LINE flex failed: status={resp.status_code} body={resp.text[:200]}"
            )
            return None
    except Exception as e:
        logger.error(f"LINE flex exception: {e}")
        return None
