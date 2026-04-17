import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from database import SessionLocal, engine
import models, auth


def _resolve_admin_password() -> Optional[str]:
    """Return a password for a first-time admin creation, or None to skip.

    Prefer SEED_ADMIN_PASSWORD from the environment. If it isn't set we
    refuse to fall back to a hardcoded credential in any production-ish
    environment — instead we return None so the caller can skip creating
    the admin user (the deploy should not fail over optional seed data).
    In local dev we generate a random password and print it so seed
    remains convenient.
    """
    pw = os.environ.get("SEED_ADMIN_PASSWORD")
    if pw:
        return pw
    prod_markers = ("DATABASE_URL", "RENDER", "RENDER_SERVICE_ID")
    if any(os.environ.get(k) for k in prod_markers) or os.environ.get("PRICERADAR_ENV") == "production":
        return None
    generated = secrets.token_urlsafe(18)
    print(f"[seed] SEED_ADMIN_PASSWORD not set — generated temporary dev password: {generated}")
    return generated


def seed():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Create admin user
    admin = db.query(models.User).filter(models.User.username == "admin").first()
    if not admin:
        admin_pw = _resolve_admin_password()
        if admin_pw is None:
            print(
                "[seed] Skipping admin user creation: SEED_ADMIN_PASSWORD is not set in a "
                "production-like environment. Set the env var and re-run seed to provision admin."
            )
        else:
            hashed_password = auth.get_password_hash(admin_pw)
            admin = models.User(
                username="admin",
                email="admin@priceradar.space",
                hashed_password=hashed_password,
                plan="enterprise",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("Created admin user (enterprise plan)")

    # 2. Create sample products (bound to admin user)
    products_data = [
        {
            "name": "Nintendo Switch 有機ELモデル",
            "price": 37980,
            "category": "ゲーム機",
            "comps": [
                {"name": "Amazon", "url": "https://www.amazon.co.jp/dp/B0CHR8YHTD", "prices": [37500, 36800, 37000]},
                {"name": "楽天市場", "url": "https://item.rakuten.co.jp/nintendo-switch", "prices": [38000, 37980, 37800]}
            ]
        },
        {
            "name": "Apple AirPods Pro 第2世代",
            "price": 39800,
            "category": "オーディオ",
            "comps": [
                {"name": "Amazon", "url": "https://www.amazon.co.jp/dp/B0BDGW6RNC", "prices": [39000, 38500, 38800]},
                {"name": "Yahoo", "url": "https://shopping.yahoo.co.jp/airpods", "prices": [40000, 39500, 39800]}
            ]
        },
        {
            "name": "Sony WH-1000XM5",
            "price": 44000,
            "category": "オーディオ",
            "comps": [
                {"name": "Amazon", "url": "https://www.amazon.co.jp/dp/B09Y2PVV8B", "prices": [44500, 43800, 44000]},
                {"name": "ビックカメラ", "url": "https://www.biccamera.com/bc/item/10000000000/", "prices": [45000, 44800, 44000]}
            ]
        },
        {
            "name": "ワイヤレスマウス",
            "price": 2980,
            "category": "PC周辺機器",
            "comps": [
                {"name": "Amazon", "url": "https://www.amazon.co.jp/dp/B000000000", "prices": [2500, 2400, 2480]}
            ]
        },
        {
            "name": "テスト用モニター",
            "price": 30000,
            "category": "PC周辺機器",
            "comps": [
                {"name": "Amazon", "url": "https://www.amazon.co.jp/dp/B000000001", "prices": [29800, 29000, 29500]},
                {"name": "楽天", "url": "https://item.rakuten.co.jp/monitor", "prices": [31000, 30500, 30000]}
            ]
        }
    ]

    if admin is None:
        print("[seed] No admin user — skipping sample product population")
        db.commit()
        db.close()
        print("Seeding complete.")
        return

    for pdata in products_data:
        if not db.query(models.Product).filter(
            models.Product.product_name == pdata["name"],
            models.Product.user_id == admin.id
        ).first():
            product = models.Product(
                user_id=admin.id,  # SaaS: bind to admin user
                product_name=pdata["name"],
                own_price=pdata["price"],
                category=pdata["category"]
            )
            db.add(product)
            db.flush()  # Get ID
            
            for comp_data in pdata["comps"]:
                comp = models.CompetitorUrl(
                    product_id=product.id,
                    competitor_name=comp_data["name"],
                    url=comp_data["url"]
                )
                db.add(comp)
                db.flush()
                
                # Add price history
                for i, price in enumerate(comp_data["prices"]):
                    history = models.PriceHistory(
                        competitor_url_id=comp.id,
                        price=price,
                        stock_status="在庫あり",
                        scraped_at=datetime.now(timezone.utc) - timedelta(days=2-i)
                    )
                    db.add(history)
            
            print(f"Created product: {pdata['name']}")
            
    db.commit()
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed()
