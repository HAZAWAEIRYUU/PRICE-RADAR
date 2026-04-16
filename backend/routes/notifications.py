"""通知設定 API + LINE 連携状態 + テスト送信。"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from database import get_db
import models, schemas, auth
from services import line_messaging

limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.get("/notifications/settings", response_model=schemas.NotificationSettings)
def get_settings(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """ログイン中のユーザーの通知設定を取得。"""
    return current_user


@router.put("/notifications/settings", response_model=schemas.NotificationSettings)
def update_settings(
    update: schemas.NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """通知設定を部分更新。"""
    data = update.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/notifications/line-status", response_model=schemas.LineLinkStatus)
def get_line_status(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """LINE 連携状態と友達追加用 Bot ID を返す。

    bot_basic_id は LINE_BOT_BASIC_ID 環境変数が未設定だと None を返す
    (フロント側で「友達追加リンク」を隠す/エラー表示する)。
    """
    import logging
    bot_basic_id = line_messaging.get_bot_basic_id()
    if not bot_basic_id:
        logging.getLogger("priceradar.notifications").warning(
            "LINE_BOT_BASIC_ID is not configured — friend-add link will be unavailable"
        )
    return schemas.LineLinkStatus(
        linked=bool(current_user.line_user_id),
        line_user_id=current_user.line_user_id,
        line_display_name=current_user.line_display_name,
        bot_basic_id=bot_basic_id,
    )


@router.delete("/notifications/line-link")
def unlink_line(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """LINE 連携を解除。"""
    current_user.line_user_id = None
    current_user.line_display_name = None
    current_user.notification_enabled = False
    db.commit()
    return {"detail": "LINE連携を解除しました"}


@router.post("/notifications/test")
@limiter.limit("5/minute")
async def send_test_notification(
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """ログイン中ユーザーの LINE にテスト通知を送信。

    Bot を友達追加していない/ブロックされている場合は LINE API が 403 を返す。
    403 の場合は自動で line_user_id をクリアし「再連携が必要」エラーを返す。
    """
    if not current_user.line_user_id:
        raise HTTPException(status_code=400, detail="LINE未連携です")

    text = (
        "✅ Price-Radar 通知テスト\n\n"
        "通知が正常に届いています。\n"
        "今後、価格変動などのイベントをこちらに通知します。"
    )
    result = await line_messaging.push_text_detailed(current_user.line_user_id, text)

    if result.blocked:
        # ユーザーが Bot をブロック/友達解除している → 自動で連携解除
        current_user.line_user_id = None
        current_user.notification_enabled = False
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=(
                "LINE Bot が友達追加されていない、またはブロックされています。"
                "Bot を友達追加してから、再度 LINE 連携をお試しください。"
            ),
        )

    if result.rate_limited:
        raise HTTPException(
            status_code=429,
            detail="LINE API のレート制限に達しました。少し時間をおいて再度お試しください。",
        )

    if not result.ok:
        raise HTTPException(
            status_code=400,
            detail="通知の送信に失敗しました。しばらくしてから再度お試しください。",
        )

    return {"detail": "テスト通知を送信しました", "message_id": result.request_id}
