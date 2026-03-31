import os
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
import stripe
from database import get_db
import models
import auth

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID_PRO = os.environ.get("STRIPE_PRICE_ID_PRO", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://price-radar.pages.dev")

@router.post("/create-checkout-session")
def create_checkout_session(current_user: models.User = Depends(auth.get_current_user), db: Session = Depends(get_db)):
    if not stripe.api_key or not STRIPE_PRICE_ID_PRO:
        raise HTTPException(status_code=500, detail="Stripe configuration is missing")
        
    try:
        # If user already has a customer ID, use it. Otherwise, let Stripe create one and we'll save it later.
        customer_id = current_user.stripe_customer_id
        
        session_params = {
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price": STRIPE_PRICE_ID_PRO,
                    "quantity": 1,
                },
            ],
            "mode": "subscription",
            "success_url": f"{FRONTEND_URL}/pricing/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{FRONTEND_URL}/pricing/cancel",
            "client_reference_id": str(current_user.id),
        }
        
        if customer_id:
            session_params["customer"] = customer_id
        else:
            session_params["customer_email"] = current_user.email

        checkout_session = stripe.checkout.Session.create(**session_params)
        return {"url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-portal-session")
def create_portal_session(current_user: models.User = Depends(auth.get_current_user)):
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe configuration is missing")
        
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    try:
        portalSession = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{FRONTEND_URL}/pricing",
        )
        return {"url": portalSession.url}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
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

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # Remove pro plan if subscription is cancelled / past due
        customer_id = subscription.get("customer")
        if customer_id:
            user = db.query(models.User).filter(models.User.stripe_customer_id == customer_id).first()
            if user:
                user.plan = "free"
                db.commit()
                
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
