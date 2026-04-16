import os
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from sqlalchemy.orm import Session
import stripe
from database import get_db
import models
import auth

logger = logging.getLogger("priceradar.stripe")

router = APIRouter()

def get_stripe_config():
    api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    price_id = os.environ.get("STRIPE_PRICE_ID", "")
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    frontend_url = os.environ.get("FRONTEND_URL", "https://priceradar.space")
    stripe.api_key = api_key
    return api_key, price_id, webhook_secret, frontend_url

@router.post("/create-checkout-session")
def create_checkout_session(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    api_key, price_id, _, frontend_url = get_stripe_config()
    if not api_key or not price_id:
        raise HTTPException(status_code=500, detail="Stripe configuration is missing")
        
    try:
        customer_id = current_user.stripe_customer_id
        
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            "mode": "subscription",
            "success_url": f"{frontend_url}/pricing/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{frontend_url}/pricing/cancel",
            "client_reference_id": str(current_user.id),
        }
        
        if customer_id:
            session_params["customer"] = customer_id
        else:
            session_params["customer_email"] = current_user.email

        checkout_session = stripe.checkout.Session.create(**session_params)
        return {"url": checkout_session.url}
    
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail="決済セッションの作成に失敗しました")
    except Exception as e:
        raise HTTPException(status_code=500, detail="内部エラーが発生しました")

@router.post("/create-portal-session")
def create_portal_session(current_user: models.User = Depends(auth.get_current_user)):
    api_key, _, _, frontend_url = get_stripe_config()
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe configuration is missing")
        
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        portalSession = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{frontend_url}/pricing",
        )
        return {"url": portalSession.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail="カスタマーポータルの作成に失敗しました")
    except Exception as e:
        raise HTTPException(status_code=500, detail="内部エラーが発生しました")

@router.get("/verify-session")
def verify_session(
    session_id: str = Query(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    api_key, _, _, _ = get_stripe_config()
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe configuration is missing")

    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise HTTPException(status_code=400, detail="Invalid session")

    if checkout_session.client_reference_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Session does not belong to this user")

    if checkout_session.payment_status != "paid":
        raise HTTPException(status_code=400, detail="Payment not completed")

    # Refresh user from DB to get latest plan
    db.refresh(current_user)
    return {"status": "verified", "plan": current_user.plan}

async def _notify_subscription(db, user, event: str, plan: str):
    """LINE 通知の安全ラッパー（失敗してもwebhookを止めない）。"""
    try:
        from services.notifications import notify_subscription_event
        await notify_subscription_event(db, user, event, plan)
    except Exception as e:
        logger.error(f"Failed to send subscription notification: {e}")


@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(..., alias="stripe-signature"), db: Session = Depends(get_db)):
    _, _, webhook_secret, _ = get_stripe_config()
    if not webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

    # Handle the event
    logger.info(f"Stripe webhook received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Save customer ID and subscription ID
        user_id = session.get("client_reference_id")
        if user_id:
            user = db.query(models.User).filter(models.User.id == int(user_id)).first()
            if user:
                user.stripe_customer_id = session.get("customer")
                user.stripe_subscription_id = session.get("subscription")
                user.plan = "pro"
                db.commit()
                logger.info(f"User {user.id} upgraded to pro via checkout")
                await _notify_subscription(db, user, "subscribed", "pro")
            else:
                logger.warning(f"Webhook: user_id={user_id} not found in DB")

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Remove pro plan if subscription is cancelled / past due
        customer_id = subscription.get("customer")
        if customer_id:
            user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
            if user:
                user.plan = "free"
                db.commit()
                await _notify_subscription(db, user, "cancelled", "free")

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        
        if customer_id:
            user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
            if user:
                if status in ["active", "trialing"]:
                    user.plan = "pro"
                else: # past_due, canceled, unpaid etc
                    user.plan = "free"
                db.commit()

    return {"status": "success"}
