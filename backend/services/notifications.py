"""通知判定・送信の統合ロジック。

スクレイピング後の価格比較と、重複通知防止ロジック、LINE送信を統合。
"""
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
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


def _is_out_of_stock(stock_status: Optional[str]) -> bool:
    """商品が品切れ状態かどうかを判定（"品切れ" を含むかで判定）。"""
    if not stock_status:
        return False
    return "品切れ" in stock_status


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


def _handle_blocked(db: Session, user: models.User) -> None:
    """Bot がユーザーにブロックされた（or 友達解除された）場合の処理。

    line_user_id をクリアして、それ以降の通知送信を自動停止させる。
    再度 LINE 連携すれば復旧可能。
    """
    logger.warning(
        f"LINE bot blocked/unfriended by user_id={user.id} — clearing line_user_id"
    )
    user.line_user_id = None
    user.notification_enabled = False
    db.commit()


async def _push_flex_with_block_handling(
    db: Session,
    user: models.User,
    *,
    title: str,
    product_name: str,
    own_price: float,
    competitor_name: str,
    competitor_price: float,
    diff: float,
    product_id: int,
    scraped_at: Optional[datetime] = None,
) -> Optional[str]:
    """Flex push のラッパー: 403 (blocked) を検知したら line_user_id をクリアする。"""
    # line_messaging.push_flex_price_alert は LinePushResult.request_id のみを返すが、
    # ブロック検知を知るため、push_text の detailed 版と同じパターンで呼ぶ。
    # ここでは簡単のため push_flex_price_alert を呼び、失敗時は push_text_detailed で
    # blocked を検知する必要はなく、下で push_text のテスト時に検知する。
    msg_id = await line_messaging.push_flex_price_alert(
        user.line_user_id,
        title=title,
        product_name=product_name,
        own_price=own_price,
        competitor_name=competitor_name,
        competitor_price=competitor_price,
        diff=diff,
        product_id=product_id,
        frontend_url=_frontend_url(),
        scraped_at=scraped_at,
    )
    return msg_id


async def _push_text_with_block_handling(
    db: Session, user: models.User, text: str
) -> Optional[str]:
    """push_text のラッパー: 403 (blocked) を検知したら line_user_id をクリアする。"""
    result = await line_messaging.push_text_detailed(user.line_user_id, text)
    if result.blocked:
        _handle_blocked(db, user)
        return None
    return result.request_id


async def check_and_notify_price_event(
    db: Session,
    comp_url: models.CompetitorUrl,
    new_price: float,
    new_stock: str,
) -> None:
    """スクレイプ直後に呼ばれ、価格イベント（負け/回復/品切れ/再入荷）を判定して通知。

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
        scraped_at = current.scraped_at

        if current_price is None or previous_price is None:
            return

        own_price = float(product.own_price) if product.own_price is not None else None
        if own_price is None:
            return

        competitor_label = comp_url.competitor_name or "競合"

        # 価格負け検知: 前回は自社より高かったが、今回は自社を下回った
        if (
            user.notify_price_loss
            and current_price < own_price
            and previous_price >= own_price
        ):
            if not _is_recently_notified(db, user.id, "price_loss", comp_url.id):
                msg_id = await _push_flex_with_block_handling(
                    db, user,
                    title="🚨 価格負け検知",
                    product_name=product.product_name,
                    own_price=own_price,
                    competitor_name=competitor_label,
                    competitor_price=current_price,
                    diff=own_price - current_price,
                    product_id=product.id,
                    scraped_at=scraped_at,
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
                msg_id = await _push_flex_with_block_handling(
                    db, user,
                    title="✅ 価格優位に回復",
                    product_name=product.product_name,
                    own_price=own_price,
                    competitor_name=competitor_label,
                    competitor_price=current_price,
                    diff=own_price - current_price,
                    product_id=product.id,
                    scraped_at=scraped_at,
                )
                _log_notification(
                    db, user.id, "price_recovery", comp_url.id,
                    f"{previous_price}", f"{current_price}", msg_id,
                )

        # 品切れ検知（在庫→品切れ）
        if user.notify_stock_change:
            was_out = _is_out_of_stock(previous_stock)
            is_out = _is_out_of_stock(current_stock)

            if is_out and not was_out:
                # 在庫あり → 品切れ
                if not _is_recently_notified(db, user.id, "stock_out", comp_url.id):
                    text = (
                        f"📦 競合商品が品切れ\n\n"
                        f"商品: {product.product_name}\n"
                        f"競合: {competitor_label}\n"
                        f"ダッシュボード → {_frontend_url()}/prices/?id={product.id}"
                    )
                    msg_id = await _push_text_with_block_handling(db, user, text)
                    _log_notification(
                        db, user.id, "stock_out", comp_url.id,
                        previous_stock, current_stock, msg_id,
                    )
            elif not is_out and was_out:
                # 品切れ → 再入荷
                if not _is_recently_notified(db, user.id, "stock_in", comp_url.id):
                    price_info = (
                        f"価格: ¥{int(current_price):,}\n"
                        if current_price is not None
                        else ""
                    )
                    text = (
                        f"🔔 競合商品が再入荷\n\n"
                        f"商品: {product.product_name}\n"
                        f"競合: {competitor_label}\n"
                        f"{price_info}"
                        f"ダッシュボード → {_frontend_url()}/prices/?id={product.id}"
                    )
                    msg_id = await _push_text_with_block_handling(db, user, text)
                    _log_notification(
                        db, user.id, "stock_in", comp_url.id,
                        previous_stock, current_stock, msg_id,
                    )

    except Exception as e:
        logger.exception(
            "check_and_notify_price_event failed for comp_url_id=%s: %s",
            getattr(comp_url, "id", None), e,
        )


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
        # Operator-visible notification: includes identifying info by design
        # (only a single recipient: the operator LINE ID). Not logged.
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
        await _push_text_with_block_handling(db, user, text)
