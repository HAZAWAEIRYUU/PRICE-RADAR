from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter()

@router.get("/prices/alerts", response_model=List[schemas.PriceAlertItem])
def get_price_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    ログイン中のユーザーが登録している商品のうち、競合価格が自社価格より安いもの（アラート対象）のリストを取得するAPI
    """
    products = db.query(models.Product)\
        .options(joinedload(models.Product.competitor_urls))\
        .filter(
            models.Product.is_active == True,
            models.Product.user_id == current_user.id
        ).all()
    alerts = []
    
    for product in products:
        lowest_comp_name = None
        lowest_comp_price = None
        lowest_stock = None
        
        for url in product.competitor_urls:
            # Get latest price history
            latest_history = db.query(models.PriceHistory)\
                .filter(models.PriceHistory.competitor_url_id == url.id)\
                .order_by(models.PriceHistory.scraped_at.desc()).first()
                
            if latest_history:
                price = float(latest_history.price)
                if lowest_comp_price is None or price < lowest_comp_price:
                    lowest_comp_price = price
                    lowest_comp_name = url.competitor_name
                    lowest_stock = latest_history.stock_status
                    
        if lowest_comp_price is not None and float(product.own_price) > lowest_comp_price:
            alerts.append({
                "product_id": product.id,
                "product_name": product.product_name,
                "own_price": str(product.own_price),
                "competitor_name": lowest_comp_name,
                "competitor_price": str(lowest_comp_price),
                "price_diff": str(float(product.own_price) - lowest_comp_price),
                "stock_status": lowest_stock
            })
            
    return alerts

@router.get("/prices/{product_id}/history", response_model=List[schemas.PriceHistoryRecord])
def get_price_history(
    product_id: int,
    limit: int = 500,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    特定の商品の競合価格推移（履歴）を取得するAPI
    - **product_id**: 価格履歴を取得したい商品のID
    - **limit**: 最大取得件数（デフォルト500）
    - **offset**: オフセット（デフォルト0）
    """
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not product:
        return []

    url_ids = [url.id for url in product.competitor_urls]
    if not url_ids:
        return []

    # Enforce plan history retention
    plan_config = models.PLAN_LIMITS.get(current_user.plan, models.PLAN_LIMITS["free"])
    retention_days = plan_config.get("history_retention_days")

    query = db.query(models.PriceHistory)\
        .filter(models.PriceHistory.competitor_url_id.in_(url_ids))

    if retention_days is not None:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        query = query.filter(models.PriceHistory.scraped_at >= cutoff)

    history = query.order_by(models.PriceHistory.scraped_at.asc())\
        .offset(offset).limit(min(limit, 1000)).all()

    return history

from fastapi import HTTPException, Request
from scraper.tasks import scrape_competitor_url
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/prices/scrape/{url_id}")
@limiter.limit("10/minute")
async def force_scrape_url(request: Request, url_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    指定した競合URLの価格を即座にスクレイピングする手動トリガーAPI
    - **url_id**: スクレイピングを実行したい競合URLのID
    """
    comp_url = db.query(models.CompetitorUrl).join(models.Product).filter(
        models.CompetitorUrl.id == url_id,
        models.Product.user_id == current_user.id
    ).first()
    
    if not comp_url:
        raise HTTPException(status_code=404, detail="Competitor URL not found or access denied")
        
    success = await scrape_competitor_url(db, comp_url)
    if success:
        return {"message": "Scraping successful"}
    else:
        raise HTTPException(status_code=400, detail="Failed to scrape price from URL")
