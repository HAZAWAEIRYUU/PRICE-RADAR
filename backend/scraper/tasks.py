import logging
import asyncio
from datetime import datetime, timezone
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
