import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

logger = logging.getLogger("priceradar.plan")

router = APIRouter()


@router.get("/plan", response_model=schemas.PlanInfo)
def get_plan_info(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    raw_plan = current_user.plan or "free"
    if raw_plan not in models.PLAN_LIMITS:
        # Data corruption marker — surface it in logs but don't break the API.
        logger.error(
            "User %s has unknown plan=%r — falling back to 'free'",
            current_user.id, raw_plan,
        )
        plan_key = "free"
    else:
        plan_key = raw_plan
    plan_config = models.PLAN_LIMITS[plan_key]

    current_products = db.query(models.Product)\
        .filter(models.Product.user_id == current_user.id).count()

    return {
        "plan": plan_key,
        "label": plan_config["label"],
        "price": plan_config["price"],
        "usage": {
            "current_products": current_products,
            "max_products": plan_config["max_products"],
            "max_competitors_per_product": plan_config["max_competitors_per_product"],
            "history_retention_days": plan_config["history_retention_days"],
        }
    }


