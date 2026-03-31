from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth

router = APIRouter()

def get_current_user_dep(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/plan", response_model=schemas.PlanInfo)
def get_plan_info(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_dep)):
    plan_key = current_user.plan or "free"
    plan_config = models.PLAN_LIMITS.get(plan_key, models.PLAN_LIMITS["free"])
    
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

@router.post("/plan/upgrade")
def upgrade_plan(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_dep)):
    raise HTTPException(status_code=400, detail="This endpoint is deprecated. Please use /api/stripe/create-checkout-session for updates.")

