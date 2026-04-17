"""LINE Messaging API client.

公式SDKを使わず httpx ベースで実装（既存依存と整合）。
"""
import asyncio
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import quote
import httpx

logger = logging.getLogger("priceradar.line")

LINE_PUSH_ENDPOINT = "https://api.line.me/v2/bot/message/push"

# ユーザーが bot をブロック or 友達解除した場合、LINE API は 403 を返す
LINE_STATUS_USER_BLOCKED = 403
LINE_STATUS_RATE_LIMIT = 429

# Display timezone for notifications. Defaults to JST (UTC+9) since the
# app is Japan-first; override with DISPLAY_TZ_OFFSET_HOURS to adjust.
_DEFAULT_TZ_OFFSET_HOURS = 9
try:
    _tz_offset_hours = int(os.environ.get("DISPLAY_TZ_OFFSET_HOURS", _DEFAULT_TZ_OFFSET_HOURS))
except (TypeError, ValueError):
    _tz_offset_hours = _DEFAULT_TZ_OFFSET_HOURS
DISPLAY_TZ = timezone(timedelta(hours=_tz_offset_hours))
_DISPLAY_TZ_LABEL = "JST" if _tz_offset_hours == 9 else f"UTC{'+' if _tz_offset_hours >= 0 else ''}{_tz_offset_hours}"
# Keep the legacy name for anything that imports it.
JST = DISPLAY_TZ


class LinePushResult:
    """LINE push の結果を返すコンテナ。

    - request_id: 成功時の LINE-request-id（None なら失敗）
    - status_code: HTTP ステータス (取得できた場合)
    - blocked: True なら bot がユーザーにブロックされている（403）
    - rate_limited: True なら LINE 側のレート制限 (429)
    """
    __slots__ = ("request_id", "status_code", "blocked", "rate_limited")

    def __init__(self, request_id: Optional[str] = None, status_code: Optional[int] = None,
                 blocked: bool = False, rate_limited: bool = False):
        self.request_id = request_id
        self.status_code = status_code
        self.blocked = blocked
        self.rate_limited = rate_limited

    @property
    def ok(self) -> bool:
        return self.request_id is not None


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


async def _post_line(payload: dict, *, label: str) -> LinePushResult:
    """LINE /v2/bot/message/push への POST 共通処理。

    - 429 (rate limit) は exponential backoff で 1 回だけリトライ
    - 403 は bot ブロック/フレンド解除として blocked=True を返す
    - 成功時は LinePushResult(request_id=...)
    """
    token = _get_access_token()
    if not token:
        logger.error("LINE_MESSAGING_CHANNEL_ACCESS_TOKEN is not configured")
        return LinePushResult()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    target_preview = payload.get("to", "?")[:8]

    attempts = [0, 1.0]  # 初回 + 1秒後リトライ (429 のみ)
    last_status: Optional[int] = None
    last_body = ""
    for i, delay in enumerate(attempts):
        if delay:
            await asyncio.sleep(delay)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(LINE_PUSH_ENDPOINT, json=payload, headers=headers)
        except Exception as e:
            logger.error(f"LINE {label} exception: {e}")
            return LinePushResult()

        last_status = resp.status_code
        last_body = resp.text[:200]

        if resp.status_code == 200:
            request_id = resp.headers.get("x-line-request-id")
            logger.info(f"LINE {label} sent to {target_preview}... (req_id={request_id}, attempt={i+1})")
            return LinePushResult(request_id=request_id or "ok", status_code=200)

        if resp.status_code == LINE_STATUS_USER_BLOCKED:
            logger.warning(
                f"LINE {label} blocked by user: to={target_preview}... body={last_body}"
            )
            return LinePushResult(status_code=403, blocked=True)

        if resp.status_code == LINE_STATUS_RATE_LIMIT and i < len(attempts) - 1:
            logger.warning(f"LINE {label} rate limited (429) — retrying once")
            continue  # retry with delay

        # Other error — stop retrying
        break

    logger.warning(
        f"LINE {label} failed: status={last_status} body={last_body} to={target_preview}..."
    )
    return LinePushResult(
        status_code=last_status,
        rate_limited=(last_status == LINE_STATUS_RATE_LIMIT),
    )


async def push_text(line_user_id: str, text: str) -> Optional[str]:
    """指定のLINEユーザーIDにテキストメッセージを送信。

    成功時は LINE API レスポンスの x-line-request-id を返す。失敗時は None。
    詳細な結果が欲しい場合は `push_text_detailed` を使用。
    """
    result = await push_text_detailed(line_user_id, text)
    return result.request_id


async def push_text_detailed(line_user_id: str, text: str) -> LinePushResult:
    """push_text のラッパー。429/403 の詳細を含む LinePushResult を返す。"""
    payload = {
        "to": line_user_id,
        "messages": [{"type": "text", "text": text}],
    }
    return await _post_line(payload, label="push")


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
    scraped_at: Optional[datetime] = None,
) -> Optional[str]:
    """価格関連の Flex Message を送信。"""
    sign = "+" if diff >= 0 else ""
    diff_text = f"{sign}¥{int(abs(diff)):,}" if diff != 0 else "¥0"
    diff_color = "#E5484D" if diff > 0 else "#30A46C"

    # 価格を確認した時刻 (JST)。渡されない場合は "現在" を表示
    if scraped_at is not None:
        if scraped_at.tzinfo is None:
            scraped_at = scraped_at.replace(tzinfo=timezone.utc)
        timestamp_text = scraped_at.astimezone(DISPLAY_TZ).strftime(f"%m/%d %H:%M {_DISPLAY_TZ_LABEL}")
    else:
        timestamp_text = datetime.now(DISPLAY_TZ).strftime(f"%m/%d %H:%M {_DISPLAY_TZ_LABEL}")

    # product_id は int の前提だが、URL 組み立て時は念のためエンコード
    safe_product_id = quote(str(int(product_id)), safe="")

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
                {"type": "separator", "margin": "md"},
                {
                    "type": "text",
                    "text": f"最終確認: {timestamp_text}",
                    "size": "xs",
                    "color": "#888888",
                    "align": "end",
                    "margin": "sm",
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
                        "uri": f"{frontend_url}/prices/?id={safe_product_id}",
                    },
                }
            ],
        },
    }

    payload = {
        "to": line_user_id,
        "messages": [{"type": "flex", "altText": title, "contents": flex}],
    }
    result = await _post_line(payload, label="flex")
    return result.request_id
