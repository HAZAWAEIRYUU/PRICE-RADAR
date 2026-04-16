"""通知判定・送信の統合ロジック。

スクレイピング後の価格比較と、重複通知防止ロジック、LINE送信を統合。
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session
import models
from services import line_messaging

logger = logging.getLogger("priceradar.notifications")

# 同一イベントは24時間以内は再送しない
DEDUP_WINDOW = timedelta(hours=24)

# 運用者 (FuN.LLC) に Stripe イベントを通知する場合の LINE user_id
OPERATOR_LINE_USER_ID_ENV = "OPERATOR_LINE_USER_ID"


def _frontend_url() -> str:
    return os.environ.get("FRONTEND_URL", "https://priceradar.space")


def _is_recently_notified(
    db: Session, user_id: int, event_type: str, entity_id: Optional[int]
) -> bool:
    """同一 (user_id, event_type, entity_id) で24時間以内の記録があるかを確認。"""
    cutoff = datetime.now(timezone.utc) - DEDUP_WINDOW
    query = db.query(models.NotificationLog).filter(
        models.NotificationLog.user_id == user_id,
        models.NotificationLog.event_type == event_type,
        models.NotificationLog.sent_at >= cutoff,
    )
    if entity_id is not None:
        query = query.filter(models.NotificationLog.entity_id == entity_id)
    return query.first() is not None


def _log_notification(
    db: Session,
    user_id: int,
    event_type: str,
    entity_id: Optional[int],
    previous_state: Optional[str],
    current_state: Optional[str],
    line_message_id: Optional[str],
) -> None:
    log = models.NotificationLog(
        user_id=user_id,
        event_type=event_type,
        entity_id=entity_id,
        previous_state=previous_state,
        current_state=current_state,
        line_message_id=line_message_id,
    )
    db.add(log)
    db.commit()


async def check_and_notify_price_event(
    db: Session,
    comp_url: models.CompetitorUrl,
    new_price: float,
    new_stock: str,
) -> None:
    """スクレイプ直後に呼ばれ、価格イベント（負け/回復/品切れ）を判定して通知。

    呼び出し側は新しい PriceHistory を保存した後にこれを呼ぶこと。
    """
    try:
        product = comp_url.product
        if product is None or not product.is_active:
            return
        user = product.owner
        if user is None or not user.line_user_id or not user.notification_enabled:
            return

        # 最新2件の PriceHistory を取得（今回保存した分が含まれる前提）
        histories = (
            db.query(models.PriceHistory)
            .filter(models.PriceHistory.competitor_url_id == comp_url.id)
            .order_by(models.PriceHistory.scraped_at.desc())
            .limit(2)
            .all()
        )
        if len(histories) < 2:
            # 比較対象なし、初回はスキップ
            return

        current, previous = histories[0], histories[1]
        current_price = float(current.price) if current.price is not None else None
        previous_price = float(previous.price) if previous.price is not None else None
        current_stock = current.stock_status or ""
        previous_stock = previous.stock_status or ""

        if current_price is None or previous_price is None:
            return

        own_price = float(product.own_price) if product.own_price is not None else None
        if own_price is None:
            return

        # 価格負け検知: 前回は自社より高かったが、今回は自社を下回った
        if (
            user.notify_price_loss
            and current_price < own_price
            and previous_price >= own_price
        ):
            if not _is_recently_notified(db, user.id, "price_loss", comp_url.id):
                msg_id = await line_messaging.push_flex_price_alert(
                    user.line_user_id,
                    title="🚨 価格負け検知",
                    product_name=product.product_name,
                    own_price=own_price,
                    competitor_name=comp_url.competitor_name or "競合",
                    competitor_price=current_price,
                    diff=own_price - current_price,
                    product_id=product.id,
                    frontend_url=_frontend_url(),
                )
                _log_notification(
                    db, user.id, "price_loss", comp_url.id,
                    f"{previous_price}", f"{current_price}", msg_id,
                )

        # 価格優位回復: 前回は自社を下回っていたが、今回は自社以上に戻った
        elif (
            user.notify_price_recovery
            and current_price >= own_price
            and previous_price < own_price
        ):
            if not _is_recently_notified(db, user.id, "price_recovery", comp_url.id):
                msg_id = await line_messaging.push_flex_price_alert(
                    user.line_user_id,
                    title="✅ 価格優位に回復",
                    product_name=product.product_name,
                    own_price=own_price,
                    competitor_name=comp_url.competitor_name or "競合",
                    competitor_price=current_price,
                    diff=own_price - current_price,
                    product_id=product.id,
                    frontend_url=_frontend_url(),
                )
                _log_notification(
                    db, user.id, "price_recovery", comp_url.id,
                    f"{previous_price}", f"{current_price}", msg_id,
                )

        # 品切れ検知
        if (
            user.notify_stock_change
            and "品切れ" in current_stock
            and "品切れ" not in previous_stock
        ):
            if not _is_recently_notified(db, user.id, "stock_out", comp_url.id):
                text = (
                    f"📦 競合商品が品切れ\n\n"
                    f"商品: {product.product_name}\n"
                    f"競合: {comp_url.competitor_name}\n"
                    f"ダッシュボード → {_frontend_url()}/prices/?id={product.id}"
                )
                msg_id = await line_messaging.push_text(user.line_user_id, text)
                _log_notification(
                    db, user.id, "stock_out", comp_url.id,
                    previous_stock, current_stock, msg_id,
                )

    except Exception as e:
        logger.error(f"check_and_notify_price_event failed: {e}")


async def notify_subscription_event(
    db: Session, user: models.User, event: str, plan: str
) -> None:
    """Stripe Webhook から呼ばれるサブスクリプション通知。

    event: "subscribed" / "cancelled" / "payment_failed" など
    """
    # 1. 運用者 (FuN.LLC) に全件通知
    operator_user_id = os.environ.get(OPERATOR_LINE_USER_ID_ENV)
    if operator_user_id:
        emoji = {"subscribed": "🎉", "cancelled": "😢", "payment_failed": "⚠️"}.get(event, "ℹ️")
        text = (
            f"{emoji} Price-Radar {event}\n\n"
            f"User: {user.username} (id={user.id})\n"
            f"Plan: {plan}\n"
            f"Email: {user.email or '(none)'}"
        )
        await line_messaging.push_text(operator_user_id, text)

    # 2. 本人が通知設定を有効にしている場合のみ通知
    if user.line_user_id and user.notification_enabled and user.notify_subscription:
        if event == "subscribed":
            text = (
                f"🎉 Pro プランへのアップグレードが完了しました\n\n"
                f"ご利用ありがとうございます。\n"
                f"ダッシュボード → {_frontend_url()}/dashboard/"
            )
        elif event == "cancelled":
            text = "💳 Pro プランが解約されました。Free プランに変更されています。"
        else:
            text = f"Stripe イベント: {event}"
        await line_messaging.push_text(user.line_user_id, text)
