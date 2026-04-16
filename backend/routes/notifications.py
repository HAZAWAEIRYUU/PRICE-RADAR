"""通知設定 API + LINE 連携状態 + テスト送信。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from services import line_messaging

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
    """LINE 連携状態と友達追加用 Bot ID を返す。"""
    return schemas.LineLinkStatus(
        linked=bool(current_user.line_user_id),
        line_user_id=current_user.line_user_id,
        line_display_name=current_user.line_display_name,
        bot_basic_id=line_messaging.get_bot_basic_id(),
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
async def send_test_notification(
    current_user: models.User = Depends(auth.get_current_user),
):
    """ログイン中ユーザーの LINE にテスト通知を送信。

    Bot を友達追加していない場合は LINE API がエラーを返す → このエンドポイントで疎通確認できる。
    """
    if not current_user.line_user_id:
        raise HTTPException(status_code=400, detail="LINE未連携です")

    text = (
        "✅ Price-Radar 通知テスト\n\n"
        "通知が正常に届いています。\n"
        "今後、価格変動などのイベントをこちらに通知します。"
    )
    msg_id = await line_messaging.push_text(current_user.line_user_id, text)
    if msg_id is None:
        raise HTTPException(
            status_code=400,
            detail="通知の送信に失敗しました。LINE Bot を友達追加しているかご確認ください。",
        )
    return {"detail": "テスト通知を送信しました", "message_id": msg_id}
