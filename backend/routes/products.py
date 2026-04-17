from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
import models, schemas, auth
from services.url_safety import validate_safe_url, UnsafeUrlError

router = APIRouter()


def _check_competitor_url(url: str) -> None:
    """Reject URLs that could SSRF the scraper. Raises HTTPException(400)."""
    try:
        validate_safe_url(url)
    except UnsafeUrlError as e:
        raise HTTPException(status_code=400, detail=f"無効なURL: {e}")

@router.get("/products", response_model=List[schemas.Product])
def get_products(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    ログイン中のユーザーが登録した商品一覧を取得するAPI
    """
    products = db.query(models.Product)\
        .options(joinedload(models.Product.competitor_urls))\
        .filter(models.Product.user_id == current_user.id)\
        .order_by(models.Product.created_at.desc()).all()
    return products

@router.get("/products/count", response_model=schemas.ProductCount)
def get_products_count(db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    ログイン中のユーザーが登録している商品数を取得するAPI
    """
    count = db.query(models.Product)\
        .filter(models.Product.user_id == current_user.id).count()
    return {"count": count}

@router.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    特定の商品の詳細情報（競合URLを含む）を取得するAPI
    - **product_id**: 取得したい商品のID
    """
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id  # SaaS: ownership check
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/products", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    """
    新規商品を登録するAPI。現在のプランに基づく上限（商品数および商品あたりの競合URL数）チェックが行われます。
    
    - **product_name**: 商品名
    - **own_price**: 自社価格
    - **category**: (オプション) カテゴリ
    - **competitor_urls**: (オプション) 競合URL情報のリスト (name, url)
    """
    # SaaS: enforce plan limits
    plan_config = models.PLAN_LIMITS.get(current_user.plan, models.PLAN_LIMITS["free"])
    max_products = plan_config["max_products"]
    current_count = db.query(models.Product)\
        .filter(models.Product.user_id == current_user.id).count()
    if max_products is not None and current_count >= max_products:
        raise HTTPException(
            status_code=403,
            detail=f"商品数の上限に達しました（{current_user.plan}プラン: {max_products}件）。プランをアップグレードしてください。"
        )
    
    # Check competitor URL limit
    max_comps = plan_config["max_competitors_per_product"]
    if max_comps is not None and product.competitor_urls and len(product.competitor_urls) > max_comps:
        raise HTTPException(
            status_code=403,
            detail=f"競合URL数の上限を超えています（{current_user.plan}プラン: 1商品あたり{max_comps}件）。プランをアップグレードしてください。"
        )

    db_product = models.Product(
        user_id=current_user.id,  # SaaS: bind to current user
        product_name=product.product_name,
        own_price=product.own_price,
        category=product.category,
        is_active=product.is_active
    )
    db.add(db_product)
    db.flush()  # To get db_product.id
    
    for comp in product.competitor_urls:
        _check_competitor_url(comp.url)
        db_comp = models.CompetitorUrl(
            product_id=db_product.id,
            competitor_name=comp.competitor_name,
            url=comp.url
        )
        db.add(db_comp)
        
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product_update: schemas.ProductUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id  # SaaS: ownership check
    ).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id  # SaaS: ownership check
    ).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    db.delete(db_product)
    db.commit()
    return {"detail": "Product deleted"}

@router.post("/products/{product_id}/competitors", response_model=schemas.CompetitorUrl)
def add_competitor(product_id: int, comp: schemas.CompetitorUrlCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.user_id == current_user.id  # SaaS: ownership check
    ).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check competitor URL limit per product
    plan_config = models.PLAN_LIMITS.get(current_user.plan, models.PLAN_LIMITS["free"])
    max_comps = plan_config["max_competitors_per_product"]
    current_comp_count = len(db_product.competitor_urls)
    if max_comps is not None and current_comp_count >= max_comps:
        raise HTTPException(
            status_code=403,
            detail=f"競合URL数の上限に達しました（{current_user.plan}プラン: 1商品あたり{max_comps}件）。プランをアップグレードしてください。"
        )
        
    _check_competitor_url(comp.url)

    db_comp = models.CompetitorUrl(
        product_id=product_id,
        competitor_name=comp.competitor_name,
        url=comp.url
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp
