import logging
import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from .core import get_scraper

logger = logging.getLogger("priceradar.scraper")

async def scrape_competitor_url(db: Session, comp_url: models.CompetitorUrl):
    scraper = get_scraper(comp_url.url)
    price, stock = await scraper.scrape(comp_url.url)

    if price is not None:
        new_history = models.PriceHistory(
            competitor_url_id=comp_url.id,
            price=price,
            stock_status=stock,
            scraped_at=datetime.now(timezone.utc)
        )
        db.add(new_history)
        db.commit()
        logger.info(f"Successfully scraped {comp_url.url}: ¥{price} ({stock})")

        # Trigger LINE notifications (price loss / recovery / stock out)
        try:
            from services.notifications import check_and_notify_price_event
            await check_and_notify_price_event(db, comp_url, price, stock)
        except Exception as e:
            logger.error(f"Notification check failed for {comp_url.url}: {e}")

        return True
    else:
        logger.warning(f"Failed to extract price from {comp_url.url}")
        return False

async def run_scheduled_scraping():
    db = SessionLocal()
    try:
        # Get all active competitor URLs
        comp_urls = db.query(models.CompetitorUrl).join(models.Product).filter(models.Product.is_active == True).all()
        logger.info(f"Starting scheduled scraping job for {len(comp_urls)} URLs")
        
        # In a real SaaS, we'd distribute these or batch them
        # For this PoC, we run concurrently but with a limit
        concurrency = 2
        semaphore = asyncio.Semaphore(concurrency)
        
        async def scrape_with_sema(url_obj):
            async with semaphore:
                await scrape_competitor_url(db, url_obj)
        
        tasks = [scrape_with_sema(c) for c in comp_urls]
        if tasks:
            await asyncio.gather(*tasks)
            
        logger.info("Scheduled scraping job completed")
    finally:
        db.close()


async def cleanup_old_history():
    """Free プランユーザーの古い価格履歴を削除する"""
    db = SessionLocal()
    try:
        free_users = db.query(models.User).filter(models.User.plan == "free").all()
        if not free_users:
            return

        retention = models.PLAN_LIMITS["free"]["history_retention_days"]
        if retention is None:
            return

        cutoff = datetime.now(timezone.utc) - timedelta(days=retention)
        free_user_ids = [u.id for u in free_users]

        deleted = db.query(models.PriceHistory)\
            .filter(
                models.PriceHistory.scraped_at < cutoff,
                models.PriceHistory.competitor_url_id.in_(
                    db.query(models.CompetitorUrl.id).join(models.Product).filter(
                        models.Product.user_id.in_(free_user_ids)
                    )
                )
            ).delete(synchronize_session=False)

        db.commit()
        if deleted:
            logger.info(f"Cleaned up {deleted} old price history records for Free plan users")
    except Exception as e:
        logger.error(f"History cleanup failed: {e}")
        db.rollback()
    finally:
        db.close()
