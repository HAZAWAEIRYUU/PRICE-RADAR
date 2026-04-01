from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from database import get_db
import models, schemas, auth

router = APIRouter()

def get_current_user_dep(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

@router.get("/prices/alerts", response_model=List[schemas.PriceAlertItem])
def get_price_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_dep)):
    """
    ログイン中のユーザーが登録している商品のうち、競合価格が自社価格より安いもの（アラート対象）のリストを取得するAPI
    """
    # SaaS: only fetch products owned by the current user
    products = db.query(models.Product).filter(
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
def get_price_history(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_dep)):
    """
    特定の商品の競合価格推移（履歴）を取得するAPI
    - **product_id**: 価格履歴を取得したい商品のID
    """
    # SaaS: verify ownership before returning price history
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id
    ).first()
    if not product:
        return []
        
    url_ids = [url.id for url in product.competitor_urls]
    if not url_ids:
        return []
        
    history = db.query(models.PriceHistory)\
        .filter(models.PriceHistory.competitor_url_id.in_(url_ids))\
        .order_by(models.PriceHistory.scraped_at.asc()).all()
        
    return history

from fastapi import HTTPException
from scraper.tasks import scrape_competitor_url

@router.post("/prices/scrape/{url_id}")
async def force_scrape_url(url_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_dep)):
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
